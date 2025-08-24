# Vibe Deutsch - German Learning Platform

A production-ready German learning platform with AI-powered vocabulary analysis, interactive chat, image generation, and comprehensive learning features.

## ✨ Features

### Core Learning
- **Smart Word Search** - Database-first lookup with OpenAI fallback
- **Complete Grammar Display** - Articles, plurals, verb conjugations
- **Multi-language Support** - German, English, Chinese translations
- **Interactive Exams** - Fill-in-the-blank, multiple choice questions
- **Spaced Repetition System** - Intelligent review scheduling
- **Favorites & Progress Tracking** - Save words and monitor learning

### AI-Powered Features
- **Interactive Chat** - Educational conversations about German words
- **AI Image Generation** - Visual vocabulary aids using DALL-E
- **Smart Suggestions** - AI-enhanced word recommendations
- **Auto-Enhancement** - Missing grammar and translations generated

### Production Features
- **Secure Authentication** - JWT with refresh tokens, 90-day sessions
- **Docker Deployment** - One-click setup for NAS and servers
- **Bulk Import** - Excel/PDF vocabulary import with processing
- **Intelligent Caching** - Minimizes API costs
- **Enterprise Security** - Security headers, rate limiting, HTTPS support

## 🛠 Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vue 3, TypeScript, Tailwind CSS, Pinia
- **AI**: OpenAI API via OpenRouter
- **Security**: JWT authentication, security middleware
- **Infrastructure**: Docker, UV package management

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

Perfect for Synology NAS, servers, or any Docker environment:

```bash
# Clone repository
git clone https://github.com/stars1210JasonHe/Deutsch_Learning_Platform.git
cd LanguageLearning

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Deploy with Docker
docker-compose up -d

# Access at http://localhost:8000
```

📖 **For Synology NAS**: See [MD/DEPLOY-SYNOLOGY.md](MD/DEPLOY-SYNOLOGY.md) for detailed GUI setup instructions.

### Option 2: Local Development

#### Prerequisites
- Python 3.10+
- Node.js 18+
- UV package manager: `pip install uv`

#### 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/stars1210JasonHe/Deutsch_Learning_Platform.git
cd LanguageLearning

# Create environment file
cp .env.example .env
# Edit .env with your OpenAI API key and configuration
```

#### 2. Backend Setup
```bash
# Install dependencies
uv sync

# Start backend server  
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server (MUST be on port 3000)
npm run dev
```

#### 4. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
LanguageLearning/
├── app/                    # FastAPI backend
│   ├── api/               # REST endpoints (auth, translate, chat, images)
│   ├── core/              # Configuration, security, dependencies
│   ├── db/                # Database models and session management
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic request/response schemas
│   └── services/          # Business logic and AI integrations
├── frontend/              # Vue 3 TypeScript application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── views/         # Page components
│   │   ├── stores/        # Pinia state management
│   │   └── router/        # Vue Router configuration
├── scripts/               # Production vocabulary management
├── tests/                 # API and integration tests
├── archive/               # Development tools (archived)
├── MD/                    # Organized documentation
│   ├── deployment/        # Deployment guides
│   ├── security/          # Security documentation
│   └── development/       # Development guides
├── data/                  # SQLite database
├── docker-compose.yml     # Container orchestration
└── Dockerfile             # Multi-stage build configuration
```

## 🔐 Security & Authentication

- **JWT Authentication** - Access and refresh tokens with automatic renewal
- **Security Headers** - XSS, CSRF, clickjacking protection
- **Rate Limiting** - Brute force protection
- **Environment-aware** - HTTP/HTTPS deployment flexibility
- **Cookie Security** - HttpOnly, secure, SameSite protection

### Demo Account
- Email: `demo@example.com`
- Password: `demo123`

## 📋 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - Login with remember me
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/me` - Current user info

### Word & Translation
- `POST /api/translate/word` - Word lookup with AI fallback
- `POST /api/translate/sentence` - Sentence translation
- `POST /api/chat/word` - Interactive word chat
- `POST /api/images/generate` - Educational image generation

### Learning
- `GET /api/favorites` - Saved words
- `GET /api/search/history` - Search history  
- `POST /api/exam/generate` - Practice exams
- `GET /api/srs/review` - Spaced repetition

## 🐳 Docker Deployment

### Quick Deploy
```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Configuration
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=your_32_character_secret_key
```

## 🧪 Development

```bash
# Run tests
uv run python tests/run_tests.py

# Vocabulary management  
uv run python scripts/vocabulary_manager.py --help

# Frontend E2E tests
cd frontend && npm run test
```

## ⚠️ Troubleshooting

- **OpenAI Errors**: Check API key in `.env`
- **Database Issues**: Ensure `data/` directory exists
- **CORS Problems**: Frontend must run on port 3000
- **Build Failures**: Clear node_modules and reinstall

## 📚 Documentation

- **[MD/deployment/](MD/deployment/)** - Deployment guides
- **[MD/security/](MD/security/)** - Security documentation  
- **[MD/development/](MD/development/)** - Development guides
- **[scripts/README.md](scripts/README.md)** - Vocabulary management

## Production Deployment

### Security Checklist
- [ ] Change `SECRET_KEY` in production
- [ ] Configure SSL/TLS for internet exposure
- [ ] Set up regular database backups
- [ ] Monitor authentication logs

### Performance
- Use SSD storage for database
- Allocate 2-4GB RAM for AI features
- OpenAI responses cached automatically

---

**Ready to learn German?** Deploy with Docker and start your AI-powered language journey!