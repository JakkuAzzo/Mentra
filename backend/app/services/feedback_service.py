# pyright: reportGeneralTypeIssues=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportAssignmentType=false
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import UserAnswer, Question
from app.schemas.schemas import FeedbackResponse
from app.services.llm_service import LLMService
import asyncio

class FeedbackService:
    """
    Service for generating AI-powered feedback on student answers.
    Integrates with local LLM for intelligent, personalized explanations.
    """
    
    @staticmethod
    async def generate_feedback(
        db: Session,
        question: Question,
        user_answer: str,
        is_correct: bool
    ) -> FeedbackResponse:
        """
        Generate step-by-step explanation and feedback for an answer.
        Uses local LLM to create personalized, educational feedback.
        """
        
        # Get correct answer from options
        correct_option = next(
            (opt for opt in question.options if opt.is_correct is True),
            None
        )
        correct_answer_text = correct_option.option_text if correct_option else "N/A"
        
        # Generate feedback using LLM
        llm_feedback = await LLMService.generate_feedback(
            question_text=question.question_text,
            user_answer=user_answer,
            correct_answer=correct_answer_text,
            is_correct=is_correct
        )
        
        return FeedbackResponse(
            is_correct=is_correct,
            explanation=llm_feedback.get("explanation", ""),
            key_concepts=llm_feedback.get("key_concepts", []),
            next_topic_recommendation=llm_feedback.get("next_step"),
            confidence_score=llm_feedback.get("confidence_score", 0.8),
            effort_level=llm_feedback.get("effort_level", "medium")
        )
    
    @staticmethod
    def store_answer(
        db: Session,
        user_id: int,
        question_id: int,
        answer_text: str,
        is_correct: bool,
        time_spent: int,
        confidence_level: float = 0.5
    ) -> UserAnswer:
        """Store user's answer in database with confidence level"""
        answer = UserAnswer(
            user_id=user_id,
            question_id=question_id,
            answer_text=answer_text,
            is_correct=is_correct,
            time_spent_seconds=time_spent,
            confidence_level=confidence_level,
            created_at=datetime.utcnow()
        )
        db.add(answer)
        db.commit()
        db.refresh(answer)
        return answer
    
    @staticmethod
    def get_answer_history(db: Session, user_id: int, limit: int = 20):
        """Get user's recent answer history"""
        answers = db.query(UserAnswer).filter(
            UserAnswer.user_id == user_id
        ).order_by(UserAnswer.created_at.desc()).limit(limit).all()
        return answers
    
    @staticmethod
    def calculate_average_time(db: Session, user_id: int, topic_id: int) -> float:
        """Calculate average time spent on questions in a topic"""
        from sqlalchemy import func, join
        from app.models import Topic
        
        avg_time = db.query(func.avg(UserAnswer.time_spent_seconds)).join(
            Question
        ).filter(
            UserAnswer.user_id == user_id,
            Question.topic_id == topic_id,
            UserAnswer.time_spent_seconds > 0
        ).scalar()
        
        return avg_time or 0.0
    
    @staticmethod
    def get_confidence_distribution(db: Session, user_id: int) -> dict:
        """Get user's confidence level distribution"""
        answers = db.query(UserAnswer).filter(
            UserAnswer.user_id == user_id
        ).all()
        
        if not answers:
            return {
                "very_confident": 0,
                "confident": 0,
                "neutral": 0,
                "uncertain": 0,
                "very_uncertain": 0
            }
        
        conf_distribution = {
            "very_confident": 0,
            "confident": 0,
            "neutral": 0,
            "uncertain": 0,
            "very_uncertain": 0
        }
        
        for answer in answers:
            confidence = getattr(answer, 'confidence_level', 0.5)
            if confidence >= 0.9:
                conf_distribution["very_confident"] += 1
            elif confidence >= 0.7:
                conf_distribution["confident"] += 1
            elif confidence >= 0.5:
                conf_distribution["neutral"] += 1
            elif confidence >= 0.3:
                conf_distribution["uncertain"] += 1
            else:
                conf_distribution["very_uncertain"] += 1
        
        return conf_distribution

