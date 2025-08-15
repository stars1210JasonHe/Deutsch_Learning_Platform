# Vibe Deutsch - German Learning Platform

A comprehensive German learning platform with AI-powered vocabulary analysis, grammar display, and interactive learning features.

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

## 🛠 Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue 3 + TypeScript + Vite + Tailwind CSS  
- **AI**: OpenAI API via OpenRouter
- **Authentication**: JWT tokens
- **Package Management**: UV (Python) + npm (Frontend)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- UV package manager: `pip install uv`

### 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/stars1210JasonHe/Deutsch_Learning_Platform.git
cd LanguageLearning

# Create environment file
cp .env.example .env
# Edit .env with your OpenAI API key and configuration
```

### 2. Backend Setup
```bash
# Install dependencies
uv sync

# Start backend server  
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access Application
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
└── Screenshots/           # Documentation images
```

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

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login

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

### Environment Variables
Required in `.env`:
```bash
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=your_jwt_secret
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for language model capabilities
- Vue.js and FastAPI communities for excellent frameworks
- German language learning community for inspiration and feedback