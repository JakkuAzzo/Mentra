from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import User, Question, UserAnswer, Topic, UserProgress
from app.schemas.schemas import UserAnswerCreate, UserAnswerResponse
from datetime import datetime

class QuestionService:
    @staticmethod
    def get_question_by_id(db: Session, question_id: int):
        """Get question by ID with options"""
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise ValueError("Question not found")
        return question
    
    @staticmethod
    def get_questions_by_topic(db: Session, topic_id: int, limit: int = 10):
        """Get questions for a specific topic"""
        questions = db.query(Question).filter(
            Question.topic_id == topic_id
        ).limit(limit).all()
        return questions
    
    @staticmethod
    def get_adaptive_question(db: Session, user_id: int, topic_id: int):
        """
        Get next adaptive question based on user performance.
        Prioritizes topics with lower accuracy scores.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get topic
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise ValueError("Topic not found")
        
        # Get user's recent answers on this topic
        recent_answers = db.query(UserAnswer).join(
            Question
        ).filter(
            UserAnswer.user_id == user_id,
            Question.topic_id == topic_id
        ).order_by(desc(UserAnswer.created_at)).limit(5).all()
        
        # Adjust difficulty based on performance
        if recent_answers:
            recent_accuracy = sum(1 for a in recent_answers if a.is_correct) / len(recent_answers)
            if recent_accuracy > 0.8:
                difficulty = min(5, topic.difficulty_level + 1)
            elif recent_accuracy < 0.5:
                difficulty = max(1, topic.difficulty_level - 1)
            else:
                difficulty = topic.difficulty_level
        else:
            difficulty = topic.difficulty_level
        
        # Get unused or rarely attempted questions at adjusted difficulty
        question = db.query(Question).filter(
            Question.topic_id == topic_id,
            Question.difficulty == difficulty
        ).first()
        
        if not question:
            # Fallback to any question if specific difficulty not found
            question = db.query(Question).filter(
                Question.topic_id == topic_id
            ).first()
        
        return question

class ProgressService:
    @staticmethod
    def update_user_progress(
        db: Session, 
        user_id: int, 
        topic_id: int, 
        is_correct: bool
    ):
        """Update user's progress on a topic"""
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.topic_id == topic_id
        ).first()
        
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                topic_id=topic_id,
                questions_attempted=0,
                questions_correct=0,
                accuracy_score=0.0
            )
            db.add(progress)
        
        progress.questions_attempted += 1
        if is_correct:
            progress.questions_correct += 1
        
        progress.accuracy_score = (progress.questions_correct / progress.questions_attempted) * 100
        progress.last_attempted = datetime.utcnow()
        
        db.commit()
        return progress
    
    @staticmethod
    def get_user_progress(db: Session, user_id: int):
        """Get user's progress across all topics"""
        progress_records = db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).all()
        return progress_records
    
    @staticmethod
    def get_weak_topics(db: Session, user_id: int, threshold: float = 70.0) -> list:
        """Get topics where user performance is below threshold"""
        weak_topics = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.accuracy_score < threshold,
            UserProgress.questions_attempted > 0
        ).all()
        return weak_topics
    
    @staticmethod
    def get_user_summary(db: Session, user_id: int) -> dict:
        """Get user's overall learning summary"""
        progress_records = db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).all()
        
        if not progress_records:
            return {
                "total_questions_attempted": 0,
                "total_accuracy": 0.0,
                "topics_studied": 0,
                "weak_topics": [],
                "strong_topics": []
            }
        
        total_attempted = sum(p.questions_attempted for p in progress_records)
        total_correct = sum(p.questions_correct for p in progress_records)
        overall_accuracy = (total_correct / total_attempted * 100) if total_attempted > 0 else 0
        
        weak_topics = [p.topic.name for p in progress_records if p.accuracy_score < 70]
        strong_topics = [p.topic.name for p in progress_records if p.accuracy_score >= 85]
        
        return {
            "total_questions_attempted": total_attempted,
            "total_accuracy": round(overall_accuracy, 2),
            "topics_studied": len(progress_records),
            "weak_topics": weak_topics,
            "strong_topics": strong_topics
        }
