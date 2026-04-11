"""
Pytest configuration and fixtures for Mentra backend tests.
Provides shared test database, sample users, topics, and questions.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import (
    User, Subject, Topic, Question, QuestionOption, 
    UserProgress, UserAnswer, UserSession
)
from app.core.security import hash_password

# Use in-memory SQLite for tests
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def db_engine():
    """Create a test database engine"""
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    """Create a new database session for each test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_subject(db_session):
    """Create a sample subject"""
    subject = Subject(
        name="Mathematics",
        description="Basic mathematics fundamentals"
    )
    db_session.add(subject)
    db_session.commit()
    return subject

@pytest.fixture
def sample_topics(db_session, sample_subject):
    """Create multiple sample topics"""
    topics = [
        Topic(
            subject_id=sample_subject.id,
            name="Algebra",
            description="Algebraic equations and expressions",
            difficulty_level=2
        ),
        Topic(
            subject_id=sample_subject.id,
            name="Geometry",
            description="Shapes and spatial reasoning",
            difficulty_level=3
        ),
        Topic(
            subject_id=sample_subject.id,
            name="Calculus",
            description="Limits and derivatives",
            difficulty_level=4
        ),
    ]
    db_session.add_all(topics)
    db_session.commit()
    return topics

@pytest.fixture
def sample_questions(db_session, sample_topics):
    """Create sample questions for testing"""
    questions = []
    
    for topic in sample_topics:
        for i in range(5):
            q = Question(
                topic_id=topic.id,
                question_text=f"What is {topic.name} question {i+1}?",
                question_type="multiple_choice",
                difficulty=topic.difficulty_level,
                explanation=f"This is the explanation for {topic.name} question {i+1}"
            )
            db_session.add(q)
            db_session.flush()
            
            # Add options
            for j in range(4):
                option = QuestionOption(
                    question_id=q.id,
                    option_text=f"Option {j+1}",
                    is_correct=(j == 0)  # First option is correct
                )
                db_session.add(option)
            
            questions.append(q)
    
    db_session.commit()
    return questions

@pytest.fixture
def sample_user_progress(db_session, sample_user, sample_topics):
    """Create sample user progress"""
    progress_records = []
    
    for topic in sample_topics:
        progress = UserProgress(
            user_id=sample_user.id,
            topic_id=topic.id,
            questions_attempted=10,
            questions_correct=7,
            accuracy_score=70.0,
            last_attempted=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(progress)
        progress_records.append(progress)
    
    db_session.commit()
    return progress_records

@pytest.fixture
def sample_user_answers(db_session, sample_user, sample_questions):
    """Create sample user answers"""
    answers = []
    
    for i, question in enumerate(sample_questions[:10]):
        answer = UserAnswer(
            user_id=sample_user.id,
            question_id=question.id,
            user_answer="1",  # First option
            is_correct=(i % 3 != 0),  # 2/3 correct rate
            time_spent=30 + (i * 10),
            confidence_level=0.7,
            created_at=datetime.utcnow() - timedelta(hours=i)
        )
        db_session.add(answer)
        answers.append(answer)
    
    db_session.commit()
    return answers

@pytest.fixture
def sample_user_sessions(db_session, sample_user):
    """Create sample user sessions"""
    sessions = []
    
    for i in range(7):
        session = UserSession(
            user_id=sample_user.id,
            started_at=datetime.utcnow() - timedelta(days=i),
            ended_at=datetime.utcnow() - timedelta(days=i, hours=-1),
            duration_minutes=60
        )
        db_session.add(session)
        sessions.append(session)
    
    db_session.commit()
    return sessions
