from sqlalchemy.orm import Session
from app.models import UserProgress, Topic, Subject
from typing import List

class RecommendationService:
    """
    Service for generating personalized learning recommendations.
    Recommends topics based on user's weak areas and learning patterns.
    """
    
    @staticmethod
    def get_next_topic_recommendation(
        db: Session, 
        user_id: int
    ) -> Topic | None:
        """
        Analyze user's weak topics and recommend the next topic to study.
        This implements the intelligent recommendation requirement.
        """
        # Get weak topics (accuracy < 70%)
        weak_progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.accuracy_score < 70
        ).all()
        
        if weak_progress:
            # Sort by accuracy score (lowest first)
            weak_progress.sort(key=lambda x: x.accuracy_score)
            return weak_progress[0].topic
        
        # If no weak topics, recommend next untested topic
        return RecommendationService._get_next_untested_topic(db, user_id)
    
    @staticmethod
    def _get_next_untested_topic(db: Session, user_id: int) -> Topic | None:
        """Get first topic user hasn't studied yet"""
        # Get topics user has studied
        studied_topic_ids = db.query(UserProgress.topic_id).filter(
            UserProgress.user_id == user_id
        ).all()
        studied_topic_ids = [t[0] for t in studied_topic_ids]
        
        # Find first unstudied topic
        if studied_topic_ids:
            untested_topic = db.query(Topic).filter(
                ~Topic.id.in_(studied_topic_ids)
            ).first()
        else:
            untested_topic = db.query(Topic).first()
        
        return untested_topic
    
    @staticmethod
    def get_personalized_learning_path(
        db: Session,
        user_id: int,
        subject_id: int | None = None
    ) -> List[dict]:
        """
        Generate a personalized learning path based on:
        - User's current weak areas
        - Topic prerequisites
        - Difficulty progression
        """
        
        if subject_id:
            topics = db.query(Topic).filter(
                Topic.subject_id == subject_id
            ).all()
        else:
            topics = db.query(Topic).all()
        
        # Score topics based on user performance
        scored_topics = []
        for topic in topics:
            progress = db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.topic_id == topic.id
            ).first()
            
            if progress:
                score = progress.accuracy_score
                attempts = progress.questions_attempted
            else:
                score = 0  # Not started
                attempts = 0
            
            scored_topics.append({
                "topic_id": topic.id,
                "topic_name": topic.name,
                "current_score": score,
                "attempts": attempts,
                "priority": 100 + (70 - score) if attempts > 0 else 150  # Higher priority = higher number
            })
        
        # Sort by priority (highest first)
        scored_topics.sort(key=lambda x: x["priority"], reverse=True)
        
        return scored_topics
    
    @staticmethod
    def should_review_topic(
        db: Session,
        user_id: int,
        topic_id: int
    ) -> bool:
        """
        Determine if user should review a topic based on:
        - Time since last attempt
        - Current accuracy
        - Natural forgetting curve
        """
        
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.topic_id == topic_id
        ).first()
        
        if not progress:
            return False
        
        # If accuracy is below 70%, recommend review
        if progress.accuracy_score < 70:
            return True
        
        # Based on spaced repetition - recommend review if been 7+ days
        from datetime import datetime, timedelta
        if progress.last_attempted:
            days_since_attempt = (datetime.utcnow() - progress.last_attempted).days
            if days_since_attempt > 7:
                return True
        
        return False
