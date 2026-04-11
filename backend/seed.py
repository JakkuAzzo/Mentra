"""
Database seed script for populating sample data.
Useful for development and testing.
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models import (
    Subject, Topic, Question, QuestionOption, User
)
from app.core.security import hash_password

def seed_database():
    """Populate database with sample data"""
    db = SessionLocal()
    
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Clear existing data
        db.query(QuestionOption).delete()
        db.query(Question).delete()
        db.query(Topic).delete()
        db.query(Subject).delete()
        db.query(User).delete()
        
        # Create sample user
        sample_user = User(
            email="student@example.com",
            username="student",
            hashed_password=hash_password("testpass123"),
            full_name="Sam Student",
            learning_style="adaptive"
        )
        db.add(sample_user)
        db.flush()
        
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
        
        db.commit()
        print("✅ Database seeded successfully!")
        print(f"   - Created {len([math_subject, chemistry_subject])} subjects")
        print(f"   - Created {len([algebra_topic, quadratic_topic, bonding_topic])} topics")
        print(f"   - Created sample user: student@example.com / testpass123")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
