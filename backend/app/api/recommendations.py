from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import get_settings
from app.services.recommendation_service import RecommendationService
from app.services.spaced_repetition_service import SpacedRepetitionService, SessionAnalyticsService
from app.services.question_service import QuestionService
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

class TopicReviewItem(BaseModel):
    """Topic due for review with urgency level"""
    topic_id: int
    topic_name: str
    days_overdue: int
    priority_score: float
    last_reviewed: Optional[datetime]
    current_accuracy: float

class MasteryPrediction(BaseModel):
    """Prediction of when user will master a topic"""
    topic_id: int
    topic_name: str
    current_accuracy: float
    estimated_days_to_mastery: int
    estimated_mastery_date: datetime
    confidence_level: str  # low, medium, high

class SessionStats(BaseModel):
    """Overall learning session statistics"""
    total_sessions: int
    total_hours_learned: float
    average_session_length_minutes: float
    peak_learning_hour: int
    current_streak_days: int
    consistency_score: float  # 0-100
    total_questions_answered: int
    average_accuracy: float

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

@router.get("/due-for-review/{user_id}", response_model=List[TopicReviewItem])
def get_topics_due_for_review(
    user_id: int,
    db: Session = Depends(get_db),
    settings = Depends(get_settings)
):
    """
    Get all topics that are due for review based on spaced repetition algorithm.
    Returns topics sorted by priority (most urgent first).
    
    Implements FR3: Spaced Repetition Learning Optimization
    Uses Ebbinghaus forgetting curve: [1, 3, 7, 14, 30, 60, 120] days intervals
    """
    try:
        if not settings.ENABLE_SPACED_REPETITION:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Spaced repetition feature is disabled"
            )
        
        topics_due = SpacedRepetitionService.get_topics_due_for_review(db, user_id)
        
        response = []
        for topic in topics_due:
            # Get last review date and current accuracy
            last_answer = QuestionService.get_user_last_answer_for_topic(db, user_id, topic.id)
            accuracy = QuestionService.get_topic_accuracy(db, user_id, topic.id)
            
            days_overdue = (datetime.utcnow() - last_answer.created_at).days if last_answer else 999
            priority_score = SpacedRepetitionService._calculate_priority_score(
                accuracy,
                days_overdue,
                topic.difficulty_level or 1.0
            )
            
            response.append(TopicReviewItem(
                topic_id=topic.id,
                topic_name=topic.name,
                days_overdue=max(0, days_overdue),
                priority_score=priority_score,
                last_reviewed=last_answer.created_at if last_answer else None,
                current_accuracy=accuracy
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch due-for-review topics: {str(e)}"
        )

@router.get("/mastery-date/{user_id}/{topic_id}", response_model=MasteryPrediction)
def get_mastery_prediction(
    user_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    settings = Depends(get_settings)
):
    """
    Get estimated date when user will reach mastery (85% accuracy) for a topic.
    
    Implements FR4: Performance Prediction
    Factors: current accuracy trend, difficulty level, consistency
    """
    try:
        if not settings.ENABLE_PERFORMANCE_PREDICTION:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Performance prediction feature is disabled"
            )
        
        topic = QuestionService.get_topic_by_id(db, topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
        # Get mastery estimate
        mastery_info = SpacedRepetitionService.estimate_mastery_date(
            db,
            user_id,
            topic_id
        )
        
        current_accuracy = QuestionService.get_topic_accuracy(db, user_id, topic_id)
        
        # Determine confidence based on consistency and data points
        accuracy_samples = QuestionService.get_user_answers_for_topic(db, user_id, topic_id)
        consistency = len(accuracy_samples) > 5  # at least 5 attempts
        
        if current_accuracy >= 0.85:
            confidence_level = "high"
        elif consistency and current_accuracy >= 0.70:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        return MasteryPrediction(
            topic_id=topic_id,
            topic_name=topic.name,
            current_accuracy=current_accuracy,
            estimated_days_to_mastery=mastery_info["days_remaining"],
            estimated_mastery_date=mastery_info["mastery_date"],
            confidence_level=confidence_level
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict mastery date: {str(e)}"
        )

@router.get("/session-stats/{user_id}", response_model=SessionStats)
def get_session_statistics(
    user_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    settings = Depends(get_settings)
):
    """
    Get comprehensive session analytics for a user over the specified period.
    
    Implements FR5: Session Analytics & Engagement Tracking
    Default: last 7 days, can query up to 90 days
    """
    try:
        if not settings.ENABLE_SESSION_ANALYTICS:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Session analytics feature is disabled"
            )
        
        stats = SessionAnalyticsService.calculate_session_stats(db, user_id, days)
        
        # Calculate average accuracy across all answers in period
        answers = QuestionService.get_user_answers_in_period(db, user_id, days)
        avg_accuracy = (
            sum(1 for a in answers if a.is_correct) / len(answers)
            if answers else 0.0
        )
        
        return SessionStats(
            total_sessions=stats["total_sessions"],
            total_hours_learned=stats["total_hours"],
            average_session_length_minutes=stats["avg_session_length_minutes"],
            peak_learning_hour=stats["peak_hour"],
            current_streak_days=stats["streak"],
            consistency_score=stats["consistency_score"],
            total_questions_answered=len(answers),
            average_accuracy=avg_accuracy
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session statistics: {str(e)}"
        )

@router.get("/personalized/{user_id}")
def get_personalized_recommendations(
    user_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    settings = Depends(get_settings)
):
    """
    Get personalized learning recommendations for user.
    Combines spaced repetition + performance prediction + session insights.
    
    Returns ranked list of topics to focus on based on:
    1. Topics overdue for review (spaced repetition)
    2. Topics with declining accuracy (performance prediction)
    3. User's learning patterns (session analytics)
    """
    try:
        if not settings.ENABLE_SPACED_REPETITION:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Personalized recommendations require spaced repetition feature"
            )
        
        # Get due-for-review topics
        due_topics = SpacedRepetitionService.get_topics_due_for_review(db, user_id)
        
        recommendations = []
        for topic in due_topics[:limit]:
            accuracy = QuestionService.get_topic_accuracy(db, user_id, topic.id)
            last_answer = QuestionService.get_user_last_answer_for_topic(db, user_id, topic.id)
            days_since = (datetime.utcnow() - last_answer.created_at).days if last_answer else 999
            
            recommendations.append({
                "topic_id": topic.id,
                "topic_name": topic.name,
                "reason": "overdue_review" if days_since > 7 else "practice_needed",
                "current_accuracy": accuracy,
                "urgency": "high" if days_since > 14 else "medium",
                "estimated_time_minutes": 15 + int(accuracy * 10)  # less time if mastered
            })
        
        return {"recommendations": recommendations, "count": len(recommendations)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate personalized recommendations: {str(e)}"
        )
