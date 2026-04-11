from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models import User
from app.schemas.schemas import UserCreate, UserLogin
from app.core.security import hash_password, verify_password, create_token, verify_token
from app.core.config import settings


ROLE_ACCESS_LEVEL = {
    "student": 1,
    "teacher": 2,
    "analyst": 2,
    "manager": 3,
    "admin": 4,
}

class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user already exists
        user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if user:
            raise ValueError("User already exists")
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        role = (user_data.role or "student").lower()
        if role not in ROLE_ACCESS_LEVEL:
            raise ValueError("Invalid role. Allowed: student, teacher, analyst, manager, admin")

        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=role,
            access_level=ROLE_ACCESS_LEVEL[role],
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    @staticmethod
    def login_user(db: Session, email: str, password: str) -> tuple[User, str]:
        """Authenticate user and return user object and token"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        # Create access token
        access_token = create_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return user, access_token
    
    @staticmethod
    def verify_user_token(token: str) -> dict:
        """Verify token and return payload"""
        payload = verify_token(token)
        if not payload:
            raise ValueError("Invalid token")
        return payload
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """Get user by email"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        return user
