from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import QuestionResponse, FeedbackRequest, FeedbackResponse
from app.services.question_service import QuestionService
from app.services.feedback_service import FeedbackService
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/api/questions", tags=["questions"])

@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific question"""
    try:
        question = QuestionService.get_question_by_id(db, question_id)
        return question
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/topic/{topic_id}")
def get_questions_by_topic(
    topic_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all questions for a topic"""
    questions = QuestionService.get_questions_by_topic(db, topic_id, limit)
    return {"questions": questions, "count": len(questions)}

@router.get("/adaptive/{user_id}/{topic_id}")
def get_next_adaptive_question(
    user_id: int,
    topic_id: int,
    db: Session = Depends(get_db)
):
    """
    Get next adaptive question based on user's performance.
    This implements adaptive difficulty adjustment.
    """
    try:
        question = QuestionService.get_adaptive_question(db, user_id, topic_id)
        return question
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/submit-answer", response_model=FeedbackResponse)
def submit_answer(
    user_id: int,
    feedback_request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit an answer and receive AI-powered feedback.
    This implements the step-by-step feedback requirement (FR2).
    """
    try:
        question = QuestionService.get_question_by_id(db, feedback_request.question_id)
        
        # Check if answer is correct
        is_correct = False
        if question.question_type == "multiple_choice":
            # Get correct option
            correct_option = next(
                (opt for opt in question.options if opt.is_correct),
                None
            )
            is_correct = (feedback_request.user_answer == str(correct_option.id)) if correct_option else False
        
        # Generate AI feedback
        feedback = FeedbackService.generate_feedback(
            db,
            question,
            feedback_request.user_answer,
            is_correct
        )
        
        # Store answer
        stored_answer = FeedbackService.store_answer(
            db,
            user_id,
            feedback_request.question_id,
            feedback_request.user_answer,
            is_correct,
            feedback_request.time_spent
        )
        
        # Update progress
        ProgressService.update_user_progress(
            db,
            user_id,
            question.topic_id,
            is_correct
        )
        
        return feedback
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
