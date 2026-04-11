from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

@router.get("/next-topic/{user_id}")
def get_next_topic_recommendation(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the next recommended topic to study.
    This implements the personalized recommendation requirement (FR3).
    Prioritizes weak topics first, then suggests new topics.
    """
    try:
        recommendation = RecommendationService.get_next_topic_recommendation(
            db, 
            user_id
        )
        
        if not recommendation:
            return {
                "message": "No topics available",
                "user_id": user_id
            }
        
        return {
            "topic_id": recommendation.id,
            "topic_name": recommendation.name,
            "description": recommendation.description,
            "difficulty_level": recommendation.difficulty_level
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/learning-path/{user_id}")
def get_personalized_learning_path(
    user_id: int,
    subject_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Get personalized learning path.
    Returns topics prioritized by user's current performance and needs.
    Addresses FR3: Recommend what learner should study next.
    """
    try:
        learning_path = RecommendationService.get_personalized_learning_path(
            db,
            user_id,
            subject_id
        )
        
        return {
            "user_id": user_id,
            "path": learning_path,
            "total_topics": len(learning_path)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/should-review/{user_id}/{topic_id}")
def check_if_should_review(
    user_id: int,
    topic_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if user should review a topic based on spaced repetition.
    Uses natural forgetting curve to optimize review timing.
    """
    should_review = RecommendationService.should_review_topic(
        db,
        user_id,
        topic_id
    )
    
    return {
        "user_id": user_id,
        "topic_id": topic_id,
        "should_review": should_review
    }
