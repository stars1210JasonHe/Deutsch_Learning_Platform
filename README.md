Vibe Deutsch – German Learning Platform

Overview

Vibe Deutsch is a German learning platform featuring:
- Word search with database-first lookup, OpenAI fallback, and caching
- Sentence translation with word-by-word gloss
- Search history, exam system, and spaced repetition (SRS)
- Modern Vue 3 frontend with Vite + Pinia + Tailwind
- FastAPI backend with SQLAlchemy + SQLite

Tech Stack

- Backend: Python, FastAPI, SQLAlchemy, SQLite
- AI: OpenAI/OpenRouter via `openai` SDK (async)
- Frontend: Vue 3, Vite, Pinia, Tailwind CSS

Key Features

- Database-first word lookup; if not found, analyze via OpenAI and persist
- Suggestions when input is not a valid German word (user can pick one and continue)
- Sentence translation with gloss (DE/EN/ZH)
- Caching and search history

Getting Started

Prerequisites

- Python 3.10+
- Node.js 18+
- uv (Python package manager) – optional but recommended

Environment

1) Create and configure `.env` at the project root (do NOT commit it). You can use ` - Copy.env` as a template.
   - Required keys:
     - OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
     - DATABASE_URL (defaults to `sqlite:///./data/app.db`)

Install & Run – Backend

1) Install Python deps (using uv):
   uv sync

2) Start the API:
   uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

The database tables are created on startup. Logs are written to `uvicorn.out/err` when applicable.

Install & Run – Frontend

1) Install deps:
   cd frontend
   npm install

2) Start dev server:
   npm run dev

Vite dev server runs at http://localhost:3000 and proxies `/api/*` to the backend (see `vite.config.ts`).

Core API Endpoints

- Auth
  - POST `/auth/register`
  - POST `/auth/login`
- Translation / Search
  - POST `/translate/word` – database-first, OpenAI fallback
  - POST `/translate/word/select` – pick a suggested word and analyze it
  - POST `/translate/sentence` – sentence translation with gloss
  - GET  `/search/history` – recent searches

Search Behavior

1) Word search:
   - Look up in DB → if found, return immediately
   - If not found, call OpenAI to analyze and save to DB
   - If the input is not a valid German word, API returns `found=false` with up to 5 suggestions
2) Sentence translation:
   - Uses OpenAI; responses are cached

Scripts

- Data import and utilities are in `scripts/` and top-level helpers like `import_excel_vocabulary.py`, `preview_excel.py`, etc.

Testing

- Backend quick tests:
  uv run python -m pytest -q
- Or project runner:
  uv run python run_tests.py

Troubleshooting

- 401 from OpenAI/OpenRouter: check `.env` (API key / base URL / model)
- Frontend build errors (Vue template): ensure all tags are properly closed
- CORS: frontend uses Vite proxy; backend CORS settings are in `app/main.py`

Repository Hygiene

- Secrets: `.env` must never be committed
- Local artifacts: database files and node_modules should be ignored (see `.gitignore`)

License

Add your preferred license here.

# Vibe Deutsch - OpenAI-powered German Learning Platform

A modern German learning platform with intelligent caching, word analysis, and creative learning modules.

## Features (MVP)
- 🔍 Smart word search with OpenAI integration and caching
- 📖 DWDS-style dictionary with morphology tables
- 🌐 Multi-language translator (DE/EN/ZH)
- 📝 Search history tracking for personalized learning
- 🔐 JWT authentication system
- ⚡ Intelligent response caching to minimize API costs
- 📊 Excel vocabulary import with auto-completion of missing forms
- 🧠 Automatic verb conjugation and noun declension using OpenAI

## Tech Stack
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue 3 + Vite + TypeScript + TailwindCSS
- **AI**: OpenAI API (GPT-4o-mini)
- **Auth**: JWT tokens

## Setup (Windows with UV)

1. **Install UV** (if not already installed):
```bash
pip install uv
```

2. **Clone and setup**:
```bash
git clone <your-repo>
cd LanguageLearning
```

3. **Create virtual environment and install dependencies**:
```bash
uv venv
.venv\Scripts\activate
uv pip install -e .
```

4. **Environment setup**:
```bash
copy .env.example .env
# Edit .env with your OpenAI API key
```

5. **Initialize database**:
```bash
mkdir data
python -m app.db.init_db
```

6. **Import vocabulary from Excel files** (Optional):
```bash
# Double-click import_vocabulary.bat or run:
import_vocabulary.bat
```

7. **Run backend**:
```bash
# Double-click start.bat or run:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Run frontend** (in another terminal):
```bash
cd frontend
npm install
npm run dev
```

## API Documentation
After starting the backend, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure
```
/app
  /api          # API endpoints
  /core         # Config, security, dependencies
  /models       # SQLAlchemy models
  /schemas      # Pydantic schemas
  /services     # Business logic
  /db           # Database setup
/frontend       # Vue 3 application
/data           # SQLite database and uploads
```

## Vocabulary Import from Excel

The system supports importing German vocabulary from Excel files with automatic enhancement:

### Supported Excel Format
The importer expects Excel files with these columns:
- **German Word**: The German vocabulary (e.g., "der Tisch")
- **Article**: Article only (der/die/das)
- **Noun Only**: Base noun form
- **Translation**: English translation
- **Example Sentence**: German example sentence
- **Classification**: Word category/topic

### Import Process
1. **Place Excel files** in the root directory with names like:
   - `german_vocabulary_A1_sample.xlsx`
   - `german_vocabulary_A2_sample.xlsx`
   - `german_vocabulary_B1_sample.xlsx`

2. **Run import**: `import_vocabulary.bat`

3. **Auto-enhancement**: For each imported word, the system:
   - Adds Chinese translations using OpenAI
   - Generates complete verb conjugation tables
   - Creates noun declension forms
   - Validates and enhances existing data

### Manual Import Commands
```bash
# Preview Excel structure
python preview_excel.py

# Import with limit (for testing)
python scripts/improved_excel_importer.py

# Check database statistics
python scripts/vocabulary_manager.py stats
```

## Development Commands
```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black app/
isort app/

# Type checking
mypy app/
```