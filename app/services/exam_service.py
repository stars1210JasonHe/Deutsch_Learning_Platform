"""
Exam Generation Service - Phase 2
Generates CEFR-aligned exams with auto-checking and feedback
"""
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import random

from app.models.exam import Exam, ExamSection, ExamQuestion, ExamAttempt, ExamResponse
from app.models.word import WordLemma
from app.models.user import User
from app.services.openai_service import OpenAIService
from app.core.config import settings
from openai import AsyncOpenAI


class ExamService:
    def __init__(self):
        self.openai_service = OpenAIService()
        
        # Create dedicated exam client if separate credentials provided
        if settings.openai_exam_api_key:
            self.exam_client = AsyncOpenAI(
                api_key=settings.openai_exam_api_key,
                base_url=settings.openai_exam_base_url or "https://api.openai.com/v1"
            )
            # Force GPT-4o for now to avoid GPT-5 issues
            self.exam_model = "gpt-4o"  # Override to use stable model
        else:
            # Fall back to main OpenAI service
            self.exam_client = self.openai_service.client
            self.exam_model = settings.openai_exam_model or self.openai_service.model
    
    async def generate_exam(
        self,
        db: Session,
        user: User,
        level: str = "A1",
        topics: List[str] = None,
        question_types: List[str] = None,
        question_count: int = 10,
        title: str = None,
        description: str = None
    ) -> Dict[str, Any]:
        """Generate a new exam using a template-first approach with OpenAI if available"""
        
        # If description is provided, analyze it to extract focus areas
        if description:
            analysis = await self._analyze_exam_description(description, level)
            if not topics:
                topics = analysis.get('topics', self._get_default_topics(level))
            if not question_types:
                question_types = analysis.get('question_types', ["mcq", "cloze", "matching"])
            if not title:
                title = analysis.get('title', f"German {level} Custom Exam")
        else:
            if not topics:
                topics = self._get_default_topics(level)
            if not question_types:
                question_types = ["mcq", "cloze", "matching"]
            if not title:
                title = f"German {level} Practice Exam"
        
        # Get vocabulary for this level from database
        vocabulary = await self._get_level_vocabulary(db, level)
        
        # Step 1: Create an exam template/blueprint (prefer OpenAI if available)
        template = await self._generate_exam_template(
            level=level,
            topics=topics,
            question_types=question_types,
            count=question_count,
            vocabulary=vocabulary,
            description=description
        )

        # Step 2: Generate exam questions from the template
        exam_content = await self._generate_exam_from_template(
            level=level,
            topics=topics,
            template=template,
            vocabulary=vocabulary,
        )
        
        try:
            # Create exam in database
            exam = await self._create_exam_in_db(
                db, user, title, level, topics, exam_content
            )
            
            return {
                "exam_id": exam.id,
                "title": exam.title,
                "level": exam.cefr_level,
                "total_questions": exam.total_questions,
                "sections": await self._format_exam_for_frontend(exam)
            }
        except Exception as e:
            logging.error(f"Failed to create exam in database: {e}")
            logging.error(f"Error type: {type(e).__name__}")
            raise e
    
    async def _analyze_exam_description(
        self,
        description: str,
        level: str
    ) -> Dict[str, Any]:
        """Analyze user's exam description to extract focus areas and preferences"""
        
        if not getattr(self.openai_service, "client", None):
            # Fallback: basic keyword extraction
            return self._simple_description_analysis(description, level)
        
        prompt = f"""
Analyze this exam request description for German language learning at CEFR {level} level:

"{description}"

Extract the key information and return ONLY JSON with this schema:
{{
  "title": "string - suggested exam title based on the description",
  "topics": ["array", "of", "specific", "grammar", "topics", "or", "areas"],
  "question_types": ["array", "of", "suitable", "question", "types"],
  "focus_areas": ["array", "of", "specific", "skills", "to", "emphasize"],
  "difficulty_emphasis": "string - areas where user wants extra challenge",
  "suggested_question_count": number
}}

Available question types: mcq, cloze, matching, reorder, writing
Common German topics: verbs, nouns, articles, adjectives, prepositions, cases, modal_verbs, past_tense, subjunctive, word_order, etc.

Focus on the user's specific needs and weaknesses mentioned in the description.
"""
        
        try:
            # Use the main OpenAI client for description analysis (fallback)
            if not self.openai_service.client:
                return self._simple_description_analysis(description, level)
                
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.analysis_model,
                messages=[
                    {"role": "system", "content": "Analyze exam requests and return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0  # Use default temperature
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            result = json.loads(content.strip())
            
            # Validate and set defaults
            if 'topics' not in result or not result['topics']:
                result['topics'] = self._get_default_topics(level)
            if 'question_types' not in result or not result['question_types']:
                result['question_types'] = ["mcq", "cloze", "matching"]
            if 'title' not in result:
                result['title'] = f"German {level} Custom Exam"
                
            return result
            
        except Exception as e:
            logging.warning(f"Failed to analyze exam description with AI: {e}")
            return self._simple_description_analysis(description, level)
    
    def _simple_description_analysis(self, description: str, level: str) -> Dict[str, Any]:
        """Simple keyword-based description analysis as fallback"""
        
        desc_lower = description.lower()
        
        # Extract topics based on keywords
        topic_keywords = {
            'verbs': ['verb', 'conjugation', 'past tense', 'present', 'future'],
            'cases': ['case', 'accusative', 'dative', 'genitive', 'nominative'],
            'articles': ['article', 'der', 'die', 'das', 'ein', 'eine'],
            'adjectives': ['adjective', 'comparative', 'superlative'],
            'prepositions': ['preposition', 'with', 'zu', 'für', 'von'],
            'modal_verbs': ['modal', 'können', 'müssen', 'wollen', 'sollen'],
            'word_order': ['word order', 'sentence structure', 'syntax']
        }
        
        detected_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                detected_topics.append(topic)
        
        # Extract question type preferences
        question_type_keywords = {
            'mcq': ['multiple choice', 'choose', 'select'],
            'cloze': ['fill', 'blank', 'gap', 'complete'],
            'matching': ['match', 'pair', 'connect'],
            'writing': ['write', 'compose', 'essay'],
            'reorder': ['order', 'arrange', 'sequence']
        }
        
        suggested_types = []
        for qtype, keywords in question_type_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                suggested_types.append(qtype)
        
        # Generate title from description
        title_words = description.split()[:4]  # First few words
        title = f"German {level} - {' '.join(title_words)}"
        if len(title) > 50:
            title = title[:47] + "..."
        
        return {
            'title': title,
            'topics': detected_topics if detected_topics else self._get_default_topics(level),
            'question_types': suggested_types if suggested_types else ["mcq", "cloze", "matching"],
            'focus_areas': detected_topics,
            'difficulty_emphasis': "general",
            'suggested_question_count': 10
        }
    
    async def _generate_exam_template(
        self,
        level: str,
        topics: List[str],
        question_types: List[str],
        count: int,
        vocabulary: List[Dict],
        description: str = None
    ) -> Dict[str, Any]:
        """Create an exam blueprint template. Prefer OpenAI; fallback to deterministic template."""

        # Deterministic fallback distribution
        def _fallback_template() -> Dict[str, Any]:
            per_section = max(1, count // 2)
            type_share = max(1, count // max(1, len(question_types)))
            # Set time limit to approximately 18 seconds per question (3 minutes for 10 questions)
            time_per_question = 0.3  # 18 seconds = 0.3 minutes
            return {
                "sections": [
                    {
                        "title": "Grammar and Vocabulary",
                        "description": "Core CEFR-aligned practice",
                        "num_questions": count,
                        "types": {t: type_share for t in question_types},
                    }
                ],
                "metadata": {
                    "level": level,
                    "estimated_time_minutes": max(3, int(count * time_per_question)),
                    "total_points": count,
                },
            }

        if not self.exam_client:
            return _fallback_template()

        vocab_sample = random.sample(vocabulary, min(len(vocabulary), 20))
        # Safely handle German characters in vocabulary
        vocab_items = []
        for w in vocab_sample:
            try:
                vocab_items.append(f"{w['lemma']} ({w['pos']})")
            except (UnicodeEncodeError, KeyError):
                # Skip problematic vocabulary items
                continue
        vocab_text = ", ".join(vocab_items[:10])  # Limit to 10 items to avoid long prompts

        description_context = f"\n\nSpecial Requirements: {description}" if description else ""
        
        prompt = f"""
Design a blueprint TEMPLATE for a German exam at CEFR {level}. Use topics [{', '.join(topics)}] and question types [{', '.join(question_types)}].
Use vocabulary context: {vocab_text}{description_context}

Return ONLY JSON with this schema:
{{
  "sections": [
    {{
      "title": "string",
      "description": "string",
      "num_questions": number,
      "types": {{ "mcq": number, "cloze": number, "matching": number, "reorder"?: number, "writing"?: number }}
    }}
  ],
  "metadata": {{ "level": "{level}", "estimated_time_minutes": number, "total_points": number }}
}}

Rules:
- Ensure sum(types) across all sections equals {count} total questions.
- Prefer balanced distribution across requested types; do not invent types not requested.
- Keep section count between 1 and 3.
- Set time limit to 3-5 minutes total (approximately 18-30 seconds per question for quick assessment).
"""

        try:
            response = await self.exam_client.chat.completions.create(
                model=self.exam_model,
                messages=[
                    {"role": "system", "content": "You are an expert German language teacher creating educational exams. Create concise, pedagogically sound JSON blueprints. Output valid JSON only."},
                    {"role": "user", "content": prompt},
                ]
                # max_tokens=2000,
                # timeout=30.0
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            template = json.loads(content.strip())

            # Light validation; fallback if invalid
            total_in_template = 0
            for s in template.get("sections", []):
                total_in_template += int(sum(max(0, int(v)) for v in s.get("types", {}).values()))
            if total_in_template != count:
                logging.warning("Template question count mismatch; using fallback template")
                return _fallback_template()

            return template
        except Exception as e:
            logging.error(f"OpenAI template generation failed: {e}")
            logging.error(f"Error type: {type(e).__name__}")
            # Always use fallback when OpenAI fails
            return _fallback_template()

    async def _generate_exam_from_template(
        self,
        level: str,
        topics: List[str],
        template: Dict[str, Any],
        vocabulary: List[Dict],
    ) -> Dict[str, Any]:
        """Generate concrete exam questions from a template. Prefer OpenAI; fallback deterministic."""

        if not self.exam_client:
            return self._create_fallback_exam(level, template.get("metadata", {}).get("total_points", 10))

        vocab_sample = random.sample(vocabulary, min(len(vocabulary), 30))
        # Safely encode vocabulary for JSON
        safe_vocab = []
        for w in vocab_sample:
            try:
                safe_vocab.append({
                    'lemma': str(w.get('lemma', '')),
                    'pos': str(w.get('pos', '')),
                    'translations': [str(t) for t in w.get('translations', [])]
                })
            except (UnicodeEncodeError, AttributeError):
                continue
        vocab_json = json.dumps(safe_vocab[:15], ensure_ascii=True)  # Use ASCII encoding
        template_json = json.dumps(template, ensure_ascii=False)

        prompt = f"""
Using this EXAM TEMPLATE (do not change counts or types):
{template_json}

Generate the concrete exam QUESTIONS for CEFR {level} covering topics [{', '.join(topics)}].
Use the following vocabulary context for target_words and content variety:
{vocab_json}

Output ONLY JSON with this schema:
{{
  "sections": [
    {{
      "title": "string",
      "description": "string",
      "questions": [
        {{
          "id": "string",
          "type": "mcq|cloze|matching|reorder|writing",
          "prompt": "string",
          "content": {{ }},
          "correct_answer": {{ }} | ["..."],
          "explanation": "string",
          "target_words": ["lemma", ...],
          "difficulty": "easy|medium|hard",
          "points": number
        }}
      ]
    }}
  ],
  "metadata": {{ "level": "{level}", "estimated_time_minutes": number, "total_points": number }}
}}

Strict rules:
- The number of questions per section and per type MUST exactly match the TEMPLATE "types" counts.
- For MCQ, always provide 4 options in content.options.
- For CLOZE, CRITICAL FORMAT: content must have both "text" field with [blankId] placeholders AND "blanks" array. Example:
  content: {{
    "text": "Der Hund ist [b1] und die Katze ist [b2].",
    "blanks": [
      {{"id": "b1", "alternatives": ["groß", "klein"]}},
      {{"id": "b2", "alternatives": ["schwarz", "weiß"]}}
    ]
  }}
  correct_answer maps blank ids to arrays of acceptable answers.
- For MATCHING, use 5-6 pairs in content.pairs.
- Use natural, CEFR-appropriate German sentences; avoid English unless asked in prompt.
"""

        try:
            response = await self.exam_client.chat.completions.create(
                model=self.exam_model,
                messages=[
                    {"role": "system", "content": "You are an expert German language teacher. Turn exam templates into concrete, educational question sets. Create engaging, CEFR-appropriate German questions. Output valid JSON only."},
                    {"role": "user", "content": prompt},
                ]
                    # max_tokens=3000,
                    # timeout=45.0
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except Exception as e:
            logging.error(f"OpenAI question generation failed: {e}")
            logging.error(f"Error type: {type(e).__name__}")
            # Always use fallback when OpenAI fails
            return self._create_fallback_exam(level, template.get("metadata", {}).get("total_points", 10))
    
    def _create_fallback_exam(self, level: str, count: int) -> Dict[str, Any]:
        """Create a basic exam structure when OpenAI fails"""
        # Set time limit to approximately 18 seconds per question (3 minutes for 10 questions)
        time_per_question = 0.3  # 18 seconds = 0.3 minutes
        return {
            "sections": [
                {
                    "title": f"German {level} Practice",
                    "questions": [
                        {
                            "id": f"q{i+1}",
                            "type": "mcq",
                            "prompt": "Select the correct answer:",
                            "content": {"options": ["Option A", "Option B", "Option C", "Option D"]},
                            "correct_answer": ["Option A"],
                            "explanation": "Basic question",
                            "target_words": [],
                            "difficulty": "medium",
                            "points": 1.0
                        }
                        for i in range(count)
                    ]
                }
            ],
            "metadata": {
                "level": level,
                "estimated_time_minutes": max(3, int(count * time_per_question)),
                "total_points": count
            }
        }
    
    async def _create_exam_in_db(
        self,
        db: Session,
        user: User,
        title: str,
        level: str,
        topics: List[str],
        exam_content: Dict[str, Any]
    ) -> Exam:
        """Create exam in database from generated content"""
        
        metadata = exam_content.get("metadata", {})
        
        # Create exam
        exam = Exam(
            title=title,
            description=f"Generated exam for {level} level",
            cefr_level=level,
            topics=topics,
            total_questions=0,
            time_limit_minutes=metadata.get("estimated_time_minutes", 30),
            created_by_id=user.id
        )
        
        db.add(exam)
        db.commit()
        db.refresh(exam)
        
        # Create sections and questions
        total_questions = 0
        for section_data in exam_content.get("sections", []):
            section = ExamSection(
                exam_id=exam.id,
                title=section_data.get("title", "Section"),
                description=section_data.get("description", ""),
                order_index=0
            )
            
            db.add(section)
            db.commit()
            db.refresh(section)
            
            # Create questions
            for i, question_data in enumerate(section_data.get("questions", [])):
                question = ExamQuestion(
                    section_id=section.id,
                    question_type=question_data.get("type", "mcq"),
                    prompt=question_data.get("prompt", ""),
                    content=question_data.get("content", {}),
                    correct_answer=question_data.get("correct_answer", {}),
                    alternatives=question_data.get("alternatives", {}),
                    explanation=question_data.get("explanation", ""),
                    points=question_data.get("points", 1.0),
                    difficulty=question_data.get("difficulty", "medium"),
                    order_index=i,
                    target_words=question_data.get("target_words", [])
                )
                
                db.add(question)
                total_questions += 1
        
        # Update exam total questions
        exam.total_questions = total_questions
        db.commit()
        
        return exam
    
    async def _get_level_vocabulary(self, db: Session, level: str) -> List[Dict]:
        """Get vocabulary words for the specified CEFR level"""
        
        words = db.query(WordLemma).filter(
            WordLemma.cefr == level
        ).limit(100).all()
        
        if not words:
            # If no level-specific words, get any words
            words = db.query(WordLemma).limit(50).all()
        
        return [
            {
                "lemma": word.lemma,
                "pos": word.pos or "unknown",
                "translations": [t.text for t in word.translations]
            }
            for word in words
        ]
    
    def _get_default_topics(self, level: str) -> List[str]:
        """Get default topics for each CEFR level"""
        
        topics_by_level = {
            "A1": ["greetings", "numbers", "family", "colors", "basic verbs", "articles"],
            "A2": ["past tense", "modal verbs", "adjective endings", "dative case", "time expressions"],
            "B1": ["subjunctive", "passive voice", "relative clauses", "prepositions", "word order"],
            "B2": ["advanced grammar", "complex sentences", "idiomatic expressions", "formal language"],
            "C1": ["advanced syntax", "stylistic devices", "academic language", "abstract concepts"],
            "C2": ["literary analysis", "complex discourse", "subtle nuances", "expert communication"]
        }
        
        return topics_by_level.get(level, ["general grammar", "vocabulary"])
    
    async def _format_exam_for_frontend(self, exam: Exam) -> List[Dict]:
        """Format exam data for frontend consumption"""
        
        sections = []
        for section in exam.sections:
            section_data = {
                "id": section.id,
                "title": section.title,
                "description": section.description,
                "questions": []
            }
            
            for question in section.questions:
                question_data = {
                    "id": question.id,
                    "type": question.question_type,
                    "prompt": question.prompt,
                    "content": question.content,
                    "points": question.points,
                    "difficulty": question.difficulty
                }
                section_data["questions"].append(question_data)
            
            sections.append(section_data)
        
        return sections