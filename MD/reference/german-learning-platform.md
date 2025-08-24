# Vibe Deutsch: OpenAI-powered German Learning Platform — Technical Spec (FastAPI + SQLite + Vue)

> Author: Jason He  
> Date: 2025‑08‑11  
> Goal: Build a DWDS‑style dictionary + practice site with an exam generator & auto‑checking. Backend in **Python/FastAPI**, **SQLite** DB, modern **Vue 3** frontend. Integrate **OpenAI API** for translations, morphology tables, and dynamic exercises with intelligent word search caching and user history tracking.

---

## 1) Product Overview

### 1.1 Target users
- **Beginners–intermediate (A1–B2):** need fast lookups, conjugations/declensions, sample sentences, audio.  
- **Exam takers (e.g., Goethe/ÖSD, telc):** need auto‑generated practice exams with grading and analytics.
- **Power learners:** want spaced repetition, custom word lists, and grammar drills.

### 1.2 Core value
1) **DWDS‑like word pages** with intelligent caching (definitions, POS, examples, synonyms, frequency, etymology*), 2) **Translator Mode** matching your exact workflow rules, 3) **Exam Mode**: generate tasks (fill‑in‑the‑blank, MCQ, cloze, writing), auto‑check, detailed feedback, 4) **Smart Search**: cached results for performance and user search history tracking.

\*Etymology/frequency can start minimal and expand later using public datasets or curated content you create; avoid scraping third‑party copyrighted data.

---

## 2) Feature Set

### 2.1 Smart Word Search & Caching
- **Intelligent Search**: OpenAI-powered word lookup with fuzzy matching and context awareness
- **Result Caching**: All OpenAI API responses cached in database to avoid duplicate API calls
- **Search History**: User-specific search history with timestamps and frequency tracking
- **Fast Retrieval**: Cached results return instantly for previously searched words
- **Analytics**: Track most searched words, user patterns, and optimize content accordingly

### 2.2 Dictionary (DWDS‑style) Word Page
- **Header:** lemma, IPA & audio (TTS), CEFR tag, frequency bar.
- **Tabs:**  
  - **Meaning/Usage:** short definition(s), register, collocations.
  - **Grammar:** gender/article for nouns; plural; verb conjugation (Präsens, Präteritum, Perfekt, Futur I), Partizip II, auxiliary (haben/sein). Adjective endings table.
  - **Examples:** graded sentences with translations, highlight target word.
  - **Synonyms/Antonyms:** editable curated list.
  - **Word formation:** stems, compounds, prefixes/suffixes.
  - **Notes/Etymology:** hand‑curated notes you add over time.
- **Actions:** “Add to List”, “Practice”, “Make exercise from this word”, “Report issue”.

### 2.3 Translator Mode (exact behavior you requested)
**If user sends:**  
- **A single word (DE/EN/ZH) →** return **both English & Chinese** translations for German words, or **German word** for EN/ZH. Include:
  - **Part of speech**; **for verbs**: full table (ich, du, er/sie/es, wir, ihr, sie/Sie) in **Präsens** & **Präteritum**, **Perfekt** (aux + Partizip II), **Futur I**.  
  - **For nouns**: **article (der/die/das)** + **plural**.  
  - **One example sentence** (DE + EN + ZH).
- **A sentence (EN/ZH) →** first give **German translation**, then **word‑by‑word gloss** (each token → EN + ZH), note separable prefixes & cases.  
- **Meta‑rule:** Always show original input + translation(s) **side by side**.

**UI sketch:** left (original), right (translations + tables), with “Copy,” “Save,” “Practice.”

### 2.4 Exam Mode
- **Generation:** User picks CEFR level, topics, grammar focus; LLM returns a **structured JSON exam** with keys: `sections`, `questions`, `answers`, `metadata`.
- **Question types:** MCQ, **Fill‑in‑the‑blank/cloze**, matching, sentence reordering, short writing, listening (TTS).  
- **Auto‑check:** exact match, **fuzzy** tolerance (Levenshtein/ratio), normalization (case, umlauts, punctuation), **morphology‑aware** equivalence (e.g., akzeptiere *dem/den* depending on case in cloze with alternatives).  
- **Feedback:** show expected answer, user answer, diff highlight, grammar note, link to word pages.  
- **Analytics:** per grammar topic accuracy, confusion words, time per item, suggested next steps.
- **Review deck:** misses go to SRS (Leitner or SM‑2 simplified).

### 2.5 Lists & SRS
- User word lists, tags, due queue, streaks, “Practice now” by deck/topic/CEFR.

### 2.6 Accounts & Roles
- Anonymous demo; signup with email/password or “local only”.  
- Roles: user, editor (curate content), admin.

---

## 3) Modular Architecture

```
Vue 3 Frontend (Vite/Tailwind/Pinia/Router)
  ├─ Core Components (Search, Dictionary, Translate)  
  ├─ Creative Modules (Drawing, Vision, Word Explorer)
  └─ Game Modules (Tetris, Runner, Mini-Games)
        │
        ▼  HTTPS JSON (JWT)
FastAPI Backend (Python 3.11+)
  ├─ Core Routers: /auth /words /translate /history
  ├─ Creative Routers: /draw /vision /word-family /export  
  ├─ Game Routers: /games /leaderboard
  ├─ Services: 
  │   ├─ Core: OpenAI, Cache, Auth, Search
  │   ├─ Creative: Vision, Canvas, WordRelations
  │   └─ Media: FileStorage, ImageProcessing, PDFGen
  ├─ DB: SQLite + File Storage (images, audio, exports)
  └─ Tasks: Redis Queue (heavy processing, image gen)
```

### 3.1 Modular Design Principles
- **Plugin Architecture**: Each creative module can be enabled/disabled
- **Shared Services**: Core OpenAI and caching services reused across modules
- **Media Pipeline**: Unified file upload/processing for images, audio, exports
- **Feature Flags**: Toggle experimental features per user/environment

### 3.2 Core Infrastructure  
- **OpenAI Integration:** Direct API client with Vision support for creative modules
- **Smart Caching:** All API responses cached, including vision analysis results
- **Search History:** Enhanced with module usage tracking and learning analytics
- **Task Queue:** Redis-based async processing for heavy operations (image analysis, PDF generation)
- **File Storage:** Local file system with optional cloud storage integration

---

## 4) Tech Stack

- **Frontend:** Vue 3 + Vite + TypeScript + TailwindCSS + Pinia + Vue Router + Konva.js (Canvas) + D3.js (Visualizations)
- **Backend:** FastAPI, Pydantic, SQLAlchemy, Uvicorn  
- **DB:** SQLite (with WAL mode) + intelligent caching layer  
- **LLM:** OpenAI API (GPT-4o-mini + Vision API for creative modules)  
- **Queue:** Redis (async tasks) + Celery (background processing)
- **Media:** Pillow (image processing) + ReportLab (PDF generation)
- **Auth:** JWT (PyJWT) + password hashing (passlib/argon2)  
- **Testing:** pytest + httpx + Playwright (frontend e2e)  
- **Migrations:** Alembic (even with SQLite)

Project layout:

```
/app
  /api
    /core: auth.py, words.py, translate.py, history.py
    /creative: draw.py, vision.py, word_family.py, export.py
    /games: mini_games.py, leaderboard.py
  /core
    config.py, security.py, deps.py, feature_flags.py
  /models
    /core: user.py, word.py, lemma.py, search_cache.py, search_history.py
    /creative: scene.py, vision_analysis.py, word_relation.py
    /shared: audit.py, file_storage.py
  /schemas
    *.py (Pydantic schemas for all modules)
  /services
    /core: openai_service.py, cache_service.py, auth_service.py
    /creative: vision_service.py, canvas_service.py, export_service.py
    /media: file_service.py, image_processor.py, pdf_generator.py
  /tasks
    background_tasks.py, queue_processor.py
  /db
    base.py, session.py
/frontend  (Vue app)
  /core: search, dictionary, translate
  /creative: drawing-lab, vision-analyzer, word-explorer
  /games: mini-games components
/data
  app.db, uploads/, exports/, cache/
```

---

## 5) Database Schema (SQLite)

### 5.1 Tables (ER overview)
- **users**(id, email, password_hash, role, created_at)  
- **word_lemmas**(id, lemma, pos, cefr, ipa, freq, notes)
- **word_forms**(id, lemma_id→word_lemmas.id, form, feature_key, feature_val)  
  - e.g., `("POS","verb"),("tense","praesens"),("person","ich")`
- **translations**(id, lemma_id, lang_code, text, source)  // EN/zh‑CN
- **examples**(id, lemma_id, de_text, en_text, zh_text, level)
- **synonyms**(id, lemma_id, text)
- **lists**(id, user_id, name, description)
- **list_items**(id, list_id, lemma_id)
- **exams**(id, user_id, title, level, spec_json, created_at)
- **exam_questions**(id, exam_id, qtype, prompt, options_json, answer_json, rubric_json)
- **attempts**(id, user_id, exam_id, started_at, finished_at, score)
- **attempt_items**(id, attempt_id, question_id, user_answer_json, correct, feedback)
- **srs_cards**(id, user_id, lemma_id, due_at, interval, ease)
- **search_cache**(id, query_text, query_type, response_json, created_at, hit_count)
- **search_history**(id, user_id, query_text, query_type, cached_result_id, timestamp)
- **scenes**(id, user_id, svg_data, image_url, prompt, objects_json, created_at)
- **scene_attempts**(id, user_id, scene_id, answers_json, score, feedback_json)
- **vision_analyses**(id, image_hash, analysis_json, language_level, created_at, hit_count)
- **word_relations**(id, parent_lemma_id, child_lemma_id, relation_type, strength)
- **exports**(id, user_id, export_type, file_path, created_at, download_count)
- **feature_usage**(id, user_id, feature_name, usage_count, last_used)
- **audit_logs**(id, user_id, action, entity, entity_id, meta_json, ts)

### 5.2 Example SQLAlchemy models (excerpt)

```python
# app/models/word.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class WordLemma(Base):
    __tablename__ = "word_lemmas"
    id = Column(Integer, primary_key=True)
    lemma = Column(String, index=True, unique=True, nullable=False)  # e.g., "gehen"
    pos = Column(String, index=True)   # "verb"|"noun"|"adj"|...
    cefr = Column(String)              # "A1".."C2"
    ipa = Column(String)
    freq = Column(Integer, default=0)
    notes = Column(Text)

    forms = relationship("WordForm", back_populates="lemma", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="lemma", cascade="all, delete-orphan")
    examples = relationship("Example", back_populates="lemma", cascade="all, delete-orphan")

class WordForm(Base):
    __tablename__ = "word_forms"
    id = Column(Integer, primary_key=True)
    lemma_id = Column(Integer, ForeignKey("word_lemmas.id", ondelete="CASCADE"), index=True)
    form = Column(String, index=True)  # "gegangen", "ich gehe", "die Tische", etc.
    feature_key = Column(String)       # "tense","person","number","case","gender"
    feature_val = Column(String)       # "praesens","ich","plural","akk","masc"

    lemma = relationship("WordLemma", back_populates="forms")

class Translation(Base):
    __tablename__ = "translations"
    id = Column(Integer, primary_key=True)
    lemma_id = Column(Integer, ForeignKey("word_lemmas.id", ondelete="CASCADE"), index=True)
    lang_code = Column(String, index=True)  # "en","zh"
    text = Column(Text)
    source = Column(String, default="human")

    lemma = relationship("WordLemma", back_populates="translations")

class Example(Base):
    __tablename__ = "examples"
    id = Column(Integer, primary_key=True)
    lemma_id = Column(Integer, ForeignKey("word_lemmas.id", ondelete="CASCADE"), index=True)
    de_text = Column(Text, nullable=False)
    en_text = Column(Text)
    zh_text = Column(Text)
    level = Column(String, default="A1")

    lemma = relationship("WordLemma", back_populates="examples")
```

---

## 6) API Design (FastAPI)

### 6.1 Auth
```
POST /auth/register   { email, password }
POST /auth/login      { email, password } → { access_token, token_type:"bearer" }
GET  /auth/me         (JWT)
```

### 6.2 Dictionary & Search
```
GET  /words/?q=gehen&lang=de        → search lemmas/forms (with caching)
GET  /words/{lemma}                 → full DWDS‑style payload
POST /words/                        → (editor) create/edit lemma, forms, examples
GET  /search/history                → user's search history
DELETE /search/history/{id}         → delete search history item
GET  /search/cache/stats            → cache hit rate and popular searches
```

### 6.3 Creative Modules (Phase 1)
```
# Drawing Lab
POST /draw/scene                    { svg_data?, image?, prompt?, level? } → scene analysis
GET  /draw/scenes                   → user's saved scenes
POST /draw/{scene_id}/practice      { answers } → grammar practice feedback

# Vision Analysis  
POST /vision/analyze               { image, level?, focus? } → German description + vocab
GET  /vision/history               → user's analyzed images
POST /vision/practice              { analysis_id, answers } → cloze/vocab practice

# Word Family Explorer
GET  /word-family/{lemma}          → word relations tree (compounds, derivatives)
POST /word-family/relations        { lemma_ids } → create custom study list
GET  /word-family/popular          → most explored word families

# Export Functions
POST /export/anki                  { list_id, format? } → Anki deck download
POST /export/pdf                   { content_type, filters } → PDF worksheet
GET  /export/history               → user's export history
```

**Payload (GET /words/gehen)** (sample):
```json
{
  "lemma": "gehen",
  "pos": "verb",
  "ipa": "ˈɡeːən",
  "cefr": "A1",
  "frequency": 9821,
  "grammar": {
    "aux": "sein",
    "partizip_ii": "gegangen",
    "praesens": {"ich":"gehe","du":"gehst","er_sie_es":"geht","wir":"gehen","ihr":"geht","sie_Sie":"gehen"},
    "praeteritum": {"ich":"ging","du":"gingst","er_sie_es":"ging","wir":"gingen","ihr":"gingt","sie_Sie":"gingen"},
    "perfekt": "ist gegangen",
    "futur1": {"ich":"werde gehen", "du":"wirst gehen", "...":"..."}
  },
  "translations": {"en":["to go"],"zh":["去","走"]},
  "examples": [
    {"de":"Ich gehe nach Hause.","en":"I am going home.","zh":"我回家。","level":"A1"}
  ],
  "synonyms":["laufen (teilw.)","sich begeben"]
}
```

### 6.4 Translator Mode
```
POST /translate/word        { "input": "Tisch" } → EN+ZH, noun details, example
POST /translate/sentence    { "input": "I like German." } → DE first, then per‑word gloss (EN+ZH)
```
- Always echo **original**; return **both EN & ZH**; for verbs include **full tables**; nouns include **article & plural**.

### 6.5 Exam Mode
```
POST /exam/generate    { level:"A2", topics:["Alltag"], types:["cloze","mcq"], count:20 }
POST /exam/{id}/start
POST /exam/{id}/submit    { answers:[...] }  → autocheck + feedback
GET  /exam/{id}/results
```
- Generation returns **exam JSON** (see §7).  
- Submit: server grades via **grading service** (fuzzy + morphology‑aware).

### 6.6 Practice & SRS
```
POST /srs/add          { lemma:"Tisch" }
GET  /srs/next         → due items
POST /srs/answer       { card_id, quality:0..5 } → update interval/ease
```

---

## 7) OpenAI Integration & Caching

### 7.1 OpenAI Client with Smart Caching
```python
class OpenAIService:
    async def get_word_analysis(self, word: str, from_cache: bool = True) -> dict: ...
    async def translate_sentence(self, sentence: str, from_cache: bool = True) -> dict: ...
    async def generate_exam(self, spec: dict, from_cache: bool = False) -> dict: ...
    async def cache_response(self, query: str, query_type: str, response: dict) -> int: ...
```
- **Cache-first approach**: Check SQLite cache before making OpenAI API calls
- **Cost optimization**: Track API usage and implement intelligent caching strategies
- **Search analytics**: Log all searches for user history and system analytics

### 7.2 Prompt templates

**Translator — single word**
```
System: You are a precise German language assistant.
User: Input: "{token}"
Task: If it's a German word, return:
- part of speech; for verbs: full conjugation (Präsens, Präteritum, Perfekt: aux + Partizip II, Futur I);
- for nouns: article (der/die/das) + plural form.
- English and Chinese translations (arrays)
- One example sentence (DE + EN + ZH)
Return JSON with keys: pos, tables, translations_en, translations_zh, example.
```

**Sentence translator**
```
System: You produce accurate German translations and word-by-word gloss.
User: Input sentence: "{sentence}"
1) Provide German translation first.
2) Provide per-token gloss array: [{de, en, zh, note?}].
Return JSON { german, gloss[] }.
```

**Exam generator**
```
System: You create CEFR-aligned German exams with strict JSON.
User: Level: {level}; Topics: {topics}; Types: {types}; Count: {count}.
Return:
{ "sections":[
   {"title":"...", "questions":[
      {"id":"q1","type":"cloze","prompt":"...", "blanks":[{"id":"b1","alternatives":["dem","den"]}], "answer":{"b1":["dem"]},"explanation":"case rule..."},
      {"id":"q2","type":"mcq","prompt":"...", "options":["A","B","C","D"], "answer":[1], "explanation":"..."}
   ]}
], "metadata":{"level":"A2"}}
```

---

## 8) Grading Logic

- **Normalization:** trim, lowercase (but keep ß/umlauts), strip punctuation variants; map `ae→ä` etc. for tolerant compare.  
- **Exact or set‑membership:** accept any in `alternatives`.  
- **Fuzzy:** Levenshtein ratio ≥ 0.9 → “typo” correct‑with‑warning.  
- **Morphology‑aware:** detect same lemma + correct features (case/number/person) using `word_forms` & simple rules.  
- **Writing items:** rubric keywords matched ± synonyms (LLM judge as secondary).  
- **Feedback payload:** expected, got, correct:boolean, notes, links to `/words/{lemma}`.

---

## 9) Frontend (Vue 3)

### 9.1 Pages
- **/ (Search)** global search bar → results by lemma/form.  
- **/word/:lemma** DWDS‑style tabs.  
- **/translator** follows rules: side‑by‑side original & translations, conjugations/declensions table.  
- **/exam/new** (wizard), **/exam/:id** (take), **/exam/:id/results**.  
- **/lists**, **/practice** (SRS queue), **/profile**.

### 9.2 Components
- `WordHeader` (lemma, IPA, CEFR, actions)  
- `ConjugationTable`, `DeclensionTable`, `ExamplesList`  
- `TranslatorPanel` (original ↔ translations)  
- `ExamRenderer` (MCQ, cloze, drag‑reorder)  
- `ResultCard` (diff + notes)  
- `SRSQueue`

### 9.3 Styling & UX
- Tailwind; responsive 2‑column layout on desktop, stacked on mobile.  
- Keyboard shortcuts for exams (1..4 for MCQ; Tab/Enter for blanks).  
- Dark mode toggle.

---

## 10) Example FastAPI Endpoints (MVP)

```python
# app/api/translate.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.llm import llm_word, llm_sentence

router = APIRouter(prefix="/translate", tags=["translate"])

class WordIn(BaseModel):
    input: str

@router.post("/word")
async def translate_word(body: WordIn):
    # 1) detect language/simple heuristics
    token = body.input.strip()
    data = await llm_word(token)  # returns JSON per §7.2
    return {"original": token, **data}

class SentIn(BaseModel):
    input: str

@router.post("/sentence")
async def translate_sentence(body: SentIn):
    sent = body.input.strip()
    data = await llm_sentence(sent)
    return {"original": sent, **data}
```

```python
# app/api/exam.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm import llm_exam
from app.services.grading import grade_attempt

router = APIRouter(prefix="/exam", tags=["exam"])

class ExamSpec(BaseModel):
    level: str = "A2"
    topics: list[str] = []
    types: list[str] = ["cloze","mcq"]
    count: int = 20

@router.post("/generate")
async def generate_exam(spec: ExamSpec):
    exam = await llm_exam(spec.dict())
    # save exam JSON to DB, return id
    return {"exam": exam}

class SubmitIn(BaseModel):
    answers: list[dict]

@router.post("/{exam_id}/submit")
async def submit_exam(exam_id: int, body: SubmitIn):
    graded = await grade_attempt(exam_id, body.answers)
    return graded
```

---

## 11) Data Seeding

- Start with 300–500 high‑frequency lemmas (A1/A2).  
- For each: article/pos, plural or verb tables, 2–3 examples (EN+ZH), 3–5 synonyms.  
- Write a `seed.py` script to import from CSV.  
- TTS: pre‑generate MP3s for examples (optional).

---

## 12) Deployment

- **Local dev (Windows 10):**
  - `python -m venv .venv && .venv\Scripts\activate`
  - `pip install -r requirements.txt`
  - `uvicorn app.main:app --reload`
  - Frontend: `npm i && npm run dev`

- **VPS (Ubuntu):**
  - `uvicorn` behind `nginx` (proxy, TLS), or `Caddy` for auto‑TLS.
  - Enable SQLite WAL; frequent backups of `/data/app.db`.
  - Set env vars: `LLM_ENDPOINT`, `LLM_API_KEY`, `JWT_SECRET`.

---

## 13) Security & Privacy

- Hash passwords; short JWT lifetimes + refresh.  
- Rate‑limit `/translate` & `/exam/generate`.  
- Log admin/editor changes (audit).  
- Avoid scraping licensed content; curate or use permissive sources.  
- Export/delete my data (GDPR friendly).

---

## 14) Testing

- Unit tests for grading normalization & morphology mapping.  
- Contract tests for exam JSON schema.  
- Snapshot tests for conjugation tables.  
- E2E: create exam → submit → verify score and feedback.

---

## 15) Roadmap

1. **MVP Core (4–6 weeks):** OpenAI-powered search with caching, word page (noun/verb basics), Translator Mode, search history, auth, SQLite persistence

2. **Creative Phase 1 (3–4 weeks):** 
   - **Drawing Lab**: Canvas drawing → OpenAI scene analysis → grammar exercises
   - **Picture→German**: Image upload → Vision API description → vocabulary practice  
   - **Word Family Explorer**: Interactive word relationship trees with D3.js visualizations
   - **Export Functions**: PDF worksheets, Anki deck generation

3. **Phase 2 (4–6 weeks):** Exam generator (cloze + MCQ), auto‑checking, SRS, analytics dashboard

4. **Creative Phase 2 (6–8 weeks):** Mini-games (Article Tetris, Case Runner), Grammar Maps, Comic Generator

5. **Polish:** audio, synonyms UI, dark mode, advanced analytics, performance optimization

6. **Advanced:** Pronunciation Studio, handwriting trainer, mobile PWA, editor tooling

---

## 16) Creative Phase 1 - Detailed Implementation

### 16.1 Drawing Lab Implementation
```typescript
// Frontend: Konva.js Canvas Component
const DrawingCanvas = {
  setup() {
    const stage = new Konva.Stage({ container: 'canvas', width: 800, height: 600 })
    const layer = new Konva.Layer()
    
    // Drawing tools: pen, shapes, text labels
    const drawingTools = ['pen', 'rectangle', 'circle', 'text']
    
    const analyzeDrawing = async () => {
      const dataURL = stage.toDataURL()
      const response = await api.post('/draw/scene', { 
        image: dataURL, 
        prompt: 'Describe this room in German A2 level',
        level: 'A2'
      })
      return response.data // { objects: [], sentences: [], practice_questions: [] }
    }
  }
}
```

**Backend Service:**
```python
# services/vision_service.py
class VisionService:
    async def analyze_scene(self, image_data: str, level: str = "A2"):
        # OpenAI Vision API call
        response = await openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"Analyze this drawing. Create German sentences at {level} level with preposition exercises."},
                    {"type": "image_url", "image_url": {"url": image_data}}
                ]
            }]
        )
        return self._parse_scene_analysis(response)
```

### 16.2 Picture→German Implementation
```python
# API Endpoint: /vision/analyze
async def analyze_image(image: UploadFile, level: str = "A2"):
    # Cache check first
    image_hash = hashlib.md5(await image.read()).hexdigest()
    cached = await get_cached_vision_analysis(image_hash, level)
    if cached:
        return cached
    
    # OpenAI Vision analysis
    analysis = await vision_service.describe_image(image, level)
    
    # Cache result
    await cache_vision_analysis(image_hash, level, analysis)
    
    return {
        "description": analysis.german_text,
        "vocabulary": analysis.key_words,
        "cloze_exercises": analysis.fill_blanks,
        "difficulty_level": level
    }
```

### 16.3 Word Family Explorer
```typescript
// D3.js force-directed graph
const WordFamilyGraph = {
  async loadWordFamily(lemma: string) {
    const data = await api.get(`/word-family/${lemma}`)
    
    // Create D3 force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.links))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width/2, height/2))
    
    // Render interactive node graph
    // Nodes: words, edges: relationships (compound, derivation, synonym)
  }
}
```

### 16.4 Export Functions
```python
# PDF Generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

class ExportService:
    async def generate_worksheet(self, word_list: List[str], exercise_types: List[str]):
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        
        # Add German exercises based on word list
        for word in word_list:
            word_data = await get_word_analysis(word)
            self._add_conjugation_exercise(pdf, word_data)
            self._add_cloze_exercise(pdf, word_data)
        
        pdf.save()
        return buffer.getvalue()
    
    async def generate_anki_deck(self, word_list: List[str]):
        # Generate .apkg file with word cards
        # Front: German word, Back: English/Chinese + example
        pass
```

---

## 17) Search Caching & History Implementation

### 16.1 Cache Strategy
```python
# Hash-based cache lookup for instant retrieval
cache_key = hashlib.md5(f"{query_text}:{query_type}".encode()).hexdigest()

# Cache workflow:
# 1. Check if cached result exists
# 2. If exists: return cached result + increment hit_count + log to user history  
# 3. If not exists: call OpenAI API + cache result + log to user history
```

### 16.2 Search History Features
- **Personal timeline**: User sees chronological search history with timestamps
- **Frequency tracking**: Most searched words highlighted for review
- **Quick re-search**: One-click to repeat previous searches
- **Export capability**: Download search history as CSV/JSON
- **Privacy controls**: Clear history, auto-expire old searches

### 16.3 Analytics Dashboard
- **Popular searches**: Most frequently searched words across all users
- **Cache hit rate**: Percentage of searches served from cache vs. OpenAI API
- **Cost tracking**: Daily/monthly API spend with projections
- **User patterns**: Peak usage times, common search sequences

---

## 17) Example Payloads

**Translator word response (noun):**
```json
{
  "original":"Tisch",
  "pos":"noun",
  "article":"der",
  "plural":"Tische",
  "translations_en":["table","desk"],
  "translations_zh":["桌子","台子"],
  "example":{"de":"Der Tisch ist neu.","en":"The table is new.","zh":"这张桌子是新的。"}
}
```

**Translator word response (verb):**
```json
{
  "original":"arbeiten",
  "pos":"verb",
  "tables":{
    "praesens":{"ich":"arbeite","du":"arbeitest","er_sie_es":"arbeitet","wir":"arbeiten","ihr":"arbeitet","sie_Sie":"arbeiten"},
    "praeteritum":{"ich":"arbeitete","du":"arbeitetest","er_sie_es":"arbeitete","wir":"arbeiteten","ihr":"arbeitetet","sie_Sie":"arbeiteten"},
    "perfekt":{"aux":"haben","partizip_ii":"gearbeitet","ich":"habe gearbeitet", "er_sie_es":"hat gearbeitet"},
    "futur1":{"ich":"werde arbeiten","du":"wirst arbeiten","er_sie_es":"wird arbeiten","wir":"werden arbeiten","ihr":"werdet arbeiten","sie_Sie":"werden arbeiten"}
  },
  "translations_en":["to work"],
  "translations_zh":["工作"],
  "example":{"de":"Ich arbeite in Stuttgart.","en":"I work in Stuttgart.","zh":"我在斯图加特工作。"}
}
```

**Exam JSON (excerpt):**
```json
{
  "sections":[{
    "title":"Artikel & Kasus",
    "questions":[{
      "id":"q1","type":"cloze",
      "prompt":"Setzen Sie den richtigen Artikel ein: Ich sehe ___ Tisch.",
      "blanks":[{"id":"b1","alternatives":["den"]}],
      "answer":{"b1":["den"]},
      "explanation":"Akkusativ maskulin → den Tisch."
    },{
      "id":"q2","type":"mcq",
      "prompt":"Wählen Sie die richtige Form von 'gehen' (Präsens, 1. Person Plural).",
      "options":["gehe","gehst","gehen","geht"],
      "answer":[2],
      "explanation":"wir gehen"
    }]
  }],
  "metadata":{"level":"A1","time_limit_min":20}
}
```

---

## 18) Minimal Requirements.txt

```
# Core Backend
fastapi
uvicorn[standard]
pydantic
sqlalchemy
alembic
python-dotenv
passlib[bcrypt]
pyjwt
python-Levenshtein
spacy
openai
httpx

# Creative Modules
pillow                    # Image processing
reportlab                # PDF generation  
redis                    # Task queue
celery                   # Background tasks
opencv-python-headless   # Advanced image processing
svglib                   # SVG processing

# Development
pytest
pytest-asyncio
httpx
# optional: de model downloaded at runtime (documented in README)
```

---

## 19) Implementation Notes

- **OpenAI-first approach**: Use GPT-4o-mini for cost-effective word analysis and translation
- **Aggressive caching**: Store every OpenAI response in SQLite with hash-based lookup for instant retrieval  
- **Search analytics**: Track user search patterns for personalized learning recommendations
- **Cost monitoring**: Log API usage and implement daily/monthly spending caps
- **Fallback strategy**: Maintain basic conjugation tables for offline/emergency mode
- For sentence glossing, split tokens via spaCy; align to OpenAI gloss by index  
- Add **"Accept also"** field in editor to whitelist extra correct variants discovered from user mistakes

---

## 20) License & Attribution

- Your original content © you.  
- Cite datasets you incorporate (if any) and ensure licenses allow use.  
- Avoid copying dictionary texts from protected sources; write short original definitions/examples or use permissive data.

---

*That’s the blueprint. Next step: scaffold FastAPI & Vue projects and implement `/words`, `/translate`, and `/exam` as the MVP.*


---

## 21) Creative & Visual Learning Add‑ons (Optional Modules)

> Goal: make learning playful, visual, and memorable while reinforcing grammar rules and exam skills.

### 21.1 Drawing Lab (Canvas)
- **What:** An in‑browser canvas where learners can draw or label objects; the app turns drawings into practice tasks.
- **Use cases:**
  - *Draw & Describe*: User sketches a room; LLM generates sentences with **prepositions** (auf, unter, neben, zwischen…).  
  - *Label It*: Show a scene (generated or uploaded). User adds labels (*der Tisch, die Lampe*).  
  - *Spot the Case*: Click an object; answer with the right article & case (Akk/Dat).  
- **Tech:** Vue + Canvas/SVG (Konva.js or Fabric.js).  
- **API (MVP):**
  ```http
  POST /draw/scene        { svg|png, prompt?, level? } → { scene_id, objects:[{id,label,bbox}], sentences[] }
  POST /draw/label        { scene_id, labels:[{object_id, de}] } → feedback + word links
  POST /draw/check        { scene_id, answers:{object_id:{article,case}} } → grading
  ```
- **DB tables:**
  - **scenes**(id, svg_blob, prompt, created_by, meta_json)
  - **scene_objects**(id, scene_id, label, bbox_json, gold_meta_json)
  - **scene_attempts**(id, user_id, scene_id, answers_json, score, feedback)

### 21.2 Picture → German (Describe This)
- **What:** Pick/drag an image; get an **A1–B2** German description + word list + cloze questions.
- **Why:** Boosts vocabulary in context; great for exam writing parts.  
- **API:** `POST /vision/describe { image, level } → { german, key_vocab[], cloze[] }`

### 21.3 Comic/Storyboard Generator
- **What:** Generate a 3–4 panel comic about a topic; learners fill in captions (verb forms, connectors).  
- **API:** `POST /comic/generate { topic, grammar_focus, level } → { panels[], blanks[], answer_key }`  
- **Integrates with Exam Mode** as a writing task.

### 21.4 Grammar Maps (Interactive)
- **What:** Visual “map” of cases, tenses, and word order—click nodes to open micro‑lessons & quizzes.  
- **Data:** use `word_lemmas`, `examples`, and curated rules to auto‑link.  
- **Frontend:** force‑directed graph (d3‑force) or Cytoscape.

### 21.5 Conjugation & Declension Visuals
- **What:** Heatmaps for adjective endings; sparkline charts for verb frequencies across tenses.  
- **API:** `GET /words/{lemma}/viz` → minimal JSON for charts.  
- **Why:** Pattern recognition at a glance.

### 21.6 Pronunciation Studio
- **What:** Record speech → align with target sentence → show waveform + pitch track → give phoneme‑level tips.  
- **API:** `POST /speech/score { audio, target_text } → { wpm, accuracy, stress_notes }`  
- **UI:** “karaoke” highlight as you speak.

### 21.7 Handwriting & Spelling Trainer
- **What:** On‑screen handwriting (or keyboard) practice of tricky words (Umlaute, ß).  
- **Grading:** tolerant Levenshtein + umlaut normalization.  
- **Pairs well** with SRS misses.

### 21.8 “Explain My Error” (Why was it wrong?)
- **What:** After grading, show the **rule that fixes** the mistake and 2 micro‑drills.  
- **API:** `POST /explain/error { user_answer, expected, context } → { rule, short_expl, drills[] }`

### 21.9 Word‑Family Explorer
- **What:** Tree of compounding & derivation (z. B. *schreiben → Beschreibung → beschreibbar*).  
- **UI:** click to jump to pages; export as study list.

### 21.10 Mini‑Games
- **Examples:** Article Tetris (drop the right **der/die/das**), Case Runner (pick *den/dem* while running), Prefix Snap (separable verbs).  
- **Scoring:** feed into `/stats` & SRS.

### 21.11 Preposition Playground
- **What:** Drag objects on a table; system asks “Wo ist die Tasse?” User answers with **Dativ** (an/auf/in + Dat), then move it and answer with **Akkusativ** (in + Akk).  
- **Great for:** *über/an/auf/unter/zwischen/gegenüber/entlang* mastery.

### 21.12 Export & Share
- **One‑click Anki deck** from any list or exam mistakes.  
- **PDF worksheet** generator for teachers (with keys).  
- **PWA offline** mode for dictionary & saved exams.

### 21.13 Quick API additions
```http
POST /viz/case-paths         { sentence }     → nodes, edges (case roles)
GET  /games/leaderboard      → top users (opt‑in)
POST /anki/export            { list_id }      → .apkg (or .csv)
POST /worksheet/generate     { topic, level } → PDF link
```

### 21.14 Frontend libs to consider
- **Konva.js** (canvas/SVG), **Cytoscape.js** (graphs), **d3** (simple charts), **WaveSurfer.js** (audio waveforms).

---

## 22) Cost & Privacy Notes for Visual Modules
- Cache all LLM outputs; allow **local fallback** (no image uploads off‑device if user chooses).  
- Offer **“process locally”** toggle for scenes and audio (reduced features but private).  
- Rate‑limit heavy endpoints; queue long jobs with progress IDs.

