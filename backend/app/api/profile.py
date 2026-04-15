# pyright: reportGeneralTypeIssues=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportAssignmentType=false
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models import User, UserProfile, UserProgress, CommunityMembership, CommunityTrophy, CommunityCourse
from app.schemas.schemas import (
    ProfileUpdateRequest,
    PasswordUpdateRequest,
)
import os
import shutil
from pathlib import Path

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "profiles"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _get_or_create_profile(db: Session, user_id: int) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        return profile

    profile = UserProfile(user_id=user_id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _build_stats(db: Session, user_id: int) -> dict:
    progress_records = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    total_questions_attempted = sum(record.questions_attempted for record in progress_records)
    total_questions_correct = sum(record.questions_correct for record in progress_records)
    total_accuracy = (total_questions_correct / total_questions_attempted * 100) if total_questions_attempted else 0.0
    topics_mastered = sum(1 for record in progress_records if record.accuracy_score >= 85)

    communities_joined = db.query(CommunityMembership).filter(CommunityMembership.user_id == user_id).count()
    trophies_earned = db.query(CommunityTrophy).filter(CommunityTrophy.user_id == user_id).count()

    courses = db.query(CommunityCourse).all()
    topic_accuracy = {record.topic_id: record.accuracy_score for record in progress_records}
    courses_completed = 0
    for course in courses:
        if course.topic_id is not None and topic_accuracy.get(course.topic_id, 0) >= 80:
            courses_completed += 1

    return {
        "total_questions_attempted": total_questions_attempted,
        "total_accuracy": round(float(total_accuracy), 1),
        "topics_mastered": topics_mastered,
        "communities_joined": communities_joined,
        "trophies_earned": trophies_earned,
        "courses_completed": courses_completed,
    }


def _build_cv(db: Session, user: User, profile: UserProfile) -> dict:
    stats = _build_stats(db, user.id)
    trophies = db.query(CommunityTrophy).filter(CommunityTrophy.user_id == user.id).order_by(CommunityTrophy.awarded_at.desc()).all()

    trophy_items = []
    achievements = []
    for trophy in trophies[:12]:
        trophy_items.append(
            {
                "title": trophy.title,
                "milestone_type": trophy.milestone_type,
                "awarded_at": trophy.awarded_at.strftime("%Y-%m-%d"),
            }
        )
        achievements.append(f"{trophy.title} ({trophy.milestone_type.replace('_', ' ')})")

    progress_records = db.query(UserProgress).filter(UserProgress.user_id == user.id).all()
    course_completions = []
    for progress in progress_records:
        if progress.accuracy_score >= 80:
            course_completions.append(f"{progress.topic.name} - {progress.accuracy_score:.1f}% mastery")

    if not achievements:
        achievements = [
            f"Maintained an average accuracy of {stats['total_accuracy']:.1f}% across completed practice sessions.",
            "Actively engaged in adaptive learning pathways and peer community progress.",
        ]

    full_name = user.full_name or user.username
    headline = profile.cv_headline or "Adaptive Learner and Community Contributor"
    summary = profile.cv_summary or (
        f"{full_name} has completed {stats['total_questions_attempted']} guided practice questions, "
        f"earned {stats['trophies_earned']} milestone trophies, and demonstrated growth across personalized courses."
    )

    return {
        "full_name": full_name,
        "display_name": profile.display_name,
        "headline": headline,
        "summary": summary,
        "achievements": achievements,
        "course_completions": course_completions,
        "milestone_trophies": trophy_items,
    }


@router.get("/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    profile = _get_or_create_profile(db, user_id)
    stats = _build_stats(db, user_id)

    return {
        "user_id": int(user.id),
        "email": str(user.email),
        "username": str(user.username),
        "full_name": user.full_name,
        "role": str(user.role),
        "display_name": profile.display_name,
        "avatar_style": str(profile.avatar_style),
        "profile_image_url": profile.profile_image_url,
        "bio": profile.bio,
        "institution": profile.institution,
        "workplace": profile.workplace,
        "cv_headline": profile.cv_headline,
        "cv_summary": profile.cv_summary,
        "stats": stats,
    }


@router.put("/{user_id}")
def update_profile(user_id: int, payload: ProfileUpdateRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    profile = _get_or_create_profile(db, user_id)

    if payload.email and payload.email != user.email:
        existing = db.query(User).filter(User.email == payload.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        user.email = payload.email

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.display_name is not None:
        profile.display_name = payload.display_name
    if payload.avatar_style is not None:
        profile.avatar_style = payload.avatar_style
    if payload.profile_image_url is not None:
        profile.profile_image_url = payload.profile_image_url
    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.institution is not None:
        profile.institution = payload.institution
    if payload.workplace is not None:
        profile.workplace = payload.workplace
    if payload.cv_headline is not None:
        profile.cv_headline = payload.cv_headline
    if payload.cv_summary is not None:
        profile.cv_summary = payload.cv_summary

    db.commit()
    db.refresh(user)
    db.refresh(profile)

    return get_profile(user_id, db)


@router.put("/{user_id}/password")
def update_password(user_id: int, payload: PasswordUpdateRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)

    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()

    return {"status": "password_updated"}


@router.get("/{user_id}/cv")
def get_profile_cv(user_id: int, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    profile = _get_or_create_profile(db, user_id)
    return _build_cv(db, user, profile)


@router.post("/{user_id}/image")
async def upload_profile_image(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload profile image. Returns updated profile with image_url."""
    user = _get_user_or_404(db, user_id)
    profile = _get_or_create_profile(db, user_id)

    # Validate file type (images only)
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files (JPEG, PNG, GIF, WebP) are allowed"
        )

    # Validate file size (max 5MB)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to start
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )

    # Save file
    try:
        # Generate unique filename: user_<id>_<timestamp>.<ext>
        import time
        ext = file.filename.split(".")[-1] if file.filename else "jpg"
        filename = f"user_{user_id}_{int(time.time())}.{ext}"
        filepath = UPLOAD_DIR / filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update profile with image URL
        image_url = f"/uploads/profiles/{filename}"
        profile.profile_image_url = image_url
        db.commit()
        db.refresh(profile)

        return {
            "status": "image_uploaded",
            "image_url": image_url,
            "profile": {
                "user_id": int(user.id),
                "display_name": profile.display_name,
                "avatar_style": str(profile.avatar_style),
                "profile_image_url": profile.profile_image_url,
            }
        }

    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
