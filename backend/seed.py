"""
Database seed script for populating sample data.
Useful for development and testing.
"""

# pyright: reportGeneralTypeIssues=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportAssignmentType=false

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import SessionLocal, engine, Base
from app.models import (
    Subject, Topic, Question, QuestionOption, User, UserProgress, UserAnswer, UserSession, LearningPath,
    UserProfile, Community, CommunityMembership, CommunityCourse, CommunityGame, CommunityTrophy
)
from app.core.security import hash_password


ROLE_ACCESS_LEVEL = {
    "student": 1,
    "teacher": 2,
    "analyst": 2,
    "manager": 3,
    "admin": 4,
}

def seed_database():
    """Populate database with sample data"""
    db = SessionLocal()
    
    try:
        # Recreate tables so schema changes are reflected in local demo DB.
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Clear existing data
        db.query(UserSession).delete()
        db.query(CommunityTrophy).delete()
        db.query(CommunityGame).delete()
        db.query(CommunityCourse).delete()
        db.query(CommunityMembership).delete()
        db.query(Community).delete()
        db.query(UserProfile).delete()
        db.query(UserAnswer).delete()
        db.query(UserProgress).delete()
        db.query(LearningPath).delete()
        db.query(QuestionOption).delete()
        db.query(Question).delete()
        db.query(Topic).delete()
        db.query(Subject).delete()
        db.query(User).delete()
        
        # Create multi-role users
        users = [
            User(
                email="student@example.com",
                username="student",
                hashed_password=hash_password("testpass123"),
                full_name="Sam Student",
                learning_style="adaptive",
                role="student",
                access_level=ROLE_ACCESS_LEVEL["student"],
            ),
            User(
                email="caseystudent@example.com",
                username="caseystudent",
                hashed_password=hash_password("password123"),
                full_name="Casey Student",
                learning_style="adaptive",
                role="student",
                access_level=ROLE_ACCESS_LEVEL["student"],
            ),
            User(
                email="teacher@example.com",
                username="teacher",
                hashed_password=hash_password("testpass123"),
                full_name="Tina Teacher",
                learning_style="visual",
                role="teacher",
                access_level=ROLE_ACCESS_LEVEL["teacher"],
            ),
            User(
                email="manager@example.com",
                username="manager",
                hashed_password=hash_password("testpass123"),
                full_name="Manny Manager",
                learning_style="adaptive",
                role="manager",
                access_level=ROLE_ACCESS_LEVEL["manager"],
            ),
            User(
                email="admin@example.com",
                username="admin",
                hashed_password=hash_password("testpass123"),
                full_name="Alice Admin",
                learning_style="adaptive",
                role="admin",
                access_level=ROLE_ACCESS_LEVEL["admin"],
            ),
            User(
                email="analyst@example.com",
                username="analyst",
                hashed_password=hash_password("testpass123"),
                full_name="Andy Analyst",
                learning_style="auditory",
                role="analyst",
                access_level=ROLE_ACCESS_LEVEL["analyst"],
            ),
        ]

        db.add_all(users)
        db.flush()

        db.add_all(
            [
                UserProfile(
                    user_id=users[0].id,
                    display_name="Sam",
                    avatar_style="scholar",
                    bio="A focused learner building consistent mastery across STEM topics.",
                    institution="Kingston University",
                    cv_headline="Student Learner with Data-Driven Progress",
                ),
                UserProfile(
                    user_id=users[1].id,
                    display_name="Casey",
                    avatar_style="explorer",
                    bio="Collaborative learner interested in adaptive communities and achievement tracking.",
                    institution="Kingston University",
                ),
            ]
        )

        student_user = users[0]
        
        # Create subjects
        math_subject = Subject(
            name="Mathematics",
            description="Fundamental mathematics topics",
            level="A-Level"
        )
        chemistry_subject = Subject(
            name="Chemistry",
            description="Chemistry fundamentals",
            level="A-Level"
        )
        db.add_all([math_subject, chemistry_subject])
        db.flush()
        
        # Create topics
        algebra_topic = Topic(
            subject_id=math_subject.id,
            name="Algebra Fundamentals",
            description="Basic algebraic operations and equations",
            difficulty_level=1
        )
        quadratic_topic = Topic(
            subject_id=math_subject.id,
            name="Quadratic Equations",
            description="Solving and analyzing quadratic functions",
            difficulty_level=2
        )
        bonding_topic = Topic(
            subject_id=chemistry_subject.id,
            name="Chemical Bonding",
            description="Ionic, covalent, and metallic bonding",
            difficulty_level=2
        )
        db.add_all([algebra_topic, quadratic_topic, bonding_topic])
        db.flush()
        
        # Create questions for Algebra
        algebra_q1 = Question(
            topic_id=algebra_topic.id,
            question_text="Solve for x: 2x + 5 = 13",
            question_type="multiple_choice",
            difficulty=1
        )
        db.add(algebra_q1)
        db.flush()
        
        # Add options for algebra_q1
        options = [
            QuestionOption(question_id=algebra_q1.id, option_text="x = 2", is_correct=False, order=1),
            QuestionOption(question_id=algebra_q1.id, option_text="x = 4", is_correct=True, order=2),
            QuestionOption(question_id=algebra_q1.id, option_text="x = 6", is_correct=False, order=3),
            QuestionOption(question_id=algebra_q1.id, option_text="x = 18", is_correct=False, order=4),
        ]
        db.add_all(options)
        
        # Create questions for Quadratic Equations
        quad_q1 = Question(
            topic_id=quadratic_topic.id,
            question_text="What is the vertex of y = x² - 4x + 3?",
            question_type="multiple_choice",
            difficulty=2
        )
        db.add(quad_q1)
        db.flush()
        
        options = [
            QuestionOption(question_id=quad_q1.id, option_text="(2, -1)", is_correct=True, order=1),
            QuestionOption(question_id=quad_q1.id, option_text="(1, 0)", is_correct=False, order=2),
            QuestionOption(question_id=quad_q1.id, option_text="(2, 0)", is_correct=False, order=3),
            QuestionOption(question_id=quad_q1.id, option_text="(-2, 11)", is_correct=False, order=4),
        ]
        db.add_all(options)
        
        # Create questions for Chemistry
        chem_q1 = Question(
            topic_id=bonding_topic.id,
            question_text="Which type of bond is between sodium and chlorine in NaCl?",
            question_type="multiple_choice",
            difficulty=2
        )
        db.add(chem_q1)
        db.flush()
        
        options = [
            QuestionOption(question_id=chem_q1.id, option_text="Ionic", is_correct=True, order=1),
            QuestionOption(question_id=chem_q1.id, option_text="Covalent", is_correct=False, order=2),
            QuestionOption(question_id=chem_q1.id, option_text="Metallic", is_correct=False, order=3),
            QuestionOption(question_id=chem_q1.id, option_text="Hydrogen", is_correct=False, order=4),
        ]
        db.add_all(options)

        # Create student progress for recommendation and analytics endpoints
        now = datetime.utcnow()
        progress_records = [
            UserProgress(
                user_id=student_user.id,
                topic_id=algebra_topic.id,
                questions_attempted=12,
                questions_correct=9,
                accuracy_score=75.0,
                last_attempted=now - timedelta(days=40),
            ),
            UserProgress(
                user_id=student_user.id,
                topic_id=quadratic_topic.id,
                questions_attempted=10,
                questions_correct=6,
                accuracy_score=60.0,
                last_attempted=now - timedelta(days=25),
            ),
            UserProgress(
                user_id=student_user.id,
                topic_id=bonding_topic.id,
                questions_attempted=8,
                questions_correct=5,
                accuracy_score=62.5,
                last_attempted=now - timedelta(days=20),
            ),
        ]
        db.add_all(progress_records)

        # Create answer history for mastery and due-for-review calculations
        answers = [
            UserAnswer(
                user_id=student_user.id,
                question_id=algebra_q1.id,
                answer_text="x = 4",
                is_correct=True,
                time_spent_seconds=32,
                confidence_level=0.9,
                created_at=now - timedelta(days=6),
            ),
            UserAnswer(
                user_id=student_user.id,
                question_id=algebra_q1.id,
                answer_text="x = 2",
                is_correct=False,
                time_spent_seconds=44,
                confidence_level=0.6,
                created_at=now - timedelta(days=5),
            ),
            UserAnswer(
                user_id=student_user.id,
                question_id=quad_q1.id,
                answer_text="(2, -1)",
                is_correct=True,
                time_spent_seconds=58,
                confidence_level=0.7,
                created_at=now - timedelta(days=10),
            ),
            UserAnswer(
                user_id=student_user.id,
                question_id=quad_q1.id,
                answer_text="(2, 0)",
                is_correct=False,
                time_spent_seconds=62,
                confidence_level=0.5,
                created_at=now - timedelta(days=8),
            ),
            UserAnswer(
                user_id=student_user.id,
                question_id=chem_q1.id,
                answer_text="Ionic",
                is_correct=True,
                time_spent_seconds=40,
                confidence_level=0.8,
                created_at=now - timedelta(days=16),
            ),
            UserAnswer(
                user_id=student_user.id,
                question_id=chem_q1.id,
                answer_text="Covalent",
                is_correct=False,
                time_spent_seconds=35,
                confidence_level=0.4,
                created_at=now - timedelta(days=13),
            ),
        ]
        db.add_all(answers)

        # Create session history for analytics endpoint
        sessions = [
            UserSession(
                user_id=student_user.id,
                session_token="sess-001",
                started_at=now - timedelta(days=1, hours=2),
                ended_at=now - timedelta(days=1, hours=1, minutes=20),
                duration_minutes=40,
            ),
            UserSession(
                user_id=student_user.id,
                session_token="sess-002",
                started_at=now - timedelta(days=2, hours=3),
                ended_at=now - timedelta(days=2, hours=2, minutes=10),
                duration_minutes=50,
            ),
            UserSession(
                user_id=student_user.id,
                session_token="sess-003",
                started_at=now - timedelta(days=3, hours=1),
                ended_at=now - timedelta(days=3, minutes=5),
                duration_minutes=55,
            ),
            UserSession(
                user_id=student_user.id,
                session_token="sess-004",
                started_at=now - timedelta(days=5, hours=4),
                ended_at=now - timedelta(days=5, hours=3, minutes=20),
                duration_minutes=40,
            ),
            UserSession(
                user_id=student_user.id,
                session_token="sess-005",
                started_at=now - timedelta(days=6, hours=2),
                ended_at=now - timedelta(days=6, hours=1, minutes=30),
                duration_minutes=30,
            ),
        ]
        db.add_all(sessions)

        # Community seed data for communities tab
        linked_community = Community(
            name="Kingston STEM Scholars",
            description="Official linked university community for collaborative STEM preparation.",
            category="university",
            community_type="study",
            organization_name="Kingston University",
            is_linked=True,
            created_by=users[2].id,
        )
        student_community = Community(
            name="Evening Revision Group",
            description="Open student-led practice group for daily revision and leaderboard sprints.",
            category="group",
            community_type="study",
            organization_name="Mentra",
            is_linked=False,
            created_by=users[1].id,
        )
        db.add_all([linked_community, student_community])
        db.flush()

        db.add_all(
            [
                CommunityMembership(community_id=linked_community.id, user_id=users[2].id, role="leader"),
                CommunityMembership(community_id=linked_community.id, user_id=users[0].id, role="member"),
                CommunityMembership(community_id=linked_community.id, user_id=users[1].id, role="member"),
                CommunityMembership(community_id=student_community.id, user_id=users[1].id, role="leader"),
                CommunityMembership(community_id=student_community.id, user_id=users[0].id, role="member"),
            ]
        )

        db.add_all(
            [
                CommunityCourse(
                    community_id=linked_community.id,
                    topic_id=algebra_topic.id,
                    title="Algebra Mastery Track",
                    description="Structured weekly checkpoints focused on equation fluency.",
                    milestone_points=120,
                ),
                CommunityCourse(
                    community_id=linked_community.id,
                    topic_id=quadratic_topic.id,
                    title="Quadratic Deep Dive",
                    description="Curve interpretation and vertex optimization sessions.",
                    milestone_points=150,
                ),
                CommunityCourse(
                    community_id=student_community.id,
                    topic_id=bonding_topic.id,
                    title="Chemistry Flash Review",
                    description="Short practice bursts with leaderboard updates.",
                    milestone_points=100,
                ),
            ]
        )

        db.add_all(
            [
                CommunityGame(
                    community_id=linked_community.id,
                    title="Kahoot Challenge Arena",
                    game_type="kahoot",
                    description="Weekly timed quiz rounds with instant ranking updates.",
                    is_active=True,
                ),
                CommunityGame(
                    community_id=linked_community.id,
                    title="Streak Sprint",
                    game_type="streak_sprint",
                    description="Build daily streaks to unlock milestone trophies.",
                    is_active=True,
                ),
            ]
        )

        db.add_all(
            [
                CommunityTrophy(
                    community_id=linked_community.id,
                    user_id=users[0].id,
                    title="Algebra Consistency Award",
                    description="Maintained 7-day momentum in algebra practice.",
                    milestone_type="streak",
                ),
                CommunityTrophy(
                    community_id=linked_community.id,
                    user_id=users[1].id,
                    title="Community Collaboration Trophy",
                    description="Supported peers with high-quality answers and review notes.",
                    milestone_type="achievement",
                ),
            ]
        )
        
        # Create tournaments
        from app.models import CommunityTournament, TournamentBracket, UserStreak, BadgeTier
        
        tournament1 = CommunityTournament(
            community_id=linked_community.id,
            title="Weekly Challenge - Week 1",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now() - timedelta(days=1),
            status="completed",
            prize_pool="Badges, trophies, leaderboard placement"
        )
        db.add(tournament1)
        db.flush()
        
        # Add bracket entries for tournament
        teacher_user_id = int(users[2].id)
        student_user_id = int(users[0].id)
        casey_user_id = int(users[1].id)

        for user in [users[0], users[1], users[2]]:
            current_user_id = int(user.id)
            bracket = TournamentBracket(
                tournament_id=tournament1.id,
                user_id=current_user_id,
                score_snapshot=1500 if current_user_id == teacher_user_id else 1200,
                tier="silver" if current_user_id == teacher_user_id else "bronze",
                rank=3 if current_user_id == teacher_user_id else (1 if current_user_id == student_user_id else 2)
            )
            db.add(bracket)
        
        # Active tournament
        tournament2 = CommunityTournament(
            community_id=linked_community.id,
            title="Weekly Challenge - Week 2",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            status="active",
            prize_pool="Badges, trophies, leaderboard placement"
        )
        db.add(tournament2)
        db.flush()
        
        for user in [users[0], users[1], users[2]]:
            bracket = TournamentBracket(
                tournament_id=tournament2.id,
                user_id=int(user.id),
                score_snapshot=0,
                tier="bronze",
                rank=None
            )
            db.add(bracket)
        
        # Create user streaks
        for user in [users[0], users[1], users[2]]:
            current_user_id = int(user.id)
            streak = UserStreak(
                user_id=current_user_id,
                community_id=linked_community.id,
                current_streak=7 if current_user_id == student_user_id else (5 if current_user_id == casey_user_id else 3),
                longest_streak=14 if current_user_id == student_user_id else (10 if current_user_id == casey_user_id else 5),
                last_activity_date=datetime.now()
            )
            db.add(streak)
        
        # Create badge tiers
        badge_tiers = [
            BadgeTier(
                community_id=linked_community.id,
                user_id=users[2].id,
                tier="silver",
                score_threshold=1500,
                badge_description="Reached Silver tier with consistent practice"
            ),
            BadgeTier(
                community_id=linked_community.id,
                user_id=users[1].id,
                tier="bronze",
                score_threshold=1000,
                badge_description="Reached Bronze tier - Great start!"
            ),
        ]
        db.add_all(badge_tiers)
        
        db.commit()
        print("✅ Database seeded successfully!")
        print(f"   - Created {len([math_subject, chemistry_subject])} subjects")
        print(f"   - Created {len([algebra_topic, quadratic_topic, bonding_topic])} topics")
        print("   - Created users:")
        print("     • student / student@example.com (student, level 1, password: testpass123)")
        print("     • caseystudent / caseystudent@example.com (student, level 1, password: password123)")
        print("     • teacher / teacher@example.com (teacher, level 2, password: testpass123)")
        print("     • analyst / analyst@example.com (analyst, level 2, password: testpass123)")
        print("     • manager / manager@example.com (manager, level 3, password: testpass123)")
        print("     • admin / admin@example.com (admin, level 4, password: testpass123)")
        print("   - Created 2 communities with courses, games, and milestone trophies")
        print("   - Created 2 tournaments (1 completed, 1 active)")
        print("   - Created user streaks and badge tiers")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
