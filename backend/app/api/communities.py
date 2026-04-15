# pyright: reportGeneralTypeIssues=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportAssignmentType=false
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import (
    Community,
    CommunityMembership,
    CommunityCourse,
    CommunityGame,
    CommunityTrophy,
    Topic,
    User,
    UserProgress,
)
from app.schemas.schemas import (
    CommunityCreate,
    CommunityCourseCreate,
    CommunityTrophyCreate,
)

router = APIRouter(prefix="/api/communities", tags=["communities"])

PRIVILEGED_COMMUNITY_CREATORS = {"teacher", "admin", "manager", "analyst"}
EDU_LINKED_CATEGORIES = {"school", "university", "college"}


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _is_community_leader(db: Session, community_id: int, user_id: int) -> bool:
    membership = db.query(CommunityMembership).filter(
        CommunityMembership.community_id == community_id,
        CommunityMembership.user_id == user_id,
    ).first()
    return bool(membership and membership.role in {"leader", "moderator"})


def _serialize_community(community: Community, member_count: int) -> dict:
    return {
        "id": int(community.id),
        "name": str(community.name),
        "description": community.description,
        "category": str(community.category),
        "community_type": str(community.community_type),
        "organization_name": community.organization_name,
        "is_linked": bool(community.is_linked),
        "created_by": int(community.created_by),
        "created_at": community.created_at,
        "member_count": member_count,
    }


def _serialize_course(course: CommunityCourse) -> dict:
    return {
        "id": int(course.id),
        "title": str(course.title),
        "description": course.description,
        "topic_id": int(course.topic_id) if course.topic_id is not None else None,
        "topic_name": course.topic.name if course.topic else None,
        "milestone_points": int(course.milestone_points),
    }


def _serialize_trophy(trophy: CommunityTrophy) -> dict:
    return {
        "id": int(trophy.id),
        "user_id": int(trophy.user_id),
        "username": str(trophy.recipient.username),
        "title": str(trophy.title),
        "description": trophy.description,
        "milestone_type": str(trophy.milestone_type),
        "awarded_at": trophy.awarded_at,
    }


@router.post("")
def create_community(payload: CommunityCreate, db: Session = Depends(get_db)):
    creator = _get_user_or_404(db, payload.user_id)

    if payload.is_linked and payload.category in EDU_LINKED_CATEGORIES and creator.role not in PRIVILEGED_COMMUNITY_CREATORS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Linked school/university/college communities can only be created by teachers, admins, managers, or analysts.",
        )

    community = Community(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        community_type=payload.community_type,
        organization_name=payload.organization_name,
        is_linked=payload.is_linked,
        created_by=creator.id,
    )
    db.add(community)
    db.flush()

    db.add(
        CommunityMembership(
            community_id=community.id,
            user_id=creator.id,
            role="leader",
        )
    )

    # Linked communities get built-in educational game modules for engagement.
    if payload.is_linked:
        db.add_all(
            [
                CommunityGame(
                    community_id=community.id,
                    title="Kahoot Challenge Arena",
                    game_type="kahoot",
                    description="Weekly timed quiz battles with instant ranking updates.",
                ),
                CommunityGame(
                    community_id=community.id,
                    title="Streak Sprint",
                    game_type="streak_sprint",
                    description="Maintain daily learning streaks to unlock bonus trophies.",
                ),
            ]
        )

    db.commit()
    db.refresh(community)

    member_count = db.query(CommunityMembership).filter(CommunityMembership.community_id == community.id).count()
    return _serialize_community(community, member_count)


@router.get("")
def list_communities(
    user_id: int,
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    _get_user_or_404(db, user_id)

    all_query = db.query(Community)
    if category:
        all_query = all_query.filter(Community.category == category)

    all_communities = all_query.order_by(Community.created_at.desc()).all()
    memberships = db.query(CommunityMembership).filter(CommunityMembership.user_id == user_id).all()
    joined_ids = {m.community_id for m in memberships}

    joined = []
    discover = []
    for community in all_communities:
        member_count = db.query(CommunityMembership).filter(CommunityMembership.community_id == community.id).count()
        item = _serialize_community(community, member_count)
        if community.id in joined_ids:
            joined.append(item)
        else:
            discover.append(item)

    return {
        "joined": joined,
        "discover": discover,
        "first_run": len(joined) == 0,
        "onboarding_suggestions": discover[:3],
    }


@router.post("/{community_id}/join")
def join_community(community_id: int, user_id: int, db: Session = Depends(get_db)):
    _get_user_or_404(db, user_id)
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    existing = db.query(CommunityMembership).filter(
        CommunityMembership.community_id == community_id,
        CommunityMembership.user_id == user_id,
    ).first()
    if existing:
        return {"status": "already_joined"}

    db.add(CommunityMembership(community_id=community_id, user_id=user_id, role="member"))
    db.commit()
    return {"status": "joined"}


@router.get("/{community_id}/courses")
def list_community_courses(community_id: int, db: Session = Depends(get_db)):
    courses = db.query(CommunityCourse).filter(CommunityCourse.community_id == community_id).order_by(CommunityCourse.created_at.desc()).all()
    return [_serialize_course(course) for course in courses]


@router.post("/{community_id}/courses")
def create_community_course(community_id: int, payload: CommunityCourseCreate, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, payload.user_id)
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    if user.role not in PRIVILEGED_COMMUNITY_CREATORS and not _is_community_leader(db, community_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only leaders or privileged roles can create community courses")

    if payload.topic_id:
        topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    course = CommunityCourse(
        community_id=community_id,
        title=payload.title,
        description=payload.description,
        topic_id=payload.topic_id,
        milestone_points=payload.milestone_points,
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    return _serialize_course(course)


@router.get("/{community_id}/leaderboard")
def get_community_leaderboard(community_id: int, db: Session = Depends(get_db)):
    from app.models import UserStreak, BadgeTier
    
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    memberships = db.query(CommunityMembership).filter(CommunityMembership.community_id == community_id).all()
    courses = db.query(CommunityCourse).filter(CommunityCourse.community_id == community_id).all()
    course_topic_ids = {course.topic_id for course in courses if course.topic_id is not None}

    rankings = []
    for membership in memberships:
        user = membership.user
        if course_topic_ids:
            progress_records = db.query(UserProgress).filter(
                UserProgress.user_id == user.id,
                UserProgress.topic_id.in_(course_topic_ids),
            ).all()
        else:
            progress_records = db.query(UserProgress).filter(UserProgress.user_id == user.id).all()

        attempted = sum(p.questions_attempted for p in progress_records)
        correct = sum(p.questions_correct for p in progress_records)
        average_accuracy = float(sum(float(p.accuracy_score) for p in progress_records) / len(progress_records)) if progress_records else 0.0
        courses_completed = sum(1 for p in progress_records if p.accuracy_score >= 80)

        trophies = db.query(CommunityTrophy).filter(
            CommunityTrophy.community_id == community_id,
            CommunityTrophy.user_id == user.id,
        ).count()

        score = (correct * 10) + (courses_completed * 40) + (trophies * 25) + int(average_accuracy * 2)
        
        # Get tier based on score
        def _get_tier(s):
            if s >= 5000:
                return "platinum"
            elif s >= 2500:
                return "gold"
            elif s >= 1000:
                return "silver"
            else:
                return "bronze"
        
        tier = _get_tier(score)
        
        # Get current streak
        streak = db.query(UserStreak).filter(
            UserStreak.user_id == user.id,
            UserStreak.community_id == community_id
        ).first()
        current_streak = streak.current_streak if streak else 0

        rankings.append(
            {
                "user_id": user.id,
                "username": user.username,
                "display_name": user.profile.display_name if user.profile and user.profile.display_name else (user.full_name or user.username),
                "questions_attempted": attempted,
                "average_accuracy": round(average_accuracy, 1),
                "courses_completed": courses_completed,
                "trophies": trophies,
                "score": score,
                "tier": tier,
                "current_streak": current_streak,
            }
        )

    rankings.sort(key=lambda row: row["score"], reverse=True)
    for idx, row in enumerate(rankings, 1):
        row["rank"] = idx

    return {"community_id": community_id, "leaderboard": rankings}


@router.get("/{community_id}/engagement-hub")
def get_engagement_hub(community_id: int, db: Session = Depends(get_db)):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    games = db.query(CommunityGame).filter(
        CommunityGame.community_id == community_id,
        CommunityGame.is_active.is_(True),
    ).order_by(CommunityGame.created_at.desc()).all()

    recent_trophies = db.query(CommunityTrophy).filter(
        CommunityTrophy.community_id == community_id
    ).order_by(CommunityTrophy.awarded_at.desc()).limit(8).all()

    return {
        "community": {
            "id": community.id,
            "name": community.name,
            "is_linked": community.is_linked,
        },
        "games": [
            {
                "id": int(game.id),
                "title": str(game.title),
                "game_type": str(game.game_type),
                "description": game.description,
                "is_active": bool(game.is_active),
            }
            for game in games
        ],
        "recent_trophies": [_serialize_trophy(trophy) for trophy in recent_trophies],
        "daily_challenges": [
            "Answer 10 questions with 80%+ accuracy",
            "Help a peer in your community discussion",
            "Complete one community course module",
        ],
    }


@router.post("/{community_id}/trophies")
def award_community_trophy(community_id: int, payload: CommunityTrophyCreate, db: Session = Depends(get_db)):
    awarding_user = _get_user_or_404(db, payload.awarded_by_user_id)
    recipient = _get_user_or_404(db, payload.user_id)

    if awarding_user.role not in PRIVILEGED_COMMUNITY_CREATORS and not _is_community_leader(db, community_id, awarding_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only leaders or privileged roles can award trophies")

    trophy = CommunityTrophy(
        community_id=community_id,
        user_id=recipient.id,
        title=payload.title,
        description=payload.description,
        milestone_type=payload.milestone_type,
    )
    db.add(trophy)
    db.commit()
    db.refresh(trophy)

    return _serialize_trophy(trophy)
