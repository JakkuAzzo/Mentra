from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
from app.core.database import get_db
from app.services.progress_service import ProgressService
from app.models import UserAnswer, ExperimentEvent
from app.schemas.schemas import ExperimentEventCreate

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


@router.get("/evidence/{user_id}")
def get_outcome_evidence(user_id: int, db: Session = Depends(get_db)):
    """Return measurable baseline-vs-current outcomes for dissertation-grade evidence surfacing."""
    answers = db.query(UserAnswer).filter(UserAnswer.user_id == user_id).order_by(UserAnswer.created_at.asc()).all()
    if not answers:
        return {
            "user_id": user_id,
            "baseline_accuracy": 0.0,
            "current_accuracy": 0.0,
            "learning_gain": 0.0,
            "baseline_window_attempts": 0,
            "current_window_attempts": 0,
            "total_questions_answered": 0,
            "confidence_trend": 0.0,
        }

    window = min(10, len(answers))
    baseline = answers[:window]
    current = answers[-window:]

    baseline_accuracy = sum(1 for a in baseline if a.is_correct is True) / len(baseline)
    current_accuracy = sum(1 for a in current if a.is_correct is True) / len(current)
    baseline_conf = sum(float(getattr(a, "confidence_level", 0.5)) for a in baseline) / len(baseline)
    current_conf = sum(float(getattr(a, "confidence_level", 0.5)) for a in current) / len(current)

    return {
        "user_id": user_id,
        "baseline_accuracy": round(baseline_accuracy, 3),
        "current_accuracy": round(current_accuracy, 3),
        "learning_gain": round(current_accuracy - baseline_accuracy, 3),
        "baseline_window_attempts": len(baseline),
        "current_window_attempts": len(current),
        "total_questions_answered": len(answers),
        "confidence_trend": round(current_conf - baseline_conf, 3),
    }


@router.post("/experiments/{user_id}/events")
def log_experiment_event(
    user_id: int,
    payload: ExperimentEventCreate,
    db: Session = Depends(get_db),
):
    event = ExperimentEvent(
        user_id=user_id,
        session_token=payload.session_token,
        event_name=payload.event_name,
        event_payload=json.dumps(payload.event_payload),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"status": "logged", "event_id": event.id}


@router.get("/experiments/{user_id}/events")
def list_experiment_events(user_id: int, limit: int = 50, db: Session = Depends(get_db)):
    events = (
        db.query(ExperimentEvent)
        .filter(ExperimentEvent.user_id == user_id)
        .order_by(ExperimentEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "user_id": user_id,
        "count": len(events),
        "events": [
            {
                "id": e.id,
                "session_token": e.session_token,
                "event_name": e.event_name,
                "event_payload": json.loads(e.event_payload) if e.event_payload else {},
                "created_at": e.created_at,
            }
            for e in events
        ],
    }
