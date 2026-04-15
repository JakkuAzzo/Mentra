from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    learning_style = Column(String, default="adaptive")  # adaptive, visual, kinesthetic, auditory
    role = Column(String, default="student", index=True)  # student, teacher, manager, admin, analyst
    access_level = Column(Integer, default=1)  # 1=student, 2=teacher/analyst, 3=manager, 4=admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPath", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    answers = relationship("UserAnswer", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    communities_created = relationship("Community", back_populates="creator", cascade="all, delete-orphan")
    community_memberships = relationship("CommunityMembership", back_populates="user", cascade="all, delete-orphan")
    community_trophies = relationship("CommunityTrophy", back_populates="recipient", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    level = Column(String)  # GCSE, A-Level, Undergraduate
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    difficulty_level = Column(Integer, default=1)  # 1-5
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    subject = relationship("Subject", back_populates="topics")
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="topic", cascade="all, delete-orphan")
    community_courses = relationship("CommunityCourse", back_populates="topic", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    question_text = Column(Text)
    question_type = Column(String)  # multiple_choice, short_answer, essay
    difficulty = Column(Integer, default=1)  # 1-5
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    topic = relationship("Topic", back_populates="questions")
    answers = relationship("UserAnswer", back_populates="question", cascade="all, delete-orphan")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")

class QuestionOption(Base):
    __tablename__ = "question_options"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    option_text = Column(Text)
    is_correct = Column(Boolean, default=False)
    order = Column(Integer)
    
    # Relationships
    question = relationship("Question", back_populates="options")

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    accuracy_score = Column(Float, default=0.0)  # 0-100
    last_attempted = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Composite unique constraint
    __table_args__ = (UniqueConstraint('user_id', 'topic_id', name='uq_user_topic'),)
    
    # Relationships
    user = relationship("User", back_populates="progress")
    topic = relationship("Topic", back_populates="progress")

class UserAnswer(Base):
    __tablename__ = "user_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text)
    is_correct = Column(Boolean)
    time_spent_seconds = Column(Integer)  # seconds
    confidence_level = Column(Float, default=0.5)  # 0.0 to 1.0
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class LearningPath(Base):
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")  # active, completed, paused
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="learning_paths")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True)
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    display_name = Column(String, nullable=True)
    avatar_style = Column(String, default="scholar")
    profile_image_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    institution = Column(String, nullable=True)
    workplace = Column(String, nullable=True)
    cv_headline = Column(String, nullable=True)
    cv_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, default="group")  # school, university, college, workplace, group
    community_type = Column(String, default="study")  # study, workplace, hobby, bootcamp
    organization_name = Column(String, nullable=True)
    is_linked = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    creator = relationship("User", back_populates="communities_created")
    memberships = relationship("CommunityMembership", back_populates="community", cascade="all, delete-orphan")
    courses = relationship("CommunityCourse", back_populates="community", cascade="all, delete-orphan")
    games = relationship("CommunityGame", back_populates="community", cascade="all, delete-orphan")
    trophies = relationship("CommunityTrophy", back_populates="community", cascade="all, delete-orphan")


class CommunityMembership(Base):
    __tablename__ = "community_memberships"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")  # leader, moderator, member
    joined_at = Column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("community_id", "user_id", name="uq_community_user"),)

    community = relationship("Community", back_populates="memberships")
    user = relationship("User", back_populates="community_memberships")


class CommunityCourse(Base):
    __tablename__ = "community_courses"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    milestone_points = Column(Integer, default=100)
    created_at = Column(DateTime, default=func.now())

    community = relationship("Community", back_populates="courses")
    topic = relationship("Topic", back_populates="community_courses")


class CommunityGame(Base):
    __tablename__ = "community_games"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    title = Column(String, nullable=False)
    game_type = Column(String, default="kahoot")  # kahoot, quiz_duel, streak_sprint
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    community = relationship("Community", back_populates="games")


class CommunityTrophy(Base):
    __tablename__ = "community_trophies"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    milestone_type = Column(String, default="achievement")  # achievement, course_completion, streak
    awarded_at = Column(DateTime, default=func.now())

    community = relationship("Community", back_populates="trophies")
    recipient = relationship("User", back_populates="community_trophies")


class CommunityTournament(Base):
    __tablename__ = "community_tournaments"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    title = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String, default="upcoming")  # upcoming, active, completed
    prize_pool = Column(String, nullable=True)  # e.g., "trophies, badges, leaderboard placement"
    created_at = Column(DateTime, default=func.now())

    community = relationship("Community")
    bracket_entries = relationship("TournamentBracket", back_populates="tournament", cascade="all, delete-orphan")


class TournamentBracket(Base):
    __tablename__ = "tournament_brackets"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("community_tournaments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rank = Column(Integer, nullable=True)  # final rank when tournament ends
    score_snapshot = Column(Integer, default=0)  # score at tournament end
    tier = Column(String, default="bronze")  # bronze, silver, gold, platinum
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("tournament_id", "user_id", name="uq_tournament_user"),)

    tournament = relationship("CommunityTournament", back_populates="bracket_entries")
    user = relationship("User")


class UserStreak(Base):
    __tablename__ = "user_streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=True)
    current_streak = Column(Integer, default=0)  # days
    longest_streak = Column(Integer, default=0)  # historical record
    last_activity_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "community_id", name="uq_user_community_streak"),)

    user = relationship("User")
    community = relationship("Community")


class BadgeTier(Base):
    __tablename__ = "badge_tiers"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tier = Column(String, nullable=False)  # bronze, silver, gold, platinum
    score_threshold = Column(Integer, nullable=False)  # score required for this tier
    awarded_date = Column(DateTime, default=func.now())
    badge_description = Column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("community_id", "user_id", "tier", name="uq_community_user_tier"),)

    community = relationship("Community")
    user = relationship("User")


class ExperimentEvent(Base):
    __tablename__ = "experiment_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String, nullable=True, index=True)
    event_name = Column(String, nullable=False, index=True)
    event_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    user = relationship("User")
