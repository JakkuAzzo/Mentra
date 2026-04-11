# Architecture Documentation

## System Overview

Mentra is an AI-driven personal tutoring system designed to provide personalized, adaptive learning experiences. The system monitors learner performance, adapts question difficulty, and provides intelligent feedback.

## Architecture Layers

### Frontend (React + TypeScript)
- **UI Layer**: Interactive learning interface with real-time feedback
- **State Management**: Zustand for user auth & learning state
- **API Client**: Axios with interceptors for API calls
- **Components**: Reusable, modular React components

Key files:
- `App.tsx` - Main routing and authentication wrapper
- `pages/` - Page components (Login, Dashboard, Learning, Progress)
- `components/` - Reusable UI components
- `stores/` - Zustand state management
- `utils/api.ts` - API client configuration

### Backend (FastAPI + Python)
- **API Layer**: RESTful endpoints for frontend consumption
- **Service Layer**: Business logic for learning, progress, recommendations
- **Data Layer**: SQLAlchemy ORM models
- **Security**: JWT authentication, password hashing

Directory structure:
```
app/
├── main.py           # FastAPI application setup
├── api/              # Route handlers
│   ├── auth.py       # Authentication endpoints
│   ├── questions.py  # Question and answer endpoints
│   ├── progress.py   # Progress tracking
│   └── recommendations.py
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic validation schemas
├── services/         # Business logic
│   ├── auth_service.py
│   ├── question_service.py
│   ├── feedback_service.py
│   ├── progress_service.py
│   └── recommendation_service.py
└── core/             # Configuration & utilities
    ├── config.py
    ├── database.py
    └── security.py
```

### Database Schema

#### Users Table
- Stores user profiles and preferences
- Links to all learning activity

#### Subject & Topic Tables
- Hierarchical organization of curriculum
- Difficulty levels for adaptive learning

#### Questions Table
- Learning content
- Linked to topics
- Multiple choice options

#### UserProgress Table
- Tracks accuracy and attempt counts
- Enables weak topic identification

#### UserAnswer Table
- Historical record of all answers
- Enables performance analysis

#### LearningPath Table
- Personalized study plans per user
- Status tracking (active, completed)

## Data Flow

### Learning Session Flow
```
1. User logs in
   ↓
2. Dashboard loads → Fetch personalized learning path
   ↓
3. User selects topic → Get adaptive question
   ↓
4. User submits answer
   ↓
5. Backend evaluates → Generate feedback → Update progress
   ↓
6. Display feedback with explanations
   ↓
7. Recommend next topic
```

### Adaptive Difficulty Algorithm
```
Get user's recent performance on topic
   ↓
If accuracy > 80%: Increase difficulty
If accuracy < 50%: Decrease difficulty
Otherwise: Maintain current difficulty
   ↓
Fetch question at adjusted difficulty
   ↓
Present to user
```

### Recommendation Algorithm
```
Get all topics for user
   ↓
Score each topic by:
  - Performance (80% weight)
  - Last attempted date (20% weight)
  - Prerequisite status
   ↓
Sort by priority score
   ↓
Return prioritized learning path
```

## Key Features Implementation

### FR1: Personalized Learning Guidance
- **Implementation**: RecommendationService generates topic priorities based on performance
- **Data**: UserProgress tracks accuracy per topic
- **Endpoint**: `GET /api/recommendations/learning-path/{user_id}`

### FR2: Step-by-Step Explanations
- **Implementation**: FeedbackService AI generates explanations (placeholder for LLM integration)
- **Data**: Stored with UserAnswer
- **Endpoint**: `POST /api/questions/submit-answer`

### FR3: Adaptive Recommendations
- **Implementation**: QuestionService adjusts difficulty; RecommendationService prioritizes topics
- **Algorithm**: Spaced repetition + performance-based sorting
- **Endpoint**: Multiple endpoints combining algo results

### FR4: Content Breakdown
- **Implementation**: Topics organize content; Questions break into manageable chunks
- **Data**: Hierarchical Topic → Question structure
- **Endpoint**: Content served progressively

### FR5: 24/7 Expert Support
- **Implementation**: FastAPI always running; AI feedback generation can be instant
- **Scalability**: Stateless design allows horizontal scaling
- **Endpoint**: All endpoints available 24/7

### FR6: Progress Tracking
- **Implementation**: UserProgress + UserAnswer tables
- **Visualization**: Dashboard shows accuracy, mastered topics, weak areas
- **Endpoint**: `GET /api/progress/summary/{user_id}`

## Security Measures

1. **Authentication**: JWT tokens with 30-minute expiration
2. **Password Security**: Bcrypt hashing with salt
3. **CORS**: Whitelist allowed origins
4. **Input Validation**: Pydantic schemas validate all input
5. **Database**: Parametrized queries prevent SQL injection

## Scalability Considerations

1. **Stateless Services**: All services are stateless for horizontal scaling
2. **Database Connection Pooling**: SQLAlchemy handles connection management
3. **Caching**: Redis integration (configured but not yet implemented)
4. **CDN**: Frontend static assets can be served from CDN
5. **API Rate Limiting**: Can be added using middleware

## Performance Optimizations

1. **Query Optimization**: Database indexes on frequently queried fields
2. **Lazy Loading**: Related objects loaded on demand
3. **Pagination**: Available for large result sets
4. **Caching**: Redis for session management and hot data
5. **Async**: FastAPI supports async I/O for concurrent requests

## Deployment Pipeline

1. **Development**: Local environment with hot-reload
2. **Staging**: Docker containers with test data
3. **Production**: Kubernetes deployment with monitoring

## Environment

- **Frontend**: Node.js 18+, React 18, Vite
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL 14+
- **Cache**: Redis 7+
- **Container**: Docker & Docker Compose

## Future Enhancements

1. **Real AI Integration**: OpenAI GPT for intelligent feedback
2. **Video Content**: Embed educational videos
3. **Gamification**: Achievements, badges, leaderboards
4. **Social Features**: Study groups, peer feedback
5. **Mobile App**: React Native companion
6. **Spaced Repetition**: Advanced SRS algorithm
7. **Analytics Dashboard**: Instructor view
8. **Real-time Collaboration**: WebSocket support
9. **Accessibility**: WCAG compliance improvements
10. **Internationalization**: Multi-language support
