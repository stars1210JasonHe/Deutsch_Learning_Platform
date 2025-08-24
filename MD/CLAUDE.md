# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Testing Information

### Test Account Credentials
- **Email**: `heyeqiu1210@gmail.com`
- **Password**: `123456`
- Always use these credentials for all testing in this project

### Unicode Encoding Fix for Windows
- When running Python scripts that contain German characters (ä, ö, ü, ß), always append `2>nul` to suppress Unicode encoding errors
- Example: `uv run python script.py 2>nul`
- Alternative: `set PYTHONIOENCODING=utf-8 && uv run python script.py`

## Development Commands

### Backend (Python + FastAPI)
```bash
# Start development server
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Install dependencies
uv sync

# Run specific test
uv run python tests/test_api_endpoints.py
uv run python tests/test_live_api.py
uv run python tests/test_openai_functions.py

# Run all tests
uv run python tests/run_tests.py

# Database operations
uv run python scripts/checks/inspect_database.py
uv run python scripts/fixes/enhanced_database_fixer.py --mode all
uv run python scripts/import_excel_vocabulary.py

# PDF Processing
# Split large PDF files into smaller 50-page chunks
uv run python split_pdf.py large_dictionary.pdf
uv run python split_pdf.py large_dictionary.pdf --pages 25 --output-dir split_files
uv run python split_pdf.py large_dictionary.pdf --info  # Show PDF info only

# Verb conjugation fixes (created during development)
set PYTHONIOENCODING=utf-8 && uv run python fix_all_verbs_comprehensive.py
set PYTHONIOENCODING=utf-8 && uv run python fix_bringen_specifically.py
set PYTHONIOENCODING=utf-8 && uv run python fix_missing_imperativ.py

# Code quality
black app/ tests/
isort app/ tests/
mypy app/

# Development dependencies (for code quality tools)
uv sync --group dev
```

### Frontend (Vue 3 + TypeScript)
```bash
# Navigate to frontend and start dev server (MUST run on port 3000)
cd frontend && npm run dev

# Build for production
npm run build

# Lint and fix
npm run lint

# Install dependencies
npm install

# E2E Testing with Playwright
npm run test              # Run all Playwright tests
npm run test:headed       # Run tests with browser UI visible
npm run test:ui           # Run tests with Playwright UI interface

# IMPORTANT: Frontend MUST run on port 3000
# If port 3000 is occupied, kill the process first:
# netstat -ano | findstr ":3000"
# tasklist /fi "PID eq [PID_NUMBER]"
# taskkill /f /pid [PID_NUMBER]
```

### Docker Deployment
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f vibe-deutsch

# Stop services
docker-compose down

# Single container deployment (for Synology NAS)
# See DEPLOY-DOCKER-SINGLE.md and DEPLOY-SYNOLOGY.md for detailed instructions
docker build -t vibe-deutsch .
docker run -d --name vibe-deutsch -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data vibe-deutsch
```

## Architecture Overview

### Backend Stack
- **FastAPI** - REST API with automatic OpenAPI docs
- **SQLAlchemy** - ORM with SQLite database
- **Pydantic** - Data validation and settings management
- **UV** - Modern Python package management
- **JWT Authentication** - Access + refresh tokens with 24h/90d expiry

### Frontend Stack
- **Vue 3** - Composition API with TypeScript
- **Pinia** - State management (auth, favorites, search)
- **Vue Router** - Client-side routing
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client with interceptors

### Service Layer Architecture

The backend uses a service-oriented architecture with specialized services:

- **`enhanced_search_service.py`** - Multi-language search with AI fallback
- **`vocabulary_service.py`** - Core word management and database operations  
- **`openai_service.py`** - OpenAI API integration with caching
- **`lexicon_llm_service.py`** - Advanced linguistic analysis
- **`cache_service.py`** - Response caching to minimize API costs
- **`srs_service.py`** - Spaced repetition system
- **`exam_service.py`** - Question generation and grading

### Database Models

The database follows a normalized design:

- **`WordLemma`** - Base word forms (gehen, Tisch)
- **`WordForm`** - Inflected forms (gehe, Tisches) with grammatical features
- **`Translation`** - Multi-language translations (en, zh)
- **`Example`** - Usage examples in German with translations
- **`User`** - Authentication and user management
- **`SearchHistory`** - User search tracking
- **`SRSCard`** - Spaced repetition cards with scheduling
- **`Exam`** + **`ExamQuestion`** - Assessment system

### Authentication Flow

The authentication system uses a dual-token approach:
1. **Access Token** (24h) - API authorization 
2. **Refresh Token** (30d/90d) - Token renewal
3. **Auto-refresh** - Frontend automatically refreshes tokens
4. **Persistent sessions** - "Remember me" extends refresh to 90 days

Frontend auth store (`stores/auth.ts`) handles:
- Token storage in localStorage
- Automatic token refresh 5min before expiry  
- Request interceptors for 401 handling
- Multi-tab synchronization

## Enhanced Search System

The search system (`enhanced_search_service.py`) implements a sophisticated pipeline:

1. **Language Detection** - Chinese, English, German pattern matching
2. **Cross-language Translation** - Non-German inputs translated via OpenAI
3. **Multi-level German Search**:
   - Direct lemma matching
   - Inflected form lookup (gehe → gehen)
   - Article removal (der Tisch → Tisch)  
   - Compound word variations
   - Case-insensitive matching
4. **AI Fallback** - OpenAI analysis for unknown words with validation
5. **Real-time Completion** - Incomplete words automatically enhanced via OpenAI during search
6. **Similarity Scoring** - Levenshtein distance with ranked suggestions

### WordForm Data Structure
The system uses a flexible `WordForm` model with `feature_key` and `feature_value` pairs:
- **Tense forms**: `feature_key='tense'`, `feature_value='praesens_ich'`, `form='ich bringe'`
- **Articles**: `feature_key='article'`, `feature_value='article'`, `form='der'`
- **Imperativ**: `feature_key='tense'`, `feature_value='imperativ_du'`, `form='bring'`

## OpenAI Integration Patterns

### Service Configuration
All OpenAI calls go through `openai_service.py` with:
- Model selection (default: gpt-4o-mini via OpenRouter)
- Response caching via `cache_service.py`
- Structured JSON responses with validation
- Error handling and fallback behavior

### Common Usage Patterns
```python
# Word analysis with validation
analysis = await openai_service.analyze_german_word(word)

# Translation with confidence scoring  
translation = await openai_service.translate_to_german(text, source_lang)

# Example generation
example = await openai_service.generate_example(word, context)
```

## Frontend State Management

### Store Structure
- **`auth.ts`** - User authentication, token management
- **`favorites.ts`** - Saved words with local caching
- **`search.ts`** - Search history, recent queries

### Component Patterns
- **`WordResult.vue`** - Clean UI showing word, meaning, and conjugation tables (Präsens, Präteritum, Perfekt, Imperativ)
- **`EnhancedWordResult.vue`** - Advanced search results with suggestions
- **`FavoriteButton.vue`** - Toggle word favorites with optimistic updates
- **`SpeechButton.vue`** - Text-to-speech integration

### UI Layout for Verbs
The word display follows a clean three-column layout for essential conjugations:
- **Column 1**: Präsens (Present) - blue styling
- **Column 2**: Präteritum (Simple Past) - green styling  
- **Column 3**: Perfekt (Present Perfect) - purple styling
- **Imperativ**: Separate teal-styled section for commands (du, ihr, Sie forms)

## Testing Strategy

### API Testing
- **`test_api_endpoints.py`** - Full endpoint coverage
- **`test_live_api.py`** - Integration tests against running server
- **`test_api_directly.py`** - Authentication flow testing

### Service Testing  
- **`test_openai_functions.py`** - OpenAI service mocking
- **`test_vocabulary_service.py`** - Database operations
- **`test_translation_fixes.py`** - Search accuracy validation

### Running Tests
Run tests against a development server with proper OpenAI API keys configured.

## Environment Configuration

### Required Variables
```bash
# OpenAI (required)
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Database
DATABASE_URL=sqlite:///./data/app.db

# Security (change in production)
SECRET_KEY=your_32_character_key
```

### Development vs Production
- Development uses HTTP CORS for localhost:3000
- Production requires SSL/TLS setup
- Docker deployment uses volume mounts for persistent data
- OpenRouter recommended for cost efficiency

## Database Operations

### Vocabulary Import
```bash
# Excel import with auto-enhancement
uv run python scripts/import_excel_vocabulary.py

# Database validation and fixing
uv run python scripts/fixes/enhanced_database_fixer.py --mode all

# Check for incomplete entries
uv run python scripts/checks/check_incomplete_words.py
```

### Schema Migrations
Database schema is managed through SQLAlchemy models. Changes require:
1. Update model definitions in `app/models/`
2. Create Alembic migration (if using migrations)
3. Test with `enhanced_database_fixer.py` for data integrity

## Deployment Considerations

### Docker Production
- Uses SQLite with volume persistence
- 4GB memory limit for optimal performance  
- Health checks on `/docs` endpoint
- Resource constraints for shared environments

### Synology NAS
- GUI-based Container Manager deployment
- Port 8000 exposure for web interface
- Volume mounting for data persistence
- Environment variable configuration through UI

## Common Development Patterns

### Adding New API Endpoints
1. Define Pydantic schemas in `app/schemas/`
2. Implement service logic in appropriate service class
3. Create FastAPI router in `app/api/`
4. Include router in `app/main.py`
5. Add tests in `tests/`

### Frontend Feature Addition
1. Create/update Pinia store for state management
2. Implement Vue components with TypeScript
3. Add routes in `frontend/src/router/`
4. Update navigation and authentication guards
5. Add Playwright E2E tests in `frontend/tests/`

### Database Model Changes
1. Modify SQLAlchemy models in `app/models/`
2. Update related services for new fields
3. Run database validation scripts
4. Test import/export functionality

## Verb Conjugation System

### Essential Conjugation Forms
All verbs should have complete conjugation data:
- **Präsens**: 6 forms (ich, du, er_sie_es, wir, ihr, sie_Sie)
- **Präteritum**: 6 forms (ich, du, er_sie_es, wir, ihr, sie_Sie)  
- **Perfekt**: 6 forms (ich, du, er_sie_es, wir, ihr, sie_Sie)
- **Imperativ**: 3 forms (du, ihr, Sie)

### Conjugation Fix Scripts
When verbs are missing conjugations:
1. **Individual fixes**: Use `fix_bringen_specifically.py` as template
2. **Comprehensive fixes**: Run `fix_all_verbs_comprehensive.py` to check ALL 140+ verbs
3. **Real-time fixes**: Search service automatically completes incomplete words via OpenAI

### Unicode Handling
Always use `set PYTHONIOENCODING=utf-8` before running Python scripts on Windows to handle German characters (ä, ö, ü, ß) properly.

## Additional Resources

### Deployment Documentation
- **`DEPLOY-SYNOLOGY.md`** - Complete GUI-based deployment guide for Synology NAS
- **`DEPLOY-DOCKER-SINGLE.md`** - Single container deployment without docker-compose
- **`README.md`** - Project overview and quick start guide

### Project Analysis Files
- **`SEARCH-LOGIC-COMPLETE.md`** - Detailed search system implementation analysis
- **`SEARCH-LOGIC-FIX.md`** - Search system debugging and fixes
- **`SEARCH-QUESTIONS-ANSWERS.md`** - FAQ about search functionality

### Docker Configuration Files
- **`Dockerfile`** - Multi-stage production build
- **`Dockerfile.standard`** - Alternative Docker configuration
- **`docker-compose.yml`** - Orchestrated multi-service deployment
- **`.dockerignore`** - Files excluded from Docker build context

### Quick Deployment Scripts
```bash
# Run deployment scripts (if available)
./docker-run.sh    # Start containers
./docker-stop.sh   # Stop containers
```