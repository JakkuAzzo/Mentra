# Setup & Installation Guide

## Local Development

### Prerequisites
- Node.js 18+ (Frontend)
- Python 3.11+ (Backend)
- PostgreSQL 14+
- Redis (optional, for caching)

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

# Run database migrations (if applicable)
python -m alembic upgrade head  # uncomment when migrations added

# Start development server
uvicorn app.main:app --reload
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

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

# Stop services
docker-compose down
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
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

## Database Schema

The application uses PostgreSQL with the following main entities:

- **users**: Student accounts with learning preferences
- **subjects**: Areas of study (Math, Chemistry, etc.)
- **topics**: Individual topics within subjects
- **questions**: Quiz questions with multiple choice options
- **user_progress**: Tracks accuracy and attempts per topic
- **user_answers**: Individual answer records
- **learning_paths**: Personalized study plans
- **user_sessions**: Learning session tracking

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user

### Questions
- `GET /api/questions/{question_id}` - Get specific question
- `GET /api/questions/topic/{topic_id}` - Get topic's questions
- `GET /api/questions/adaptive/{user_id}/{topic_id}` - Get adaptive question
- `POST /api/questions/submit-answer` - Submit answer and get feedback

### Progress
- `GET /api/progress/user/{user_id}` - Get all progress records
- `GET /api/progress/summary/{user_id}` - Get summary statistics
- `GET /api/progress/weak-topics/{user_id}` - Get weak areas

### Recommendations
- `GET /api/recommendations/next-topic/{user_id}` - Get next topic to study
- `GET /api/recommendations/learning-path/{user_id}` - Get full learning path
- `GET /api/recommendations/should-review/{user_id}/{topic_id}` - Check review status

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
