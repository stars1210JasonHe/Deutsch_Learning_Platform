# Vibe Deutsch - AI-Powered German Learning Platform

A production-ready German learning platform with intelligent translation, multi-language support, interactive AI chat, and comprehensive vocabulary management.

## ✨ Key Features

### 🌐 Intelligent Translation System
- **Multi-language Input** - English, Chinese, German word search
- **Auto Language Detection** - Smart detection with ambiguity handling
- **Translate Mode** - Auto-detect → German → Database search pipeline
- **Context-Aware Results** - Grammatical analysis with conjugation tables

### 🤖 AI-Powered Learning
- **Interactive Chat** - Educational conversations with quick tips system
- **AI Image Generation** - Visual vocabulary aids using DALL-E
- **Smart Word Analysis** - Complete grammar display with verb conjugations
- **Structured Responses** - Examples, practice exercises, and learning tips

### 📚 Comprehensive Vocabulary System
- **70K+ German Words** - Pre-loaded vocabulary database
- **Smart Search** - Database-first with AI fallback for unknown words
- **Flexible Schema** - WordForm system supporting all German grammar cases
- **Bulk Import Tools** - Excel/PDF processing for vocabulary expansion

### 🎯 Learning Features
- **Spaced Repetition System** - Scientific learning algorithm
- **Interactive Exams** - AI-generated questions with auto-grading
- **Favorites & Progress** - Personal vocabulary tracking
- **Search History** - Review past learning sessions
- **User Feedback System** - Report incorrect word data with AI-powered corrections

### 🔒 Production Security
- **JWT Authentication** - Secure tokens with 90-day refresh cycles
- **Enterprise Security** - XSS, CSRF, rate limiting protection
- **Environment Flexible** - HTTP/HTTPS deployment support
- **Multi-tab Sync** - Seamless authentication across browser tabs

## 🛠 Technology Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue 3 + TypeScript + Pinia + Tailwind CSS
- **AI Integration**: OpenAI GPT-4o-mini via OpenRouter
- **Infrastructure**: Docker + UV package management
- **Database**: SQLite with 70K+ words, forms, translations

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

Perfect for NAS devices, servers, or local development:

```bash
# Clone repository
git clone <repository-url>
cd LanguageLearning

# Create environment configuration
cp .env.example .env
# Edit .env with your OpenAI API key

# Deploy with Docker Compose
docker-compose up -d

# Access at http://localhost:8000
```

**Demo Account**: Email `demo@example.com`, Password `demo123`

### Option 2: Development Setup

#### Prerequisites
- Python 3.10+ with UV: `pip install uv`
- Node.js 18+

#### Backend Setup
```bash
# Install Python dependencies
uv sync

# Start development server
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server (MUST use port 3000)
npm run dev
```

## 🏗 Architecture Overview

### Core Services Architecture

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Vue Frontend  │───▶│   FastAPI Backend    │───▶│  OpenAI API     │
│                 │    │                      │    │                 │
│ • Word Search   │    │ • Translation API    │    │ • GPT-4o-mini   │
│ • Chat Interface│    │ • Language Detection │    │ • DALL-E        │
│ • Image Display │    │ • Vocabulary Service │    │ • Text Analysis │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
                                  │
                       ┌──────────▼──────────┐
                       │   SQLite Database   │
                       │                     │
                       │ • 70K+ Word Lemmas  │
                       │ • Translation Cache │
                       │ • User Data & Auth  │
                       └─────────────────────┘
```

### Translation Pipeline

1. **Language Detection** - AI identifies input language with confidence scoring
2. **Ambiguity Handling** - Special cases like "hell" (German=bright vs English=underworld)
3. **German Translation** - Multi-option translation with context
4. **Database Search** - Exact match → Inflected forms → Fuzzy matching
5. **AI Enhancement** - Unknown words analyzed and cached

## 📁 Project Structure

```
LanguageLearning/
├── app/                     # FastAPI Backend
│   ├── api/                # REST API endpoints
│   │   ├── words.py        # Translation & search system
│   │   ├── chat.py         # AI chat with quick tips
│   │   ├── auth.py         # JWT authentication
│   │   ├── images.py       # DALL-E integration
│   │   └── feedback.py     # User feedback system
│   ├── services/           # Core business logic
│   │   ├── openai_service.py      # AI integration hub
│   │   ├── vocabulary_service.py  # Word management
│   │   └── enhanced_search_service.py # Multi-language search
│   ├── models/             # SQLAlchemy database models
│   └── core/               # Configuration & security
├── frontend/               # Vue 3 TypeScript Frontend
│   ├── src/
│   │   ├── views/          # Main pages (Home, Dashboard, etc.)
│   │   ├── components/     # UI components (WordResult, FeedbackModal)
│   │   ├── stores/         # Pinia state management
│   │   └── composables/    # Reusable Vue logic
├── scripts/                # Production vocabulary tools
│   ├── samples/            # Sample data generation scripts
│   ├── process_feedback_with_openai.py  # Automated feedback processing
│   └── send_email.py       # Email notification system
├── tests/                  # Comprehensive test suite
├── docs/                   # Organized documentation
│   ├── deployment/         # Docker, NAS deployment guides
│   ├── development/        # Technical guides & debugging
│   └── security/           # Security implementation docs
└── data/                   # SQLite database & backups
```

## 🔧 Development Commands

### Backend Development
```bash
# Start development server
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run comprehensive tests
uv run python tests/run_tests.py

# Vocabulary management
uv run python scripts/vocabulary_manager.py --help
uv run python scripts/excel_vocabulary_importer.py file.xlsx

# Database operations
uv run python scripts/vocabulary_manager.py --stats  # View database statistics
uv run python scripts/vocabulary_manager.py --search "word"  # Search database

# Feedback system management
uv run python scripts/process_feedback_with_openai.py  # Process pending feedback with AI
uv run python check_feedback.py  # View feedback statistics and status
```

### Frontend Development
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Run E2E tests
npm run test
npm run test:headed  # With browser UI
```

## 🐳 Docker Configuration

### Production Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=sqlite:///./data/app.db
```

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openrouter_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini

# Security
SECRET_KEY=your_32_character_secret_key

# Database
DATABASE_URL=sqlite:///./data/app.db

# Optional: Network configuration for NAS deployment
ADDITIONAL_ALLOWED_HOSTS=http://10.0.0.100:8000,https://nas.local:8000
```

## 📊 API Overview

### Translation & Search
- `POST /api/words/translate-search` - Multi-language word translation
- `POST /api/words/translate-search-select` - Select German translation
- `GET /api/words/{lemma}` - Detailed word analysis
- `GET /api/words/` - Search vocabulary database

### AI Features  
- `POST /api/chat/word` - Interactive word chat with structured responses
- `POST /api/images/generate` - Educational image generation
- `POST /api/translate/sentence` - Sentence translation with glossing

### Learning System
- `POST /api/exam/generate` - AI-generated practice exams
- `GET /api/srs/review` - Spaced repetition cards
- `GET /api/favorites` - Saved vocabulary
- `GET /api/search/history` - Learning session history

### Feedback System
- `POST /api/feedback/word/{lemma_id}` - Submit word feedback
- `GET /api/feedback/word/{lemma_id}` - Retrieve word feedback

## 🧪 Testing & Quality

### Test Coverage
- **API Tests** - Complete endpoint validation
- **Security Tests** - Authentication & middleware testing
- **Integration Tests** - Live API testing
- **E2E Tests** - Playwright browser automation

### Quality Assurance
```bash
# Backend tests
uv run python tests/run_tests.py
uv run python tests/test_security_fixes.py

# Frontend tests
cd frontend
npm run lint
npm run test
```

## 🌍 Deployment Scenarios

### 🏠 Home NAS Deployment
- **Synology NAS** - Container Manager GUI setup
- **Single Port** - Simplified networking (port 8000)
- **HTTP Support** - Local network deployment
- **Data Persistence** - Volume mounting for database

### ☁️ Server Deployment
- **HTTPS Ready** - SSL/TLS configuration
- **Docker Compose** - Multi-container orchestration
- **Health Checks** - Automatic restart on failure
- **Backup Ready** - Database backup automation

## 🔍 Troubleshooting

### Common Issues
- **Translation not showing**: Clear browser cache, check frontend display logic
- **OpenAI errors**: Verify API key and model availability
- **Database conflicts**: Use vocabulary manager tools for diagnosis
- **Unicode issues**: Use `2>nul` on Windows for German characters

### Debug Resources
- **API Documentation**: http://localhost:8000/docs
- **CLAUDE.md**: Comprehensive development guide
- **docs/development/**: Technical debugging guides

## 📚 Documentation

- **[docs/CLAUDE.md](docs/CLAUDE.md)** - Complete development guide
- **[docs/deployment/](docs/deployment/)** - Deployment scenarios
- **[docs/security/](docs/security/)** - Security implementation
- **[docs/development/](docs/development/)** - Technical guides & debugging
- **[scripts/README.md](scripts/README.md)** - Vocabulary management tools

## 🚀 Production Checklist

### Security
- [ ] Change `SECRET_KEY` for production
- [ ] Configure HTTPS for internet exposure  
- [ ] Set up database backups
- [ ] Review authentication logs

### Performance
- [ ] SSD storage for database
- [ ] 2-4GB RAM allocation
- [ ] OpenAI response caching enabled
- [ ] Monitor API usage costs

---

**🎯 Ready to master German?** Deploy with Docker and experience AI-powered language learning!

*Built with ❤️ for German language learners worldwide*