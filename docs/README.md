# Vibe Deutsch - German Learning Platform

A comprehensive German learning platform with AI-powered vocabulary analysis, persistent authentication, and intelligent learning features.

## ✨ Features

- 🔍 **Smart Word Search**: Database-first lookup with OpenAI fallback for unknown words
- 📚 **Complete Grammar Display**: Articles, plurals, verb conjugations across all tenses  
- 🌐 **Multi-language Support**: German, English, and Chinese translations
- 📝 **Interactive Exams**: Fill-in-the-blank, multiple choice, and spaced repetition
- ⭐ **Favorites System**: Save words for focused study
- 📊 **Progress Tracking**: Search history and learning analytics
- 🎯 **SRS (Spaced Repetition)**: Intelligent review scheduling
- ⚡ **Intelligent Caching**: Minimizes API costs with smart response caching
- 📋 **Bulk Import**: Excel and PDF vocabulary import with auto-enhancement
- 🔐 **Persistent Authentication**: Remember me for 90 days, automatic token refresh
- 🐳 **Docker Ready**: One-click deployment on Synology NAS and other platforms

## 🛠 Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue 3 + TypeScript + Vite + Tailwind CSS  
- **AI**: OpenAI API via OpenRouter
- **Authentication**: JWT with refresh tokens and persistent sessions
- **Package Management**: UV (Python) + npm (Frontend)
- **Deployment**: Docker + Docker Compose

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

📖 **For Synology NAS**: See [DEPLOY-SYNOLOGY.md](DEPLOY-SYNOLOGY.md) for detailed GUI setup instructions.

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

# Start development server
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
│   ├── api/               # API endpoints
│   ├── core/              # Configuration & security
│   ├── db/                # Database setup
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic
├── frontend/              # Vue 3 application
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── views/         # Page components
│   │   ├── stores/        # Pinia state management
│   │   └── router/        # Vue Router setup
├── data/                  # SQLite database files
├── tests/                 # Test scripts
├── scripts/               # Utility scripts
│   ├── fixes/            # Database repair scripts
│   └── checks/           # Analysis scripts
├── Screenshots/           # Documentation images
├── Dockerfile            # Docker build configuration
├── docker-compose.yml    # Docker orchestration
└── DEPLOY-SYNOLOGY.md    # Synology deployment guide
```

## 🔐 Authentication & Security

### Advanced Session Management
- **Persistent Login**: Sessions survive browser restarts and network disconnections
- **Remember Me**: Optional 90-day extended sessions
- **Automatic Refresh**: Tokens refresh automatically before expiry
- **Smart Recovery**: 401 errors trigger seamless token refresh
- **HTTP Compatible**: Secure authentication over HTTP for local networks

### Login Features
- ✅ **24-hour standard sessions**
- ✅ **90-day extended sessions** with "Remember me"
- ✅ **Automatic token refresh** (refreshes 5 minutes before expiry)
- ✅ **Network resilience** (handles connection drops gracefully)
- ✅ **Multi-tab synchronization**

## 🔧 Key Features Detail

### Word Search & Analysis
- **Database Priority**: Instant lookup from local vocabulary database
- **AI Enhancement**: Unknown words analyzed via OpenAI with grammatical information
- **Smart Suggestions**: Non-German inputs get 5 relevant German word suggestions
- **Complete Grammar**: Articles (der/die/das), plurals, and full verb conjugation tables

### Exam System
- **Multiple Formats**: Fill-in-the-blank, multiple choice, translation exercises
- **Adaptive Difficulty**: Questions adjust based on performance
- **Progress Tracking**: Detailed analytics and improvement metrics

### Vocabulary Management
- **Excel Import**: Bulk import from structured Excel files
- **Auto-Enhancement**: Missing translations, examples, and grammar auto-generated
- **Duplicate Cleanup**: Intelligent merging of related word forms
- **Quality Assurance**: Comprehensive validation and error correction

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
Required environment variables in `.env`:
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=your_32_character_secret_key
```

### Synology NAS Deployment
1. **Install Container Manager** from Package Center
2. **Upload project** to `/docker/vibe-deutsch/`
3. **Configure environment** variables in Container Manager
4. **Deploy with docker-compose.yml**
5. **Access at** `http://your-nas-ip:8000`

See [DEPLOY-SYNOLOGY.md](DEPLOY-SYNOLOGY.md) for detailed step-by-step instructions.

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login with remember me option
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info

### Word & Translation
- `POST /translate/word` - Word lookup with AI fallback
- `POST /translate/sentence` - Sentence translation with gloss
- `POST /translate/word/select` - Select from AI suggestions

### Learning Features  
- `GET /search/history` - Search history
- `GET /favorites` - Saved words
- `POST /exam/generate` - Create practice exam
- `GET /srs/review` - Spaced repetition cards

## 📚 Vocabulary Import

### Supported Formats
- **Excel Files**: `.xlsx` with German, English, Chinese columns
- **PDF Files**: German vocabulary lists with auto-extraction

### Import Process
```bash
# Import Excel vocabulary
uv run python scripts/import_excel_vocabulary.py

# Import from PDF  
uv run python scripts/pdf_vocabulary_importer.py

# Auto-fix incomplete entries
uv run python scripts/fixes/enhanced_database_fixer.py --mode all
```

## 🧪 Testing

```bash
# Run all tests
uv run python tests/run_tests.py

# Test specific functionality
uv run python tests/test_api_endpoints.py
uv run python tests/test_openai_functions.py

# Test live API integration
uv run python tests/test_live_api.py

# Test authentication system
uv run python tests/test_api_directly.py
```

## 🔧 Development Commands

```bash
# Database analysis
uv run python scripts/checks/inspect_database.py

# Check for incomplete entries  
uv run python scripts/checks/check_incomplete_words.py

# Fix database issues
uv run python scripts/fixes/enhanced_database_fixer.py

# Generate missing examples
uv run python scripts/fixes/generate_missing_examples.py
```

## ⚠️ Troubleshooting

### Common Issues
- **401 OpenAI Error**: Check `.env` file for correct API key and base URL
- **Database Errors**: Ensure `data/` directory exists and is writable
- **Frontend Build Issues**: Clear cache with `rm -rf frontend/node_modules && npm install`
- **CORS Issues**: Backend CORS settings in `app/main.py`, frontend proxy in `vite.config.ts`
- **Session Timeout**: Check token refresh logs, verify refresh token endpoint

### Docker Issues
- **Container Won't Start**: Check logs with `docker-compose logs`
- **Port Conflicts**: Modify ports in `docker-compose.yml`
- **Volume Permissions**: Ensure data directory has correct permissions
- **Memory Issues**: Increase container memory limits for large vocabulary imports

### Authentication Debugging
```bash
# Check token status in browser console
localStorage.getItem('token')
localStorage.getItem('refreshToken')
localStorage.getItem('tokenExpiry')

# Backend token verification
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/auth/me
```

## 🚀 Production Deployment

### Security Checklist
- [ ] Change default `SECRET_KEY` in production
- [ ] Use strong OpenAI API key
- [ ] Configure firewall rules for port 8000
- [ ] Set up SSL/TLS if exposing to internet
- [ ] Regular database backups
- [ ] Monitor authentication logs

### Performance Optimization
- **Database**: Use SSD storage for better performance
- **Memory**: Allocate 1-2GB RAM for optimal performance
- **Network**: Use CDN for static assets in production
- **Caching**: OpenAI responses cached automatically

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for language model capabilities
- Vue.js and FastAPI communities for excellent frameworks
- Docker for containerization technology
- Synology for NAS platform compatibility
- German language learning community for inspiration and feedback

---

🎉 **Ready to learn German?** Deploy with Docker and start your language journey!