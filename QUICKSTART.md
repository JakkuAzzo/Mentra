# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Docker (Recommended)

```bash
# From project root
docker-compose up -d

# Wait for services to start (30 seconds)
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Option 2: Local Development

#### Terminal 1 - Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py  # Populate sample data
uvicorn app.main:app --reload
```

#### Terminal 2 - Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

#### Terminal 3 - Database (if needed)
```bash
# Using Docker for just the database
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=mentra_user \
  -e POSTGRES_PASSWORD=mentra_password \
  -e POSTGRES_DB=mentra_db \
  postgres:15-alpine
```

---

## 📝 First Steps After Startup

### Create a Test Account

Navigate to **http://localhost:5173/register**

```
Full Name: Test Student
Email: test@example.com
Username: teststudent
Password: password123
```

### Access the Dashboard

After login, you'll see:
- ✅ Progress summary cards
- 📚 Personalized learning path
- 📊 Performance analytics

### Start Learning

1. Click "Practice" on any topic in the learning path
2. Answer quiz questions
3. Get AI-powered feedback with explanations
4. Watch your progress update automatically

---

## 🎯 Key Features to Try

### 1. Adaptive Difficulty
- Answer questions correctly → difficulty increases
- Answer incorrectly → get detailed explanation + easier questions next

### 2. Personalized Recommendations
- Your weak areas are highlighted
- Learning path prioritizes topics for review
- Spaced repetition built-in

### 3. Progress Tracking
- **Dashboard**: Quick overview of your learning
- **Progress Page**: Detailed topic-by-topic breakdown
- **Visualizations**: Accuracy graphs and mastery indicators

---

## 📚 Sample Credentials (if seeded)

```
Email: student@example.com
Password: testpass123
```

---

## 🔧 Troubleshooting

### Backend won't start?
```bash
# Check if port 8000 is in use
lsof -i :8000

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

### Frontend won't start?
```bash
# Check if port 5173 is in use
lsof -i :5173

# Clear node modules
rm -rf node_modules package-lock.json
npm install
```

### Database connection error?
```bash
# Verify DATABASE_URL in backend/.env
# Check PostgreSQL is running
docker ps | grep postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

---

## 📖 Documentation

- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Setup Guide**: See [SETUP.md](SETUP.md)
- **Project Spec**: See original [Final Year Project Document](../Final+year+project.docx)

---

## 🎨 UI Features

- ✨ Modern, responsive design with Tailwind CSS
- 📱 Mobile-friendly interface
- 🌙 Clean visual hierarchy
- ⚡ Fast, snappy interactions
- ♿ Accessible components

---

## 🚀 Deployment Ready

The project is containerized and ready for deployment to:
- AWS (ECS, App Runner, EC2)
- Heroku
- Railway
- DigitalOcean
- Any Docker-compatible platform

---

## 📧 Support

For issues or questions, refer to [SETUP.md](SETUP.md) troubleshooting section.

---

**Happy Learning! 🎓**
