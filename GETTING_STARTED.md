# 🎓 Mentra - Your Personalized Learning Companion

Welcome to **Mentra**, an AI-powered tutoring system that adapts to YOUR learning pace and style!

## ✨ What Makes Mentra Special?

1. **Adaptive Learning**: Questions get harder or easier based on your performance
2. **Smart Feedback**: Get step-by-step explanations, not just right/wrong answers
3. **Personalized Paths**: The system recommends what you should study next
4. **Progress Insights**: Watch your improvement with detailed analytics
5. **Available 24/7**: Learn whenever you're ready

## 🚀 Quick Start (Choose One)

### 🐳 Easiest: Docker (5 seconds setup)

```bash
# From the mentra directory
docker-compose up -d

# Done! Open these:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### 💻 Traditional: Local Setup (2 minutes)

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📝 Create Your First Account

1. Go to http://localhost:5173 (frontend)
2. Click "Sign up"
3. Fill in your details:
   - **Full Name**: Your name
   - **Email**: Your email
   - **Username**: Pick a username
   - **Password**: At least 8 characters
4. Click "Sign up" → You're in! 🎉

## 🎯 Start Learning

### 1. View Your Dashboard
You'll see:
- **Performance Summary**: Questions answered, accuracy score, topics studied
- **Learning Path**: Topics recommended based on your weak areas
- **Quick Stats**: Your progress at a glance

### 2. Practice a Topic
- Click "Practice" on any topic
- Read the question carefully
- Select your answer
- Submit and get instant feedback

### 3. Understand the Feedback
Mentra gives you:
- ✅ Or ❌ Whether you're right or wrong
- 📖 Detailed explanation of the concept
- 🔑 Key concepts to remember
- 💡 Next recommended topic

### 4. Track Your Progress
- Visit the **Progress** page to see detailed stats
- Watch your accuracy improve over time
- See which topics you've mastered
- Identify areas that need more practice

## 💡 How the Adaptive System Works

**You answer a question correctly?**
- Next question gets slightly harder
- System registers you're understanding the topic

**You answer incorrectly?**
- You get a detailed explanation
- Next question is slightly easier
- Topic is marked for review

**Pattern Recognition:**
- After 5+ questions, the system understands your level
- Difficulty automatically adjusts to your sweet spot
- You get challenged, but not frustrated

## 📚 Understanding the Dashboard

### Cards Show:
- **Questions Attempted**: Total questions you've answered
- **Overall Accuracy**: Your average score (%)
- **Topics Studied**: How many different topics you've practiced
- **Consistency**: How regularly you're learning

### Learning Path Section:
Shows topics sorted by priority:
1. Topics where you're struggling (below 70%)
2. Topics you haven't tried yet
3. Topics you're mastering (review occasionally)

Each topic shows:
- Your current accuracy on that topic
- Number of practice attempts
- A button to start practicing

### Areas for Improvement:
Topics where you scored below 70% are highlighted.
These are the ones to focus on!

### Mastered Topics:
🎉 Topics where you're 85%+ accurate.
These show you're really understanding these concepts.

## 🏆 Tips for Success

1. **Consistency Over Intensity**
   - 15 minutes daily beats 2 hours once a week
   - Spaced repetition helps memory

2. **Read Explanations Carefully**
   - Don't just look at the answer
   - Understanding concepts beats memorization

3. **Review Weak Topics Regularly**
   - The system reminds you based on forgetting curves
   - Make weak areas your priority

4. **Track Your Progress**
   - Look at your dashboard daily
   - Celebrate improving accuracy scores
   - Watch your overall stats climb

5. **Focus on Understanding**
   - AI feedback is there to help, not judge
   - Use mistakes as learning opportunities

## 🔐 Privacy & Security

- Your password is encrypted with bcrypt
- Your progress data is private
- Your learning history is used only to personalize YOUR experience
- Sessions expire after 30 minutes for security

## 🆘 Trouble? Reference These:

- **Can't log in?** Check your email and password
- **Port already in use?** Change it: `lsof -i :5173` (Mac/Linux)
- **Database issues?** Run `docker-compose down -v` and restart
- **Detailed setup help?** See [SETUP.md](SETUP.md)
- **Quick reference?** See [QUICKSTART.md](QUICKSTART.md)

## 📖 Full Documentation

| Document | What It Contains |
|---|---|
| [README.md](README.md) | Project overview & features |
| [SETUP.md](SETUP.md) | Installation & deployment guide |
| [QUICKSTART.md](QUICKSTART.md) | Super quick reference |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical details |
| [PROJECT_COMPLETION.md](PROJECT_COMPLETION.md) | What was built |

## 🚀 Next Steps

1. **Start Learning**: Pick a topic from your learning path
2. **Answer Questions**: Get feedback and explanations
3. **Check Progress**: Visit the Progress page to see your growth
4. **Track Improvement**: Come back daily to build streaks

## 🎓 Remember

Learning is a journey, not a race. Mentra is here to help you:
- ✅ Understand concepts deeply
- ✅ Identify your weak areas
- ✅ Build confidence through mastery
- ✅ Learn at your own pace

**Every question answered is a step forward!**

---

## 📊 Sample Test Account (if seeded)

```
Email: student@example.com
Password: testpass123
```

---

## 🤝 Feedback & Support

This project is built to help you learn better. If you have suggestions or encounter issues:
1. Check the troubleshooting in SETUP.md
2. Review the architecture docs
3. Check the code comments

---

**Ready? Let's go!**

## 🎯 Your First Steps:

1. Start Docker or local servers ⬆️
2. Create an account at http://localhost:5173
3. View your dashboard
4. Click "Practice" on a topic
5. Answer your first question
6. Get your first personalized explanation
7. Watch your progress grow

**Happy Learning! 🚀📚**

---

*Mentra - AI-Driven Personal Tutor*
*Making education personalized, adaptive, and effective*
