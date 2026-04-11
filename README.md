# Mentra - AI-Driven Personal Tutor

An intelligent tutoring system that provides personalized, adaptive, and interactive learning experiences for college/A-Level and undergraduate students.

## Project Overview

Mentra addresses the gap in current e-learning systems by offering:
- **Personalized Learning Guidance**: Adapts to individual learner performance and pace
- **Intelligent Feedback**: Provides step-by-step explanations for incorrect answers
- **Adaptive Content**: Recommends topics to study based on identified weaknesses
- **Progress Tracking**: Visualizes improvement over time to maintain motivation

## Architecture

```
mentra/
├── frontend/          # React TypeScript UI
├── backend/           # Python FastAPI + AI/ML
├── docs/             # Documentation & architecture diagrams
└── docker-compose.yml # Container orchestration
```

## Functional Requirements

| Requirement | Description |
|---|---|
| FR1 | Provide personalized learning guidance based on individual performance |
| FR2 | Deliver step-by-step explanations for incorrect answers |
| FR3 | Recommend topics to study based on identified weaknesses |
| FR4 | Break learning content into manageable sections |
| FR5 | Provide expert-level learning support accessible 24/7 |
| FR6 | Track learner progress and highlight improvement |

## Non-Functional Requirements

- **Usability**: Clear, concise, easy-to-understand feedback
- **Performance**: Immediate feedback delivery (<2 seconds)
- **Availability**: 24/7 accessibility
- **Engagement**: Interactive and visually clear explanations
- **Ethics**: Support learning without encouraging academic dishonesty

## Target Users

1. **Exam-Focused Learners** (A-Level/College, age 17-18)
   - Goal: Achieve strong exam results
   - Need: Guided revision pathways, clear feedback

2. **Independent Learners** (Undergraduate, age 19-21)
   - Goal: Understand concepts efficiently
   - Need: Personalized guidance, adaptive practice

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **AI/NLP**: OpenAI API / LLama integrations
- **Cache**: Redis
- **Auth**: JWT + OAuth2
- **Deployment**: Docker, AWS/Railway

## Quick Start

### Prerequisites
- Node.js 18+ (frontend)
- Python 3.11+ (backend)
- PostgreSQL 14+
- Docker & Docker Compose (optional)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Docker Setup

```bash
docker-compose up -d
```

## Development Phases

**Phase 1**: Project scaffolding & database schema
**Phase 2**: Core API endpoints & authentication
**Phase 3**: Frontend UI components
**Phase 4**: AI/ML personalization engine
**Phase 5**: Integration & testing
**Phase 6**: Deployment & optimization

## Project Status

Starting Phase 1: Project scaffolding

## Contributing

This is a classroom project. All code must follow ethics guidelines and support genuine learning.

## Author

Abokar Mohamed (K2336443)

## License

Proprietary - Kingston University Final Year Project

## References

- Holmes et al. (2019) - Artificial Intelligence in Education
- OpenAI (2023) - ChatGPT & Language Models
- Luckin et al. (2016) - Intelligence Unleashed
