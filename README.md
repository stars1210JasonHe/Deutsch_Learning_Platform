# Vibe Deutsch - German Learning Platform 🇩🇪

A comprehensive German learning platform with AI-powered vocabulary analysis, chat assistance, image generation, and intelligent learning features.

## ✨ Key Features

- 🔍 **Smart Word Search**: Database-first lookup with OpenAI fallback for unknown words
- 💬 **Interactive Chat**: Ask questions about any German word with configurable conversation rounds
- 🎨 **AI Image Generation**: Create educational images for vocabulary using DALL-E 2/3
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
- **Frontend**: Vue 3 + TypeScript + Vite + Tailwind CSS + Pinia
- **AI**: OpenAI API via OpenRouter (GPT-4o-mini, DALL-E 2/3)
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
│   ├── api/               # API endpoints (auth, translate, chat, images, etc.)
│   ├── core/              # Configuration & security
│   ├── db/                # Database setup
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic
├── frontend/              # Vue 3 application
│   ├── src/
│   │   ├── components/    # Reusable components (ChatModal, ImageModal, etc.)
│   │   ├── views/         # Page components
│   │   ├── stores/        # Pinia state management (auth, settings, search)
│   │   └── router/        # Vue Router setup
├── tools/                 # Utility and processing scripts
│   ├── fixes/            # Database repair scripts
│   ├── checks/           # Analysis scripts
│   ├── imports/          # Import utilities
│   └── tests/            # Development test scripts
├── tests/                 # API and integration tests
├── scripts/               # Database management scripts
├── data/                  # SQLite database files
├── Sources/               # PDF sources and dictionary files
├── Screenshots/           # Documentation images
├── MD/                    # Documentation files
├── logs/                  # Processing logs
├── Dockerfile            # Docker build configuration
├── docker-compose.yml    # Docker orchestration
└── README.md             # This file
```

## 🔐 Authentication & Security

### Advanced Session Management
- **Persistent Login**: Sessions survive browser restarts and network disconnections
- **Remember Me**: Optional 90-day extended sessions
- **Automatic Refresh**: Tokens refresh automatically before expiry
- **Smart Recovery**: 401 errors trigger seamless token refresh
- **HTTP Compatible**: Secure authentication over HTTP for local networks

### Test Account
For testing purposes:
- **Email**: `heyeqiu1210@gmail.com`
- **Password**: `123456`

## 🆕 New AI-Powered Features

### Chat Assistant
- 💬 Interactive conversations about any German word
- 🎯 Educational context with grammar, usage, and cultural information
- ⚙️ Configurable conversation rounds (default: 10)
- 📋 Copy/download conversations for review
- 🧠 Powered by OpenAI via OpenRouter

### AI Image Generation
- 🎨 Generate educational images for vocabulary words
- 🖼️ Multiple styles: Educational, Cartoon, Semi-realistic
- 🔧 Configurable models: DALL-E 2 (fast) or DALL-E 3 (quality)
- 📐 Multiple size options (256x256 to 1792x1024)
- 💾 Download and copy functionality

## 🔧 Key Features Detail

### Enhanced Search System
- **Database Priority**: Instant lookup from local vocabulary database
- **AI Enhancement**: Unknown words analyzed via OpenAI with grammatical information
- **Smart Suggestions**: Non-German inputs get relevant German word suggestions
- **Multiple Choice**: When search returns multiple options, user can select the intended word
- **Complete Grammar**: Articles (der/die/das), plurals, and full verb conjugation tables

### Vocabulary Management
- **Excel Import**: Bulk import from structured Excel files
- **PDF Processing**: Extract vocabulary from Collins dictionary PDFs
- **Auto-Enhancement**: Missing translations, examples, and grammar auto-generated
- **Duplicate Cleanup**: Intelligent merging of related word forms
- **Quality Assurance**: Comprehensive validation and error correction

### Exam & Learning System
- **Multiple Formats**: Fill-in-the-blank, multiple choice, translation exercises
- **Adaptive Difficulty**: Questions adjust based on performance
- **Progress Tracking**: Detailed analytics and improvement metrics
- **Spaced Repetition**: SRS system for optimal retention

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

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login with remember me option
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Word & Translation
- `POST /api/translate/word` - Word lookup with AI fallback
- `POST /api/translate/sentence` - Sentence translation with gloss
- `POST /api/translate/word/select` - Select from AI suggestions
- `POST /api/translate/word/choice` - Select from multiple choice options

### AI Features
- `POST /api/chat/word` - Chat about a specific word
- `POST /api/images/generate` - Generate educational images

### Learning Features  
- `GET /api/search/history` - Search history
- `GET /api/favorites` - Saved words
- `POST /api/exam/generate` - Create practice exam
- `GET /api/srs/review` - Spaced repetition cards

## 🧪 Testing & Development

### Running Tests
```bash
# Run all tests
uv run python tests/run_tests.py

# Test specific functionality
uv run python tests/test_api_endpoints.py
uv run python tests/test_live_api.py

# Frontend E2E tests
cd frontend && npm run test
```

### Development Commands
```bash
# Database analysis
uv run python scripts/checks/inspect_database.py

# Fix database issues
uv run python scripts/fixes/enhanced_database_fixer.py --mode all

# Import vocabulary
uv run python scripts/import_excel_vocabulary.py

# Process Collins dictionary
uv run python tools/complete_collins_processor.py
```

### Unicode Support (Windows)
For scripts handling German characters (ä, ö, ü, ß):
```bash
set PYTHONIOENCODING=utf-8 && uv run python script.py
# OR
uv run python script.py 2>nul
```

## ⚠️ Troubleshooting

### Common Issues
- **401 OpenAI Error**: Check `.env` file for correct API key and base URL
- **Database Errors**: Ensure `data/` directory exists and is writable
- **Frontend Build Issues**: Clear cache with `rm -rf frontend/node_modules && npm install`
- **CORS Issues**: Backend CORS settings in `app/main.py`, frontend proxy in `vite.config.ts`
- **Port 3000 Required**: Frontend must run on port 3000 for proxy configuration

### Chat/Image Features
- **Chat Errors**: Verify OpenAI API key and OpenRouter configuration
- **Image Generation Fails**: Check model availability and size settings
- **Modal Issues**: Clear browser cache and refresh page

### Authentication Debugging
```bash
# Check token status in browser console
localStorage.getItem('token')
localStorage.getItem('refreshToken')
localStorage.getItem('tokenExpiry')

# Backend token verification
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/auth/me
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
- **Memory**: Allocate 2-4GB RAM for optimal performance with AI features
- **Network**: Use CDN for static assets in production
- **Caching**: OpenAI responses cached automatically to minimize costs

## 📚 Documentation

- **[CLAUDE.md](MD/CLAUDE.md)**: Development guide and architecture details
- **[DEPLOY-SYNOLOGY.md](MD/DEPLOY-SYNOLOGY.md)**: Synology NAS deployment guide
- **[SEARCH-LOGIC-COMPLETE.md](MD/SEARCH-LOGIC-COMPLETE.md)**: Search system implementation
- **[GERMAN-UMLAUT-FIX.md](MD/GERMAN-UMLAUT-FIX.md)**: Unicode handling solutions

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for language model capabilities and image generation
- Vue.js and FastAPI communities for excellent frameworks
- Docker for containerization technology
- Synology for NAS platform compatibility
- German language learning community for inspiration and feedback

---

🎉 **Ready to learn German?** Deploy with Docker and start your language journey with AI-powered assistance!

📧 **Questions?** Check the documentation in the `MD/` folder or open an issue on GitHub.