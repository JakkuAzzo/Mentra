"""
Advanced spaced repetition algorithm for optimal review scheduling.
Based on research from Ebbinghaus forgetting curve and SM-2 algorithm.
"""

# pyright: reportGeneralTypeIssues=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportAssignmentType=false, reportCallIssue=false, reportReturnType=false

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import UserProgress, UserAnswer, Question
import math

class SpacedRepetitionService:
    """
    Implements spaced repetition for optimized learning intervals.
    Reviews are scheduled when user is most likely to forget.
    """
    
    # Optimal review intervals (in days)
    INTERVALS = [1, 3, 7, 14, 30, 60, 120]
    
    @staticmethod
    def calculate_next_review_date(
        current_accuracy: float,
        question_difficulty: int,
        last_attempt: datetime = None
    ) -> datetime:
        """
        Calculate when user should review this topic based on:
        - Current accuracy (higher = longer interval)
        - Question difficulty (harder = longer interval)
        - Time since last attempt
        """
        
        if last_attempt is None:
            # First attempt - review in 1 day
            return datetime.utcnow() + timedelta(days=1)
        
        days_since = (datetime.utcnow() - last_attempt).days
        
        # Base interval calculation
        if current_accuracy >= 90:
            base_interval = 60  # Review in 2 months
        elif current_accuracy >= 80:
            base_interval = 30  # Review in 1 month
        elif current_accuracy >= 70:
            base_interval = 14  # Review in 2 weeks
        elif current_accuracy >= 60:
            base_interval = 7   # Review in 1 week
        elif current_accuracy >= 50:
            base_interval = 3   # Review in 3 days
        else:
            base_interval = 1   # Review tomorrow
        
        # Adjust for difficulty
        difficulty_factor = 1 + (question_difficulty - 1) * 0.2
        adjusted_interval = base_interval * difficulty_factor
        
        return last_attempt + timedelta(days=adjusted_interval)
    
    @staticmethod
    def get_topics_due_for_review(
        db: Session,
        user_id: int,
        include_weak: bool = True
    ) -> list:
        """
        Get topics that are due for review based on:
        - Spaced repetition intervals
        - Performance (weak topics prioritized)
        - Time since last review
        
        Returns: List of Topic objects sorted by review urgency
        """
        
        progress_records = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.questions_attempted > 0
        ).all()
        
        due_topics = []
        now = datetime.utcnow()
        
        for progress in progress_records:
            # Check if topic is due for review
            next_review = SpacedRepetitionService.calculate_next_review_date(
                progress.accuracy_score,
                progress.topic.difficulty_level,
                progress.last_attempted
            )
            
            if progress.last_attempted is None or now >= next_review:
                # Topic is due for review
                priority = SpacedRepetitionService._calculate_review_priority(
                    progress.accuracy_score,
                    progress.topic.difficulty_level,
                    progress.last_attempted
                )
                
                # Return topic object with priority for sorting
                due_topics.append((progress.topic, priority))
        
        # Sort by priority (highest first) and extract topics
        due_topics.sort(key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in due_topics]
    
    @staticmethod
    def _calculate_review_priority(
        accuracy: float,
        difficulty: int,
        last_attempted: datetime = None
    ) -> float:
        """Calculate priority score for review (higher = more urgent)"""
        
        # Weak topics get higher priority (inverse of accuracy)
        accuracy_factor = (100 - accuracy) / 100
        
        # Harder topics get higher priority
        difficulty_factor = difficulty / 5
        
        # Longer since review = higher priority
        if last_attempted:
            days_since = (datetime.utcnow() - last_attempted).days
            time_factor = min(days_since / 30, 1.0)  # Cap at 1.0
        else:
            time_factor = 1.0  # Never reviewed
        
        # Weighted combination
        priority = (
            accuracy_factor * 0.5 +
            difficulty_factor * 0.3 +
            time_factor * 0.2
        )
        
        return priority
    
    @staticmethod
    def _calculate_priority_score(
        accuracy: float,
        days_overdue: int,
        difficulty: float = 1.0
    ) -> float:
        """
        Calculate priority score for a topic review (0.0-1.0).
        Higher score = more urgent review needed.
        
        Factors:
        - Accuracy: lower accuracy = higher urgency (weight 50%)
        - Days overdue: more days overdue = higher urgency (weight 30%)
        - Difficulty: harder topics = higher urgency (weight 20%)
        """
        # Accept either 0-1 or 0-100 accuracy inputs.
        normalized_accuracy = accuracy * 100 if accuracy <= 1 else accuracy

        # Inverse accuracy (0-100 to 0-1)
        accuracy_factor = (100 - normalized_accuracy) / 100
        
        # Days overdue factor (normalized to 0-1, capped at 30 days)
        days_factor = min(days_overdue / 30, 1.0)
        
        # Difficulty factor (1-5 normalized to 0-1)
        difficulty_factor = min(difficulty / 5.0, 1.0)
        
        # Weighted combination
        priority_score = (
            accuracy_factor * 0.5 +
            days_factor * 0.3 +
            difficulty_factor * 0.2
        )
        
        return round(priority_score, 3)
    
    @staticmethod
    def estimate_mastery_date(
        db: Session,
        user_id: int,
        topic_id: int
    ) -> dict:
        """
        Estimate when user will master (>85% accuracy) a topic
        based on current progress and learning rate.
        """
        
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.topic_id == topic_id
        ).first()
        
        if not progress or progress.questions_attempted < 3:
            return {
                "estimated_days": 14,
                "days_remaining": 14,
                "mastery_date": datetime.utcnow() + timedelta(days=14),
                "confidence": "low",
                "next_milestone_accuracy": 70,
                "questions_to_master": 20
            }
        
        # Calculate learning rate
        recent_answers = db.query(UserAnswer).join(
            Question
        ).filter(
            UserAnswer.user_id == user_id,
            Question.topic_id == topic_id
        ).order_by(UserAnswer.created_at.desc()).limit(10).all()
        
        if len(recent_answers) < 2:
            return {
                "estimated_days": 14,
                "days_remaining": 14,
                "mastery_date": datetime.utcnow() + timedelta(days=14),
                "confidence": "low",
                "next_milestone_accuracy": 70,
                "questions_to_master": 20
            }
        
        # Calculate trend
        recent_correct = sum(1 for a in recent_answers if a.is_correct is True)
        improvement_rate = (recent_correct / len(recent_answers)) - (progress.accuracy_score / 100)
        
        current_accuracy = progress.accuracy_score
        target_accuracy = 85
        gap = target_accuracy - current_accuracy
        
        if improvement_rate > 0:
            # Positive trend
            days_to_mastery = max(1, int(gap / (improvement_rate * 5)))
            confidence = "high" if improvement_rate > 5 else "medium"
        else:
            # Needs more practice
            days_to_mastery = 21
            confidence = "low"
        
        # Questions needed
        questions_per_day = len(recent_answers) / max(1, (datetime.utcnow() - recent_answers[-1].created_at).days or 1)
        questions_to_master = max(3, int(gap * 2))
        
        mastery_date = datetime.utcnow() + timedelta(days=days_to_mastery)
        
        return {
            "estimated_days": days_to_mastery,
            "days_remaining": days_to_mastery,
            "mastery_date": mastery_date,
            "confidence": confidence,
            "current_accuracy": current_accuracy,
            "next_milestone_accuracy": min(target_accuracy, current_accuracy + 10),
            "questions_to_master": questions_to_master,
            "improvement_rate_per_day": round(improvement_rate, 2)
        }


class SessionAnalyticsService:
    """
    Tracks and analyzes user learning sessions for insights
    about engagement and learning patterns.
    """
    
    @staticmethod
    def calculate_session_stats(
        db: Session,
        user_id: int,
        days_back: int = 7
    ) -> dict:
        """Calculate statistics for user's recent sessions"""
        
        from app.models import UserSession
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.started_at >= cutoff_date
        ).all()
        
        if not sessions:
            return {
                "total_sessions": 0,
                "total_hours": 0,
                "avg_session_length": 0,
                "most_active_hour": None,
                "streak_days": 0
            }
        
        # Calculate metrics
        total_minutes = sum(s.duration_minutes or 0 for s in sessions)
        total_hours = total_minutes / 60
        
        avg_duration = total_minutes / len(sessions) if sessions else 0
        
        # Calculate streak
        streak = SessionAnalyticsService._calculate_streak(
            db, user_id, datetime.utcnow()
        )
        
        return {
            "total_sessions": len(sessions),
            "total_hours": round(total_hours, 2),
            "avg_session_length_minutes": round(avg_duration, 0),
            "peak_hour": SessionAnalyticsService._get_peak_hour(sessions),
            "streak": streak,
            "consistency_score": SessionAnalyticsService._calculate_consistency(
                db, user_id
            )
        }
    
    @staticmethod
    def _calculate_streak(
        db: Session,
        user_id: int,
        current_date: datetime
    ) -> int:
        """Calculate current learning streak (consecutive days)"""
        
        from app.models import UserSession
        
        streak = 0
        check_date = current_date.date()
        
        while True:
            sessions_that_day = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.started_at >= datetime.combine(check_date, datetime.min.time()),
                UserSession.started_at < datetime.combine(check_date + timedelta(days=1), datetime.min.time())
            ).count()
            
            if sessions_that_day > 0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
            
            if streak > 365:  # Safety limit
                break
        
        return streak
    
    @staticmethod
    def _get_peak_hour(sessions: list) -> int:
        """Get the hour when user is most active"""
        
        hour_counts = {}
        for session in sessions:
            hour = session.started_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if not hour_counts:
            return None
        
        return max(hour_counts, key=hour_counts.get)
    
    @staticmethod
    def _calculate_consistency(db: Session, user_id: int) -> float:
        """
        Calculate consistency score (0-100).
        Based on regularity of learning sessions.
        """
        
        from app.models import UserSession
        
        # Get last 30 days of sessions
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.started_at >= cutoff_date
        ).all()
        
        if len(sessions) < 3:
            return 0.0
        
        # Count days with activity
        active_days = set()
        for session in sessions:
            active_days.add(session.started_at.date())
        
        # Consistency = percentage of days with activity
        consistency = (len(active_days) / 30) * 100
        
        return min(100.0, consistency)
