# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Development Information

### Demo Account
- **Email**: `demo@example.com`
- **Password**: `demo123`
- Use for testing authentication flows

### Windows Unicode Handling
When running Python scripts with German characters (ä, ö, ü, ß), use:
```bash
uv run python script.py 2>nul
# or
set PYTHONIOENCODING=utf-8 && uv run python script.py
```

## Development Commands

### Backend (FastAPI + SQLAlchemy + SQLite)
```bash
# Development server
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Package management
uv sync                                    # Install dependencies
uv add package_name                       # Add new dependency

# Testing
uv run python tests/run_tests.py         # All tests
uv run python tests/test_api_endpoints.py # Specific test file
uv run python tests/test_security_fixes.py # Security validation

# Vocabulary management
uv run python scripts/vocabulary_manager.py --help
uv run python scripts/excel_vocabulary_importer.py path/to/file.xlsx

# Debug translate mode issues (common debugging pattern)
uv run python test_translate_backend.py  # Test OpenAI translation services
uv run python debug_katze_db.py         # Debug specific word database issues
```

### Frontend (Vue 3 + TypeScript + Vite)
```bash
cd frontend

# Development (MUST use port 3000 for proxy configuration)
npm run dev

# Build and quality
npm run build
npm run lint

# Testing
npm run test             # Playwright E2E tests
npm run test:headed      # Tests with browser UI
npm run test:ui          # Playwright test UI
```

### Docker Deployment
```bash
# Full stack deployment
docker-compose up -d
docker-compose logs -f
docker-compose down

# Production build
docker build -t vibe-deutsch .
```

## Architecture Overview

### Core Architecture
- **Backend**: FastAPI + SQLAlchemy + SQLite with OpenAI integration via OpenRouter
- **Frontend**: Vue 3 Composition API + TypeScript + Pinia + Tailwind CSS
- **Security**: JWT with refresh tokens, security headers, rate limiting
- **AI Integration**: OpenAI GPT-4o-mini for chat, translation, analysis; DALL-E for images
- **Deployment**: Docker with multi-stage builds, NAS-ready configuration

### Key Service Architecture

**AI Integration Services:**
- `openai_service.py` - OpenAI API with caching and model routing
- `enhanced_search_service.py` - Multi-language search with AI fallback
- `lexicon_llm_service.py` - Advanced linguistic analysis

**Core Business Services:**
- `vocabulary_service.py` - Word management and database operations
- `srs_service.py` - Spaced repetition scheduling algorithm
- `exam_service.py` - Question generation and grading logic
- `cache_service.py` - Response caching for API cost optimization

### Database Design

**Core Models:**
- `WordLemma` - Base word forms with grammatical metadata
- `WordForm` - Inflected forms with feature_key/feature_value pairs
- `Translation` - Multi-language translations (German/English/Chinese)
- `User` - Authentication with role-based access

**Learning Models:**
- `SearchHistory` - User search tracking
- `SRSCard` - Spaced repetition with scheduling metadata
- `Exam`/`ExamQuestion` - Assessment system with scoring

### Authentication Architecture

**Security Implementation:**
- JWT access tokens (24h) + refresh tokens (30-90d)  
- Cookie-based auth with httpOnly, secure, sameSite protection
- Automatic token refresh 5min before expiry
- Security middleware: XSS, CSRF, clickjacking, rate limiting

**Frontend Auth Store (`stores/auth.ts`):**
- localStorage token management with automatic cleanup
- Axios request interceptors for 401 handling
- Multi-tab session synchronization

## Search System Architecture

**Multi-Stage Search Pipeline (`enhanced_search_service.py`):**

1. **Language Detection** - Pattern matching for Chinese/English/German inputs
2. **Cross-language Translation** - Non-German queries translated via OpenAI
3. **German Search Hierarchy**:
   - Direct lemma matching (exact word lookup)
   - Inflected form resolution (gehe → gehen)
   - Article stripping (der Tisch → Tisch)
   - Case-insensitive fuzzy matching
4. **AI Enhancement** - Unknown words analyzed via OpenAI with grammatical validation
5. **Similarity Ranking** - Levenshtein distance for suggestion ordering

**WordForm Flexible Schema:**
- `feature_key='tense'`, `feature_value='praesens_ich'` → `form='ich bringe'`
- `feature_key='article'`, `feature_value='article'` → `form='der'`
- `feature_key='tense'`, `feature_value='imperativ_du'` → `form='bring'`

## OpenAI Integration Architecture

**Centralized Service (`openai_service.py`):**
- Model routing: GPT-4o-mini via OpenRouter, direct DALL-E for images
- Response caching with `cache_service.py` for cost optimization  
- Structured JSON responses with Pydantic validation
- Graceful fallback behavior for API failures

**Key Integration Points:**
```python
# Word analysis with grammatical validation
await openai_service.analyze_german_word(word)

# Multi-language translation with confidence scoring
await openai_service.translate_to_german(text, source_lang) 

# Language detection with ambiguity handling
await openai_service.detect_language(text)

# Chat completion with structured JSON responses
await openai_service.chat_completion(messages, max_tokens=800, temperature=0.7)
```

**Critical OpenAI Integration Notes:**
- Updated `chat.py` uses structured JSON responses but no `response_format` parameter
- Language detection returns proper JSON `null` not string `"null"` values
- Translation service handles ambiguous words like "hell" (German=bright vs English=underworld)

## Frontend Architecture

**State Management (Pinia Stores):**
- `auth.ts` - JWT token lifecycle, user session management
- `favorites.ts` - Saved words with optimistic updates
- `search.ts` - Search history and recent query caching

**Key Components:**
- `WordResult.vue` - Three-column verb conjugation display (Präsens/Präteritum/Perfekt)
- `ChatModal.vue` - AI chat interface with conversation management and quick tips system
- `ImageModal.vue` - DALL-E image generation with style options
- `FavoriteButton.vue` - Optimistic UI updates with rollback handling

**Translate Mode Architecture:**
- **Language Detection**: OpenAI identifies input language with ambiguity handling
- **Translation Pipeline**: Multi-step process from source language to German to database search
- **Frontend Display Logic**: Different UI sections for ambiguous vs. non-ambiguous translations
- **Key Issue**: Ensure non-ambiguous translations display correctly in Home.vue (lines 165-178)

## Testing Architecture

**Test Coverage:**
- `test_api_endpoints.py` - Complete API endpoint validation
- `test_security_fixes.py` - Security middleware and auth validation  
- `test_live_api.py` - Integration tests against running development server
- `tests/run_tests.py` - Orchestrated test suite runner

**Frontend E2E Testing (Playwright):**
- Authentication flows with persistent sessions
- Word search and AI chat interactions
- Image generation and modal functionality
- Cross-browser compatibility testing

## Environment Configuration

**Essential Variables (.env):**
```bash
# OpenAI Integration (required)
OPENAI_API_KEY=your_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1  
OPENAI_MODEL=openai/gpt-4o-mini

# Security (generate secure key for production)
SECRET_KEY=your_32_character_secret_key

# Database
DATABASE_URL=sqlite:///./data/app.db

# CORS (for ZeroTier or custom network deployments)
ADDITIONAL_ALLOWED_HOSTS=http://10.0.0.100:8000,https://nas.local:8000
```

**Deployment-Specific Settings:**
- `HTTPS_ONLY=false` for HTTP NAS deployments
- `ENVIRONMENT=production` triggers security validation
- Volume mount `./data:/app/data` for database persistence

## Production Vocabulary Management

**Modern Vocabulary Tools (scripts/):**
```bash
# Production-ready vocabulary management
uv run python scripts/vocabulary_manager.py --help

# Excel import with validation
uv run python scripts/excel_vocabulary_importer.py file.xlsx

# PDF processing for dictionaries
uv run python scripts/pdf_vocabulary_importer.py collins.pdf
```

**Development Tools (archived in archive/dev-tools/):**
- Database repair and validation scripts
- Collins dictionary processing tools  
- Historical fix scripts for reference

## Deployment Architecture

**Docker Production:**
- Multi-stage build with Node.js frontend build + Python FastAPI backend
- SQLite database with volume persistence (`./data:/app/data`)
- Security headers and rate limiting enabled
- Health checks and graceful shutdown handling

**NAS Deployment:**
- Single-port configuration (port 8000) for simplified networking
- HTTP-compatible authentication for local network access
- ZeroTier network support via `ADDITIONAL_ALLOWED_HOSTS`
- Container Manager GUI deployment (see `MD/deployment/` guides)

## Development Patterns

**Adding API Features:**
1. Define Pydantic schemas in `app/schemas/`
2. Implement business logic in appropriate service (`app/services/`)
3. Create FastAPI router in `app/api/`
4. Add comprehensive tests in `tests/`
5. Update API documentation

**Frontend Development:**
1. Create/update Pinia stores for state management
2. Implement TypeScript Vue components with proper typing
3. Add routes and authentication guards
4. Create Playwright E2E tests for critical flows

**Database Schema Evolution:**
1. Update SQLAlchemy models in `app/models/`
2. Test changes with existing data using vocabulary tools
3. Validate with comprehensive test suite

## Common Debugging Patterns

**Translate Mode Issues:**
1. Test backend with `test_translate_backend.py` to verify OpenAI responses
2. Check database for word conflicts with `debug_katze_db.py`
3. Verify frontend display logic in `Home.vue` translate sections (lines 148-184)
4. Common issue: Non-ambiguous translations not displaying due to missing UI logic

**Unicode/Encoding Issues:**
- Windows: Use `2>nul` or `set PYTHONIOENCODING=utf-8` for German/Chinese characters
- Database: Check for similar words causing search confusion (e.g., "Katze" vs "Catcher")

**Chat System Issues:**
- Verify `openai_service.chat_completion()` doesn't use unsupported `response_format` parameter
- Check structured response parsing in `ChatModal.vue` for proper JSON handling

## Documentation Structure

**Organized Documentation (MD/):**
- `deployment/` - Docker, NAS, and network deployment guides
- `security/` - Security implementation and fix documentation
- `development/` - Search logic, German language processing guides
- `reference/` - Project architecture and feature specifications