"""
Unit tests for FeedbackService integration with LLMService
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.feedback_service import FeedbackService
from app.services.llm_service import LLMService

class TestFeedbackServiceAsync:
    """Test async feedback generation in FeedbackService"""
    
    @pytest.mark.asyncio
    async def test_generate_feedback_calls_llm_service(self):
        """Test that generate_feedback calls LLMService"""
        db = MagicMock()
        question = MagicMock()
        question.question_text = "Test question"
        question.explanation = "Test explanation"
        question.topic.name = "Test Topic"
        
        with patch.object(LLMService, 'generate_feedback', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                'is_correct': True,
                'explanation': 'Great job!',
                'effort_level': 'easy'
            }
            
            feedback = await FeedbackService.generate_feedback(
                db=db,
                question=question,
                user_answer="correct",
                is_correct=True
            )
            
            mock_llm.assert_called_once()
            assert feedback['is_correct'] is True
    
    def test_store_answer_with_confidence(self, db_session, sample_user, sample_questions):
        """Test storing answer with confidence level"""
        answer = FeedbackService.store_answer(
            db=db_session,
            user_id=sample_user.id,
            question_id=sample_questions[0].id,
            user_answer="1",
            is_correct=True,
            time_spent=30,
            confidence_level=0.85
        )
        
        assert answer.user_id == sample_user.id
        assert answer.confidence_level == 0.85
        assert answer.is_correct is True
        assert answer.time_spent == 30
    
    def test_calculate_average_time_per_topic(self, db_session, sample_user, sample_user_answers):
        """Test calculating average time spent per topic"""
        avg_times = FeedbackService.calculate_average_time(
            db=db_session,
            user_id=sample_user.id
        )
        
        assert isinstance(avg_times, dict)
        for topic_id, avg_time in avg_times.items():
            assert isinstance(topic_id, int)
            assert isinstance(avg_time, (int, float))
            assert avg_time >= 0
    
    def test_get_confidence_distribution(self, db_session, sample_user, sample_user_answers):
        """Test getting confidence distribution across answers"""
        distribution = FeedbackService.get_confidence_distribution(
            db=db_session,
            user_id=sample_user.id
        )
        
        assert 'low' in distribution  # 0.0-0.33
        assert 'medium' in distribution  # 0.34-0.66
        assert 'high' in distribution  # 0.67-1.0
        
        total = sum(distribution.values())
        assert total > 0

class TestFeedbackQualitySampling:
    """Test sampling feedback for quality assurance"""
    
    def test_feedback_includes_explanation(self):
        """Test that feedback includes clear explanations"""
        # All feedback should have 'explanation' field
        pass
    
    def test_feedback_has_consistent_format(self):
        """Test that feedback follows consistent format"""
        # Should always include: is_correct, explanation, effort_level
        pass
    
    def test_effort_level_matches_answer_correctness(self):
        """Test that effort_level reflects how difficult the question was"""
        # Correct answers should be marked 'easy' or 'medium'
        # Incorrect answers should be marked 'medium' or 'hard'
        pass

class TestConfidenceScoringIntegration:
    """Test confidence scoring integration"""
    
    def test_confidence_scores_tracked_across_topic(self, db_session, sample_user):
        """Test that confidence is tracked per topic"""
        # Users' confidence should reflect their actual accuracy
        pass
    
    def test_confidence_level_influences_question_difficulty(self):
        """Test that low confidence triggers easier questions"""
        # When user has low confidence, next question should be easier
        pass
    
    def test_confidence_tracking_identifies_overconfidence(self):
        """Test detection of overconfident learners"""
        # When confidence > accuracy, identify overconfidence
        pass
