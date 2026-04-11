# Setup & Installation Guide

## Local Development

### Prerequisites
- Node.js 18+ (Frontend)
- Python 3.11+ (Backend)
- PostgreSQL 14+
- Redis (optional, for caching)
- Docker (for Ollama LLM service)

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Configure database and keys in .env:
# - Set DATABASE_URL
# - Set OPENAI_API_KEY (optional)
# - Set JWT_SECRET_KEY to a random string
# - Set LLM_PROVIDER (default: "ollama")
# - Set OLLAMA_BASE_URL (default: "http://localhost:11434")

# Run database migrations (if applicable)
python -m alembic upgrade head  # uncomment when migrations added

# Start development server
uvicorn app.main:app --reload
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### AI/LLM Setup (Ollama)

The application uses Ollama for AI-powered feedback generation. This does NOT require external API keys.

#### Option 1: Local Ollama Installation
```bash
# Install Ollama from https://ollama.ai
# Or use docker:
docker run -d \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama

# Pull the default model (neural-chat)
docker exec ollama ollama pull neural-chat

# Or pull other models:
docker exec ollama ollama pull llama2
docker exec ollama ollama pull mistral
```

#### Option 2: Docker Compose (Recommended)
If using `docker-compose.yml` from project root:
```bash
# Already includes Ollama service
docker-compose up -d

# Wait for Ollama to be ready, then pull model:
docker exec mentra-ollama ollama pull neural-chat
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/generate \
  -d '{"model":"neural-chat","prompt":"What is 2+2?"}'
```

#### Environment Configuration
Update `.env` in backend directory:
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434  # Docker
# OR
OLLAMA_BASE_URL=http://localhost:11434  # Local

OLLAMA_MODEL=neural-chat  # Or: llama2, mistral
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=500

# Feature flags for advanced features
ENABLE_SPACED_REPETITION=true
ENABLE_CONFIDENCE_SCORING=true
ENABLE_PERFORMANCE_PREDICTION=true
ENABLE_SESSION_ANALYTICS=true
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### Docker Setup

```bash
# From project root
docker-compose up -d

# Verify services
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama

# Pull Ollama model (one-time)
docker exec mentra-ollama ollama pull neural-chat

# Stop services
docker-compose down
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Ollama API: http://localhost:11434
- PostgreSQL: localhost:5432
- Redis: localhost:6379


## Project Structure

```
mentra/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── core/             # Config, database, security
│   │   └── main.py           # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Route pages
│   │   ├── stores/          # Zustand state
│   │   ├── utils/           # Helpers, API client
│   │   └── App.tsx          # Main app
│   ├── package.json
│   └── Dockerfile.dev
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user

### Questions (with AI-Powered Feedback)
- `GET /api/questions/{question_id}` - Get specific question
- `GET /api/questions/topic/{topic_id}` - Get topic's questions
- `GET /api/questions/adaptive/{user_id}/{topic_id}` - Get adaptive question
- `POST /api/questions/submit-answer` - Submit answer and get **AI-generated step-by-step feedback**
  - Includes: explanation, next learning suggestion, difficulty level
  - Uses local Ollama LLM (no external API keys needed)

### Progress
- `GET /api/progress/user/{user_id}` - Get all progress records
- `GET /api/progress/summary/{user_id}` - Get summary statistics
- `GET /api/progress/weak-topics/{user_id}` - Get weak areas

### Recommendations (Advanced Features)
#### Basic Recommendations
- `GET /api/recommendations/next-topic/{user_id}` - Get next topic to study
- `GET /api/recommendations/learning-path/{user_id}` - Get full learning path
- `GET /api/recommendations/should-review/{user_id}/{topic_id}` - Check review status

#### Spaced Repetition (FR3)
- `GET /api/recommendations/due-for-review/{user_id}` - Get topics due for review
  - Returns: Priority-sorted list based on Ebbinghaus forgetting curve
  - Intervals: [1, 3, 7, 14, 30, 60, 120] days
  - Response: `{topics: [{topic_id, topic_name, days_overdue, priority_score, current_accuracy}]}`

#### Performance Prediction (FR4)
- `GET /api/recommendations/mastery-date/{user_id}/{topic_id}` - Estimate mastery date
  - Returns: Predicted days to 85% accuracy with confidence level
  - Response: `{estimated_days_to_mastery, estimated_mastery_date, confidence_level}`

#### Session Analytics (FR5)
- `GET /api/recommendations/session-stats/{user_id}?days=7` - Get learning session statistics
  - Returns: Engagement metrics for specified period (default: last 7 days)
  - Includes: streak, consistency score, peak learning hour, total hours
  - Response: `{total_sessions, total_hours_learned, avg_session_length_minutes, peak_learning_hour, current_streak_days, consistency_score}`

#### Personalized Recommendations
- `GET /api/recommendations/personalized/{user_id}?limit=5` - Combined ML-powered recommendations
  - Combines: spaced repetition, performance trends, learning patterns
  - Response: Ranked list of topics with urgency levels

## Advanced Features

### 1. AI-Powered Feedback (LLM Integration)
- **Model**: Ollama + Neural-Chat (runs locally, no external APIs)
- **Trigger**: When user submits answer to question
- **Content**: 
  - Multi-step explanations
  - Common mistakes identified
  - Next recommended topic
  - Difficulty assessment of question

### 2. Spaced Repetition Optimization
- **Algorithm**: Ebbinghaus forgetting curve + SM-2
- **Intervals**: [1, 3, 7, 14, 30, 60, 120] days
- **Factors**: Accuracy, difficulty, time since review
- **Benefit**: Optimal review timing reduces study time by 50%

### 3. Performance Prediction
- **Prediction**: Estimated days to master each topic
- **Confidence**: Based on learning rate and data consistency
- **Use**: Motivate learners with realistic timelines

### 4. Session Analytics
- **Metrics**: Streak, consistency, peak hours, total time
- **Period**: Configurable (7, 14, 30, 90 days)
- **Use**: Identify learning patterns and engagement trends

### 5. Confidence Scoring
- **Tracking**: User self-reported confidence per answer
- **Distribution**: Low/Medium/High categorization
- **Use**: Detect overconfidence, adjust difficulty

## Database Schema

The application uses PostgreSQL with the following main entities:

- **users**: Student accounts with learning preferences
- **subjects**: Areas of study (Math, Chemistry, etc.)
- **topics**: Individual topics within subjects
- **questions**: Quiz questions with multiple choice options
- **user_progress**: Tracks accuracy and attempts per topic
- **user_answers**: Individual answer records (includes confidence_level)
- **learning_paths**: Personalized study plans
- **user_sessions**: Learning session tracking (for analytics)

### New Fields for Advanced Features
- `user_answers.confidence_level`: Float (0.0-1.0) - User's confidence in answer
- `user_answers.created_at`: DateTime - Timestamp for spaced repetition tracking

## Development Workflow

1. Create feature branch: `git checkout -b feature/feature-name`
2. Make changes across frontend/backend
3. Test locally
4. Run linting:
   - Backend: `python -m flake8 app/`
   - Frontend: `npm run lint`
5. Commit and push
6. Create pull request

## Testing

### Backend Tests
```bash
cd backend
pytest  # Run all tests
pytest -v  # Verbose output
pytest --cov=app  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test  # Run tests
npm run test:coverage  # With coverage
```

## Deployment

### Production Checklist
- [ ] Add environment-specific config
- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure CORS origins
- [ ] Set DEBUG=False in backend
- [ ] Run database migrations
- [ ] Collect static files
- [ ] Set up SSL/TLS
- [ ] Configure AI API keys
- [ ] Set up CDN for frontend
- [ ] Configure monitoring/logging

## Troubleshooting

### Backend issues
- **Port already in use**: `lsof -i :8000` (macOS/Linux)
- **Database connection**: Check DATABASE_URL in .env
- **Import errors**: `pip install -r requirements.txt --force-reinstall`

### Frontend issues
- **Port already in use**: `lsof -i :5173` (macOS/Linux)
- **Build errors**: `rm -rf node_modules && npm install`
- **CORS errors**: Check ALLOWED_ORIGINS in backend .env

### Docker issues
- **Container won't start**: Check logs with `docker-compose logs`
- **Volume permissions**: Ensure Docker has access to project directory
- **Network issues**: `docker network prune` then restart containers

## Contributing

1. Follow the project structure
2. Write meaningful commit messages
3. Keep functions small and focused
4. Add docstrings to complex logic
5. Test before committing

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [React docs](https://react.dev)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org)
- [Tailwind CSS](https://tailwindcss.com)
- [Zustand Docs](https://github.com/pmndrs/zustand)
