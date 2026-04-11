from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/api/progress", tags=["progress"])

@router.get("/user/{user_id}")
def get_user_progress(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user's progress across all topics.
    This implements the progress tracking requirement (FR6).
    """
    try:
        progress = ProgressService.get_user_progress(db, user_id)
        return {
            "user_id": user_id,
            "progress_records": progress,
            "count": len(progress)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/summary/{user_id}")
def get_learning_summary(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive learning summary with visibility of improvement.
    This addresses the "highlight improvement over time" requirement.
    """
    try:
        summary = ProgressService.get_user_summary(db, user_id)
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/weak-topics/{user_id}")
def get_weak_topics(
    user_id: int,
    threshold: float = 70.0,
    db: Session = Depends(get_db)
):
    """
    Get weakest topics for user.
    Topics below threshold are considered weak areas.
    """
    weak_topics = ProgressService.get_weak_topics(db, user_id, threshold)
    return {
        "user_id": user_id,
        "weak_topics": weak_topics,
        "threshold": threshold,
        "count": len(weak_topics)
    }
