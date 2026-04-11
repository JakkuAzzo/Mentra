from datetime import datetime
from sqlalchemy.orm import Session
from app.models import UserAnswer, Question
from app.schemas.schemas import FeedbackResponse

class FeedbackService:
    """
    Service for generating AI-powered feedback on student answers.
    This module will integrate with OpenAI or open-source LLM.
    """
    
    @staticmethod
    def generate_feedback(
        db: Session,
        question: Question,
        user_answer: str,
        is_correct: bool
    ) -> FeedbackResponse:
        """
        Generate step-by-step explanation and feedback for an answer.
        Will use LLM to create personalized, educational feedback.
        """
        
        # Placeholder for LLM integration
        # In production, this will call OpenAI API or local LLM
        
        if is_correct:
            explanation = f"Great! Your answer is correct. The question was: {question.question_text}"
            key_concepts = ["Concept 1", "Concept 2"]
            confidence_score = 0.95
        else:
            explanation = f"Your answer needs review. Let's break this down step-by-step:\n"
            explanation += f"Question: {question.question_text}\n"
            explanation += f"Your answer: {user_answer}\n"
            explanation += "Let me walk you through the correct approach..."
            key_concepts = ["Concept 1", "Concept 2", "Concept 3"]
            confidence_score = 0.85
        
        return FeedbackResponse(
            is_correct=is_correct,
            explanation=explanation,
            key_concepts=key_concepts,
            next_topic_recommendation=None,
            confidence_score=confidence_score
        )
    
    @staticmethod
    def store_answer(
        db: Session,
        user_id: int,
        question_id: int,
        answer_text: str,
        is_correct: bool,
        time_spent: int
    ) -> UserAnswer:
        """Store user's answer in database"""
        answer = UserAnswer(
            user_id=user_id,
            question_id=question_id,
            answer_text=answer_text,
            is_correct=is_correct,
            time_spent_seconds=time_spent,
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
