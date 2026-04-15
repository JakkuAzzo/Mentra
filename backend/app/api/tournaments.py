# pyright: reportGeneralTypeIssues=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportAssignmentType=false
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models import (
    Community, CommunityMembership, CommunityTournament, TournamentBracket,
    UserStreak, BadgeTier, UserProgress, CommunityTrophy, CommunityCourse, User
)

router = APIRouter(prefix="/api", tags=["tournaments"])

# Badge tier thresholds
TIER_THRESHOLDS = {
    "bronze": 0,
    "silver": 1000,
    "gold": 2500,
    "platinum": 5000,
}


def _calculate_member_score(db: Session, user_id: int, community_id: int) -> int:
    """Calculate leaderboard score for a user in a community."""
    # Score = correct_answers * 10 + courses_completed * 40 + trophies * 25 + accuracy * 2
    
    progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    correct = sum(p.questions_correct for p in progress)
    accuracy = sum(p.accuracy_score for p in progress) / len(progress) if progress else 0
    
    trophies = db.query(CommunityTrophy).filter(
        CommunityTrophy.user_id == user_id,
        CommunityTrophy.community_id == community_id
    ).count()
    
    courses = db.query(CommunityCourse).filter(CommunityCourse.community_id == community_id).all()
    topic_map = {p.topic_id: p.accuracy_score for p in progress}
    courses_completed = sum(1 for c in courses if c.topic_id and topic_map.get(c.topic_id, 0) >= 80)
    
    score = int(correct * 10 + courses_completed * 40 + trophies * 25 + accuracy * 2)
    return score


def _get_tier_for_score(score: int) -> str:
    """Determine tier based on score."""
    if score >= TIER_THRESHOLDS["platinum"]:
        return "platinum"
    elif score >= TIER_THRESHOLDS["gold"]:
        return "gold"
    elif score >= TIER_THRESHOLDS["silver"]:
        return "silver"
    else:
        return "bronze"


def _update_streak(db: Session, user_id: int, community_id: int = None) -> dict:
    """Update user's daily streak. Returns streak info."""
    now = datetime.now()
    today = now.date()
    
    streak = db.query(UserStreak).filter(
        UserStreak.user_id == user_id,
        UserStreak.community_id == community_id
    ).first()
    
    if not streak:
        streak = UserStreak(user_id=user_id, community_id=community_id, current_streak=1, longest_streak=1)
        db.add(streak)
    else:
        last_activity = streak.last_activity_date.date() if streak.last_activity_date else None
        yesterday = today - timedelta(days=1)
        
        if last_activity == today:
            # Already logged in today
            pass
        elif last_activity == yesterday:
            # Extend streak
            streak.current_streak += 1
            streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        else:
            # Streak broken, restart
            streak.current_streak = 1
    
    streak.last_activity_date = now
    db.commit()
    db.refresh(streak)
    
    return {
        "current_streak": int(streak.current_streak),
        "longest_streak": int(streak.longest_streak),
    }


@router.get("/communities/{community_id}/tournaments")
def list_tournaments(community_id: int, db: Session = Depends(get_db)):
    """List all tournaments for a community."""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    tournaments = db.query(CommunityTournament).filter(
        CommunityTournament.community_id == community_id
    ).order_by(CommunityTournament.start_date.desc()).all()
    
    return {
        "community_id": int(community.id),
        "tournaments": [
            {
                "id": int(t.id),
                "title": str(t.title),
                "status": str(t.status),
                "start_date": t.start_date.isoformat(),
                "end_date": t.end_date.isoformat(),
                "prize_pool": t.prize_pool,
            }
            for t in tournaments
        ]
    }


@router.post("/communities/{community_id}/tournaments")
def create_tournament(community_id: int, payload: dict, db: Session = Depends(get_db)):
    """Create a new weekly tournament."""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    # Validate title
    if not payload.get("title"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
    
    # Default: 7-day tournament starting now
    now = datetime.now()
    start = payload.get("start_date") or now.isoformat()
    end = payload.get("end_date") or (now + timedelta(days=7)).isoformat()
    
    tournament = CommunityTournament(
        community_id=community.id,
        title=payload["title"],
        start_date=datetime.fromisoformat(start),
        end_date=datetime.fromisoformat(end),
        status="active",
        prize_pool=payload.get("prize_pool") or "Badges, trophies, leaderboard placement"
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    
    # Add all community members to bracket
    members = db.query(CommunityMembership).filter(
        CommunityMembership.community_id == community_id
    ).all()
    
    for member in members:
        score = _calculate_member_score(db, member.user_id, community_id)
        bracket = TournamentBracket(
            tournament_id=tournament.id,
            user_id=member.user_id,
            score_snapshot=score,
        )
        db.add(bracket)
    db.commit()
    
    return {
        "status": "tournament_created",
        "tournament_id": int(tournament.id),
        "title": str(tournament.title),
        "member_count": len(members),
    }


@router.get("/communities/{community_id}/tournaments/{tournament_id}")
def get_tournament_bracket(community_id: int, tournament_id: int, db: Session = Depends(get_db)):
    """Get tournament bracket with current rankings."""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    tournament = db.query(CommunityTournament).filter(
        CommunityTournament.id == tournament_id,
        CommunityTournament.community_id == community_id
    ).first()
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    
    # Get bracket entries with user info
    entries = db.query(TournamentBracket).filter(
        TournamentBracket.tournament_id == tournament_id
    ).all()
    
    # Recalculate current scores if tournament is active
    if tournament.status == "active":
        for entry in entries:
            current_score = _calculate_member_score(db, entry.user_id, community_id)
            current_tier = _get_tier_for_score(current_score)
            
            # Find user for display
            user = db.query(User).filter(User.id == entry.user_id).first()
            entry_data = {
                "bracket_id": int(entry.id),
                "user_id": int(entry.user_id),
                "username": str(user.username) if user else "Unknown",
                "current_score": current_score,
                "initial_score": int(entry.score_snapshot),
                "tier": str(current_tier),
                "rank": None,  # Will be calculated below
            }
    
    # Sort by score and assign ranks
    bracket_list = []
    for i, entry in enumerate(entries, 1):
        user = db.query(User).filter(User.id == entry.user_id).first()
        
        if tournament.status == "active":
            current_score = _calculate_member_score(db, entry.user_id, community_id)
            tier = _get_tier_for_score(current_score)
        else:
            current_score = int(entry.score_snapshot)
            tier = str(entry.tier)
        
        bracket_list.append({
            "rank": i,
            "user_id": int(entry.user_id),
            "username": str(user.username) if user else "Unknown",
            "score": current_score,
            "tier": tier,
        })
    
    # Sort by score descending
    bracket_list.sort(key=lambda x: x["score"], reverse=True)
    for i, entry in enumerate(bracket_list, 1):
        entry["rank"] = i
    
    return {
        "tournament_id": int(tournament.id),
        "title": str(tournament.title),
        "status": str(tournament.status),
        "start_date": tournament.start_date.isoformat(),
        "end_date": tournament.end_date.isoformat(),
        "bracket": bracket_list,
    }


@router.put("/communities/{community_id}/tournaments/{tournament_id}/finish")
def finish_tournament(community_id: int, tournament_id: int, db: Session = Depends(get_db)):
    """Finalize tournament: rank all players, assign tiers, award trophies."""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    tournament = db.query(CommunityTournament).filter(
        CommunityTournament.id == tournament_id,
        CommunityTournament.community_id == community_id
    ).first()
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    
    # Get all bracket entries
    entries = db.query(TournamentBracket).filter(
        TournamentBracket.tournament_id == tournament_id
    ).all()
    
    # Calculate final scores and ranks
    entry_scores = []
    for entry in entries:
        final_score = _calculate_member_score(db, entry.user_id, community_id)
        tier = _get_tier_for_score(final_score)
        entry_scores.append({
            "entry": entry,
            "score": final_score,
            "tier": tier,
        })
    
    # Sort by score descending
    entry_scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Update bracket entries with final rank and tier
    for rank, item in enumerate(entry_scores, 1):
        entry = item["entry"]
        entry.rank = rank
        entry.score_snapshot = item["score"]
        entry.tier = item["tier"]
        
        # Award trophy to top 3
        if rank <= 3:
            trophy_title = f"Tournament {tournament.title} - Rank #{rank}"
            trophy = CommunityTrophy(
                community_id=community_id,
                user_id=entry.user_id,
                title=trophy_title,
                description=f"Finished rank {rank} in {tournament.title}",
                milestone_type="achievement"
            )
            db.add(trophy)
        
        # Create/update badge tier
        existing_tier = db.query(BadgeTier).filter(
            BadgeTier.community_id == community_id,
            BadgeTier.user_id == entry.user_id,
            BadgeTier.tier == item["tier"]
        ).first()
        
        if not existing_tier:
            badge = BadgeTier(
                community_id=community_id,
                user_id=entry.user_id,
                tier=item["tier"],
                score_threshold=item["score"],
                badge_description=f"Achieved {item['tier'].upper()} tier with {item['score']} points"
            )
            db.add(badge)
    
    # Mark tournament as completed
    tournament.status = "completed"
    db.commit()
    
    return {
        "status": "tournament_finished",
        "tournament_id": int(tournament.id),
        "final_standings": [
            {
                "rank": item["entry"].rank,
                "user_id": int(item["entry"].user_id),
                "score": item["score"],
                "tier": item["tier"],
            }
            for item in entry_scores
        ]
    }


@router.post("/communities/{community_id}/streak")
def update_user_streak(community_id: int, user_id: int, db: Session = Depends(get_db)):
    """Log user activity and update streak."""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    streak_info = _update_streak(db, user_id, community_id)
    return {
        "user_id": int(user_id),
        "community_id": int(community_id),
        **streak_info,
    }


@router.get("/communities/{community_id}/streaks")
def get_community_streaks(community_id: int, db: Session = Depends(get_db)):
    """Get top streaks for a community."""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    streaks = db.query(UserStreak).filter(
        UserStreak.community_id == community_id,
        UserStreak.current_streak > 0
    ).order_by(UserStreak.current_streak.desc()).limit(10).all()
    
    return {
        "community_id": int(community_id),
        "top_streaks": [
            {
                "user_id": int(s.user_id),
                "current_streak": int(s.current_streak),
                "longest_streak": int(s.longest_streak),
                "last_activity": s.last_activity_date.isoformat() if s.last_activity_date else None,
            }
            for s in streaks
        ]
    }


@router.get("/profile/{user_id}/badges")
def get_user_badges(user_id: int, db: Session = Depends(get_db)):
    """Get all badges earned by user across communities."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    badges = db.query(BadgeTier).filter(BadgeTier.user_id == user_id).all()
    
    return {
        "user_id": int(user_id),
        "badges": [
            {
                "community_id": int(b.community_id),
                "tier": str(b.tier),
                "score_threshold": int(b.score_threshold),
                "awarded_date": b.awarded_date.isoformat(),
                "description": b.badge_description,
            }
            for b in badges
        ]
    }
