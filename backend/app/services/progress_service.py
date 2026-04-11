"""
Progress service - provides progress tracking and updates.
Methods are delegated to QuestionService where they're implemented.
"""

from sqlalchemy.orm import Session
from app.services.question_service import QuestionService

class ProgressService:
    """Wrapper service for progress operations"""
    
    @staticmethod
    def update_user_progress(
        db: Session, 
        user_id: int, 
        topic_id: int, 
        is_correct: bool
    ):
        """Update user's progress on a topic"""
        return QuestionService.update_user_progress(db, user_id, topic_id, is_correct)
    
    @staticmethod
    def get_user_progress(db: Session, user_id: int):
        """Get user's progress across all topics"""
        return QuestionService.get_user_progress(db, user_id)
    
    @staticmethod
    def get_weak_topics(db: Session, user_id: int, threshold: float = 70.0) -> list:
        """Get topics where user performance is below threshold"""
        return QuestionService.get_weak_topics(db, user_id, threshold)
    
    @staticmethod
    def get_user_summary(db: Session, user_id: int) -> dict:
        """Get user's overall learning summary"""
        return QuestionService.get_user_summary(db, user_id)
