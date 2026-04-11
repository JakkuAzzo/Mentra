"""
Database seed script for populating sample data.
Useful for development and testing.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import SessionLocal, engine, Base
from app.models import (
    Subject, Topic, Question, QuestionOption, User, UserProgress, UserAnswer, UserSession, LearningPath
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

        student_user = next(u for u in users if u.role == "student")
        
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
        
        db.commit()
        print("✅ Database seeded successfully!")
        print(f"   - Created {len([math_subject, chemistry_subject])} subjects")
        print(f"   - Created {len([algebra_topic, quadratic_topic, bonding_topic])} topics")
        print("   - Created users (password: testpass123):")
        print("     • student@example.com (student, level 1)")
        print("     • teacher@example.com (teacher, level 2)")
        print("     • analyst@example.com (analyst, level 2)")
        print("     • manager@example.com (manager, level 3)")
        print("     • admin@example.com (admin, level 4)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
