# pyright: reportGeneralTypeIssues=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportAssignmentType=false
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.services.question_service import QuestionService
from app.services.recommendation_service import RecommendationService
from app.services.spaced_repetition_service import SessionAnalyticsService, SpacedRepetitionService

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class TopicReviewItem(BaseModel):
    """Topic due for review with urgency level."""

    topic_id: int
    topic_name: str
    days_overdue: int
    priority_score: float
    last_reviewed: Optional[datetime]
    current_accuracy: float
    reason_codes: List[str] = []


class MasteryPrediction(BaseModel):
    """Prediction of when user will master a topic."""

    topic_id: int
    topic_name: str
    current_accuracy: float
    estimated_days_to_mastery: int
    estimated_mastery_date: datetime
    confidence_level: str  # low, medium, high
    confidence_interval_low: float
    confidence_interval_high: float


class SessionStats(BaseModel):
    """Overall learning session statistics."""

    total_sessions: int
    total_hours_learned: float
    average_session_length_minutes: float
    peak_learning_hour: int
    current_streak_days: int
    consistency_score: float  # 0-100
    total_questions_answered: int
    average_accuracy: float


def _build_reason_codes(accuracy: float, days_since: int, avg_confidence: float) -> List[str]:
    reason_codes: List[str] = []
    if accuracy < 0.6:
        reason_codes.append("low_accuracy")
    if days_since >= 7:
        reason_codes.append("overdue_review")
    if avg_confidence < 0.45:
        reason_codes.append("low_confidence")
    if days_since >= 14 and accuracy < 0.75:
        reason_codes.append("streak_risk")
    if not reason_codes:
        reason_codes.append("momentum_build")
    return reason_codes


@router.get("/next-topic/{user_id}")
def get_next_topic_recommendation(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the next recommended topic to study.
    This implements the personalized recommendation requirement (FR3).
    Prioritizes weak topics first, then suggests new topics.
    """
    try:
        recommendation = RecommendationService.get_next_topic_recommendation(db, user_id)

        if not recommendation:
            return {
                "message": "No topics available",
                "user_id": user_id,
            }

        return {
            "topic_id": recommendation.id,
            "topic_name": recommendation.name,
            "description": recommendation.description,
            "difficulty_level": recommendation.difficulty_level,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/learning-path/{user_id}")
def get_personalized_learning_path(
    user_id: int,
    subject_id: int = None,
    db: Session = Depends(get_db),
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
            subject_id,
        )

        return {
            "user_id": user_id,
            "path": learning_path,
            "total_topics": len(learning_path),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/should-review/{user_id}/{topic_id}")
def check_if_should_review(
    user_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
):
    """
    Check if user should review a topic based on spaced repetition.
    Uses natural forgetting curve to optimize review timing.
    """
    should_review = RecommendationService.should_review_topic(db, user_id, topic_id)

    return {
        "user_id": user_id,
        "topic_id": topic_id,
        "should_review": should_review,
    }


@router.get("/due-for-review/{user_id}", response_model=List[TopicReviewItem])
def get_topics_due_for_review(
    user_id: int,
    db: Session = Depends(get_db),
    settings=Depends(get_settings),
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
                detail="Spaced repetition feature is disabled",
            )

        topics_due = SpacedRepetitionService.get_topics_due_for_review(db, user_id)

        response = []
        for topic in topics_due:
            last_answer = QuestionService.get_user_last_answer_for_topic(db, user_id, topic.id)
            accuracy = QuestionService.get_topic_accuracy(db, user_id, topic.id)
            answers = QuestionService.get_user_answers_for_topic(db, user_id, topic.id)
            avg_confidence = (
                sum(float(getattr(a, "confidence_level", 0.5)) for a in answers) / len(answers)
                if answers
                else 0.5
            )

            days_overdue = (datetime.utcnow() - last_answer.created_at).days if last_answer else 999
            priority_score = SpacedRepetitionService._calculate_priority_score(
                accuracy,
                days_overdue,
                topic.difficulty_level or 1.0,
            )

            response.append(
                TopicReviewItem(
                    topic_id=topic.id,
                    topic_name=topic.name,
                    days_overdue=max(0, days_overdue),
                    priority_score=priority_score,
                    last_reviewed=last_answer.created_at if last_answer else None,
                    current_accuracy=accuracy,
                    reason_codes=_build_reason_codes(accuracy, days_overdue, avg_confidence),
                )
            )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch due-for-review topics: {str(e)}",
        )


@router.get("/mastery-date/{user_id}/{topic_id}", response_model=MasteryPrediction)
def get_mastery_prediction(
    user_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    settings=Depends(get_settings),
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
                detail="Performance prediction feature is disabled",
            )

        topic = QuestionService.get_topic_by_id(db, topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )

        mastery_info = SpacedRepetitionService.estimate_mastery_date(db, user_id, topic_id)
        current_accuracy = QuestionService.get_topic_accuracy(db, user_id, topic_id)

        accuracy_samples = QuestionService.get_user_answers_for_topic(db, user_id, topic_id)
        consistency = len(accuracy_samples) > 5

        if current_accuracy >= 0.85:
            confidence_level = "high"
        elif consistency and current_accuracy >= 0.70:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        spread = 0.18 if not consistency else (0.12 if confidence_level == "medium" else 0.08)
        confidence_interval_low = max(0.0, current_accuracy - spread)
        confidence_interval_high = min(1.0, current_accuracy + spread)

        return MasteryPrediction(
            topic_id=topic_id,
            topic_name=topic.name,
            current_accuracy=current_accuracy,
            estimated_days_to_mastery=mastery_info["days_remaining"],
            estimated_mastery_date=mastery_info["mastery_date"],
            confidence_level=confidence_level,
            confidence_interval_low=round(confidence_interval_low, 3),
            confidence_interval_high=round(confidence_interval_high, 3),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict mastery date: {str(e)}",
        )


@router.get("/session-stats/{user_id}", response_model=SessionStats)
def get_session_statistics(
    user_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    settings=Depends(get_settings),
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
                detail="Session analytics feature is disabled",
            )

        stats = SessionAnalyticsService.calculate_session_stats(db, user_id, days)

        answers = QuestionService.get_user_answers_in_period(db, user_id, days)
        avg_accuracy = (sum(1 for a in answers if a.is_correct is True) / len(answers) if answers else 0.0)

        return SessionStats(
            total_sessions=stats["total_sessions"],
            total_hours_learned=stats["total_hours"],
            average_session_length_minutes=stats["avg_session_length_minutes"],
            peak_learning_hour=stats["peak_hour"],
            current_streak_days=stats["streak"],
            consistency_score=stats["consistency_score"],
            total_questions_answered=len(answers),
            average_accuracy=avg_accuracy,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session statistics: {str(e)}",
        )


@router.get("/personalized/{user_id}")
def get_personalized_recommendations(
    user_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    settings=Depends(get_settings),
):
    """
    Get personalized learning recommendations for user.
    Combines spaced repetition + performance prediction + session insights.
    """
    try:
        if not settings.ENABLE_SPACED_REPETITION:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Personalized recommendations require spaced repetition feature",
            )

        due_topics = SpacedRepetitionService.get_topics_due_for_review(db, user_id)

        recommendations = []
        for topic in due_topics[:limit]:
            accuracy = QuestionService.get_topic_accuracy(db, user_id, topic.id)
            last_answer = QuestionService.get_user_last_answer_for_topic(db, user_id, topic.id)
            days_since = (datetime.utcnow() - last_answer.created_at).days if last_answer else 999
            answers = QuestionService.get_user_answers_for_topic(db, user_id, topic.id)
            avg_confidence = (
                sum(float(getattr(a, "confidence_level", 0.5)) for a in answers) / len(answers)
                if answers
                else 0.5
            )
            spread = 0.15 if len(answers) < 5 else 0.09
            reason_codes = _build_reason_codes(accuracy, days_since, avg_confidence)

            recommendations.append(
                {
                    "topic_id": topic.id,
                    "topic_name": topic.name,
                    "reason": "overdue_review" if days_since > 7 else "practice_needed",
                    "reason_codes": reason_codes,
                    "current_accuracy": accuracy,
                    "urgency": "high" if days_since > 14 else "medium",
                    "confidence_interval_low": round(max(0.0, accuracy - spread), 3),
                    "confidence_interval_high": round(min(1.0, accuracy + spread), 3),
                    "estimated_time_minutes": 15 + int(accuracy * 10),
                }
            )

        return {"recommendations": recommendations, "count": len(recommendations)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate personalized recommendations: {str(e)}",
        )


@router.get("/next-best/{user_id}")
def get_next_best_topic(
    user_id: int,
    db: Session = Depends(get_db),
    settings=Depends(get_settings),
):
    """Get next-best topic recommendation with explainability and confidence interval."""
    personalized = get_personalized_recommendations(user_id=user_id, limit=1, db=db, settings=settings)
    recommendations = personalized.get("recommendations", [])
    if not recommendations:
        return {"next_best": None}
    next_best = recommendations[0]
    return {
        "next_best": {
            "topic_id": next_best["topic_id"],
            "topic_name": next_best["topic_name"],
            "reason_codes": next_best.get("reason_codes", []),
            "confidence_interval_low": next_best.get("confidence_interval_low", 0.0),
            "confidence_interval_high": next_best.get("confidence_interval_high", 0.0),
            "urgency": next_best.get("urgency", "medium"),
        }
    }
