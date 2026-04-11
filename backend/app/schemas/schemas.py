from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: str = "student"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    learning_style: str
    role: str
    access_level: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

# Topic/Subject Schemas
class TopicCreate(BaseModel):
    name: str
    description: Optional[str] = None
    difficulty_level: int = 1

class TopicResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    difficulty_level: int
    
    class Config:
        from_attributes = True

class SubjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    level: str

class SubjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    level: str
    topics: List[TopicResponse] = []
    
    class Config:
        from_attributes = True

# Question Schemas
class QuestionOptionCreate(BaseModel):
    option_text: str
    is_correct: bool
    order: int

class QuestionOptionResponse(BaseModel):
    id: int
    option_text: str
    is_correct: bool
    order: int
    
    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    topic_id: int
    question_text: str
    question_type: str = "multiple_choice"
    difficulty: int = 1
    options: List[QuestionOptionCreate] = []

class QuestionResponse(BaseModel):
    id: int
    topic_id: int
    question_text: str
    question_type: str
    difficulty: int
    options: List[QuestionOptionResponse] = []
    
    class Config:
        from_attributes = True

# Progress Schemas
class UserProgressResponse(BaseModel):
    id: int
    user_id: int
    topic_id: int
    questions_attempted: int
    questions_correct: int
    accuracy_score: float
    last_attempted: Optional[datetime]
    
    class Config:
        from_attributes = True

# Answer Schemas
class UserAnswerCreate(BaseModel):
    question_id: int
    answer_text: str
    time_spent_seconds: int = 0

class UserAnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: str
    is_correct: bool
    time_spent_seconds: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Learning Path Schemas
class LearningPathCreate(BaseModel):
    name: str
    description: Optional[str] = None

class LearningPathResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Feedback Schemas
class FeedbackRequest(BaseModel):
    question_id: int
    user_answer: str
    time_spent: int = 0
    confidence_level: float = 0.5  # User's confidence in their answer (0.0-1.0)

class FeedbackResponse(BaseModel):
    is_correct: bool
    explanation: str
    key_concepts: List[str] = []
    next_topic_recommendation: Optional[str] = None
    confidence_score: float = 0.0
    effort_level: str = "medium"  # easy, medium, hard
