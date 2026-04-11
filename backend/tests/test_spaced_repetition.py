"""
Tests for SpacedRepetitionService and SessionAnalyticsService.
"""

import pytest
from datetime import datetime, timedelta
from app.services.spaced_repetition_service import (
    SpacedRepetitionService, 
    SessionAnalyticsService
)
from app.models import UserProgress, Topic

class TestSpacedRepetitionService:
    """Test spaced repetition algorithm"""
    
    def test_calculate_next_review_date_high_accuracy(self):
        """Test review date calculation for high accuracy"""
        # High accuracy (90%) should result in longer interval
        next_review = SpacedRepetitionService.calculate_next_review_date(
            current_accuracy=90.0,
            question_difficulty=1,
            last_attempt=datetime.utcnow() - timedelta(days=1)
        )
        
        # Should be about 2 months out
        days_until = (next_review - datetime.utcnow()).days
        assert 50 <= days_until <= 70  # ~60 days with some tolerance
    
    def test_calculate_next_review_date_low_accuracy(self):
        """Test review date calculation for low accuracy"""
        # Low accuracy (40%) should result in shorter interval
        next_review = SpacedRepetitionService.calculate_next_review_date(
            current_accuracy=40.0,
            question_difficulty=1,
            last_attempt=datetime.utcnow()
        )
        
        # Should be about 1 day out
        days_until = (next_review - datetime.utcnow()).days
        assert 0 <= days_until <= 2
    
    def test_calculate_next_review_date_first_attempt(self):
        """Test review date for first attempt (no previous attempt)"""
        next_review = SpacedRepetitionService.calculate_next_review_date(
            current_accuracy=50.0,
            question_difficulty=1,
            last_attempt=None
        )
        
        # First review should be in 1 day
        days_until = (next_review - datetime.utcnow()).days
        assert 0 <= days_until <= 2
    
    def test_calculate_next_review_date_difficulty_adjustment(self):
        """Test that difficulty affects review intervals"""
        # Easy question (difficulty 1)
        easy_review = SpacedRepetitionService.calculate_next_review_date(
            current_accuracy=70.0,
            question_difficulty=1,
            last_attempt=datetime.utcnow()
        )
        
        # Hard question (difficulty 5)
        hard_review = SpacedRepetitionService.calculate_next_review_date(
            current_accuracy=70.0,
            question_difficulty=5,
            last_attempt=datetime.utcnow()
        )
        
        # Hard questions should have longer intervals
        easy_days = (easy_review - datetime.utcnow()).days
        hard_days = (hard_review - datetime.utcnow()).days
        assert hard_days > easy_days
    
    def test_get_topics_due_for_review(self, db_session, sample_user, sample_user_progress):
        """Test getting topics due for review"""
        # Mark one topic as overdue
        sample_user_progress[0].last_attempted = datetime.utcnow() - timedelta(days=30)
        db_session.commit()
        
        due_topics = SpacedRepetitionService.get_topics_due_for_review(
            db_session, 
            sample_user.id
        )
        
        assert len(due_topics) > 0
        assert all(hasattr(topic, 'id') for topic in due_topics)
        assert all(hasattr(topic, 'name') for topic in due_topics)
    
    def test_estimate_mastery_date_insufficient_data(self, db_session, sample_user):
        """Test mastery estimation with insufficient answer data"""
        mastery = SpacedRepetitionService.estimate_mastery_date(
            db_session,
            sample_user.id,
            99999  # Non-existent topic
        )
        
        assert 'estimated_days' in mastery
        assert 'days_remaining' in mastery
        assert 'mastery_date' in mastery
        assert 'confidence' in mastery
        assert mastery['confidence'] == 'low'
    
    def test_estimate_mastery_date_with_improvement(self, db_session, sample_user, sample_user_answers):
        """Test mastery estimation with positive improvement trend"""
        # Get first answer's topic
        topic_id = sample_user_answers[0].question.topic_id
        
        # Create progress record
        progress = UserProgress(
            user_id=sample_user.id,
            topic_id=topic_id,
            questions_attempted=10,
            questions_correct=8,
            accuracy_score=80.0,
            last_attempted=datetime.utcnow()
        )
        db_session.add(progress)
        db_session.commit()
        
        mastery = SpacedRepetitionService.estimate_mastery_date(
            db_session,
            sample_user.id,
            topic_id
        )
        
        assert 'estimated_days' in mastery
        assert 'mastery_date' in mastery
        assert isinstance(mastery['mastery_date'], datetime)
    
    def test_calculate_priority_score(self):
        """Test priority score calculation for review scheduling"""
        # Low accuracy, many days overdue, high difficulty
        high_priority = SpacedRepetitionService._calculate_priority_score(
            accuracy=30.0,
            days_overdue=20,
            difficulty=5.0
        )
        
        # High accuracy, recently attempted, low difficulty
        low_priority = SpacedRepetitionService._calculate_priority_score(
            accuracy=90.0,
            days_overdue=0,
            difficulty=1.0
        )
        
        assert high_priority > low_priority
        assert 0.0 <= high_priority <= 1.0
        assert 0.0 <= low_priority <= 1.0


class TestSessionAnalyticsService:
    """Test session analytics and engagement tracking"""
    
    def test_calculate_session_stats_with_sessions(self, db_session, sample_user, sample_user_sessions):
        """Test calculating session statistics"""
        stats = SessionAnalyticsService.calculate_session_stats(
            db_session,
            sample_user.id,
            days_back=7
        )
        
        assert 'total_sessions' in stats
        assert 'total_hours' in stats
        assert 'avg_session_length_minutes' in stats
        assert 'peak_hour' in stats
        assert 'streak' in stats
        assert 'consistency_score' in stats
        
        assert stats['total_sessions'] > 0
        assert stats['total_hours'] >= 0
        assert 0 <= stats['consistency_score'] <= 100
    
    def test_calculate_session_stats_no_sessions(self, db_session, sample_user):
        """Test session statistics with no sessions"""
        stats = SessionAnalyticsService.calculate_session_stats(
            db_session,
            sample_user.id,
            days_back=7
        )
        
        assert stats['total_sessions'] == 0
        assert stats['total_hours'] == 0
        assert stats['avg_session_length_minutes'] == 0
    
    def test_calculate_streak_consecutive_days(self, db_session, sample_user):
        """Test streak calculation for consecutive days"""
        from app.models import UserSession
        
        # Create sessions for 5 consecutive days
        for i in range(5):
            session_date = datetime.utcnow() - timedelta(days=i)
            session = UserSession(
                user_id=sample_user.id,
                started_at=session_date,
                ended_at=session_date + timedelta(hours=1),
                duration_minutes=60
            )
            db_session.add(session)
        
        db_session.commit()
        
        streak = SessionAnalyticsService._calculate_streak(
            db_session,
            sample_user.id,
            datetime.utcnow()
        )
        
        assert streak > 0
    
    def test_calculate_consistency_score(self, db_session, sample_user, sample_user_sessions):
        """Test consistency score calculation"""
        consistency = SessionAnalyticsService._calculate_consistency(
            db_session,
            sample_user.id
        )
        
        assert isinstance(consistency, (int, float))
        assert 0 <= consistency <= 100
    
    def test_get_peak_hour(self):
        """Test identification of peak learning hour"""
        from unittest.mock import MagicMock
        
        # Create mock sessions with specific hours
        sessions = []
        for hour in [9, 9, 14, 14, 14, 20]:  # 2 at 9am, 3 at 2pm, 1 at 8pm
            session = MagicMock()
            session.started_at = datetime(2024, 1, 1, hour=hour)
            sessions.append(session)
        
        peak_hour = SessionAnalyticsService._get_peak_hour(sessions)
        
        # Should identify 2pm (14:00) as peak hour
        assert peak_hour == 14


class TestEbbinghausForgettingCurve:
    """Test that implementation aligns with Ebbinghaus forgetting curve"""
    
    def test_intervals_match_sm2_algorithm(self):
        """Test that intervals match SM-2 algorithm values"""
        expected_intervals = [1, 3, 7, 14, 30, 60, 120]
        
        assert SpacedRepetitionService.INTERVALS == expected_intervals
    
    def test_forgetting_curve_predicts_decay(self):
        """Test that accuracy decay is predicted correctly"""
        # Time without review = forgetting
        recent_review = SpacedRepetitionService.calculate_next_review_date(
            current_accuracy=80.0,
            question_difficulty=1,
            last_attempt=datetime.utcnow()
        )
        
        old_review = SpacedRepetitionService.calculate_next_review_date(
            current_accuracy=80.0,
            question_difficulty=1,
            last_attempt=datetime.utcnow() - timedelta(days=10)
        )
        
        # Larger time gaps should trigger earlier reviews
        assert (old_review - datetime.utcnow()).days <= (recent_review - datetime.utcnow()).days
