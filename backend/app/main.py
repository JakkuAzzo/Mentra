from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine, Base
from app.models import models
from app.api import auth, questions, progress, recommendations

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    yield
    # Shutdown
    print("❌ Application shutting down")

app = FastAPI(
    title="Mentra - AI-Driven Personal Tutor",
    description="API for personalized adaptive learning",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Mentra API",
        "version": "1.0.0"
    }

# Include routers
app.include_router(auth.router)
app.include_router(questions.router)
app.include_router(progress.router)
app.include_router(recommendations.router)

@app.get("/", tags=["root"])
def read_root():
    return {
        "message": "Welcome to Mentra - AI-Driven Personal Tutor API",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "authentication": "/api/auth",
            "questions": "/api/questions",
            "progress": "/api/progress",
            "recommendations": "/api/recommendations"
        }
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return {
        "error": "Internal server error",
        "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
    }
