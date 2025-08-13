"""
Auto-Grading Service - Phase 2
Handles automatic grading with fuzzy matching and morphology awareness
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from difflib import SequenceMatcher
from sqlalchemy.orm import Session

from app.models.exam import ExamQuestion, ExamResponse, ExamAttempt
from app.models.word import WordLemma, WordForm


class GradingService:
    def __init__(self):
        self.fuzzy_threshold = 0.9
        
    async def grade_response(
        self,
        db: Session,
        question: ExamQuestion,
        user_answer: Any,
        time_taken: int = None
    ) -> Dict[str, Any]:
        """Grade a user's response to a question"""
        
        if question.question_type == "mcq":
            return self._grade_mcq(question, user_answer)
        elif question.question_type == "cloze":
            return await self._grade_cloze(db, question, user_answer)
        elif question.question_type == "matching":
            return self._grade_matching(question, user_answer)
        elif question.question_type == "reorder":
            return self._grade_reorder(question, user_answer)
        elif question.question_type == "writing":
            return self._grade_writing(question, user_answer)
        else:
            return {
                "is_correct": False,
                "partial_credit": 0.0,
                "points_earned": 0.0,
                "feedback": "Unknown question type",
                "auto_feedback": {}
            }
    
    def _grade_mcq(self, question: ExamQuestion, user_answer: Any) -> Dict[str, Any]:
        """Grade multiple choice question"""
        
        correct_answers = question.correct_answer
        user_selection = user_answer if isinstance(user_answer, list) else [user_answer]
        
        # Normalize answers for comparison
        correct_normalized = [self._normalize_text(ans) for ans in correct_answers]
        user_normalized = [self._normalize_text(ans) for ans in user_selection]
        
        is_correct = set(user_normalized) == set(correct_normalized)
        points_earned = question.points if is_correct else 0.0
        
        feedback = ""
        if not is_correct:
            feedback = f"Correct answer: {', '.join(correct_answers)}. "
            if question.explanation:
                feedback += question.explanation
        
        return {
            "is_correct": is_correct,
            "partial_credit": 1.0 if is_correct else 0.0,
            "points_earned": points_earned,
            "feedback": feedback,
            "auto_feedback": {
                "expected": correct_answers,
                "received": user_selection,
                "type": "exact_match"
            }
        }
    
    async def _grade_cloze(self, db: Session, question: ExamQuestion, user_answer: Any) -> Dict[str, Any]:
        """Grade cloze (fill-in-the-blank) question with morphology awareness"""
        
        if not isinstance(user_answer, dict):
            return self._create_error_result("Invalid answer format for cloze question")
        
        blanks = question.content.get("blanks", [])
        correct_answers = question.correct_answer
        
        total_blanks = len(blanks)
        correct_blanks = 0
        feedback_parts = []
        detailed_feedback = {}
        
        for blank in blanks:
            blank_id = blank["id"]
            user_response = user_answer.get(blank_id, "").strip()
            expected_answers = correct_answers.get(blank_id, [])
            alternatives = blank.get("alternatives", [])
            
            # Combine correct answers and alternatives
            all_acceptable = expected_answers + alternatives
            
            # Check for exact match first
            is_exact_match = any(
                self._normalize_text(user_response) == self._normalize_text(ans)
                for ans in all_acceptable
            )
            
            if is_exact_match:
                correct_blanks += 1
                detailed_feedback[blank_id] = {
                    "correct": True,
                    "match_type": "exact",
                    "feedback": "Correct!"
                }
            else:
                # Try fuzzy matching
                fuzzy_match, match_score, matched_answer = self._fuzzy_match(
                    user_response, all_acceptable
                )
                
                if fuzzy_match:
                    correct_blanks += 1
                    detailed_feedback[blank_id] = {
                        "correct": True,
                        "match_type": "fuzzy",
                        "match_score": match_score,
                        "feedback": f"Correct (minor spelling difference from '{matched_answer}')"
                    }
                else:
                    # Try morphology-aware matching for German
                    morphology_match = await self._check_morphology_match(
                        db, user_response, all_acceptable
                    )
                    
                    if morphology_match["is_match"]:
                        correct_blanks += 0.8  # Partial credit for morphological variants
                        detailed_feedback[blank_id] = {
                            "correct": True,
                            "match_type": "morphological",
                            "feedback": morphology_match["feedback"]
                        }
                    else:
                        detailed_feedback[blank_id] = {
                            "correct": False,
                            "match_type": "none",
                            "expected": expected_answers,
                            "received": user_response,
                            "feedback": f"Expected: {', '.join(expected_answers)}"
                        }
        
        # Calculate score
        partial_credit = correct_blanks / total_blanks if total_blanks > 0 else 0.0
        points_earned = question.points * partial_credit
        is_correct = partial_credit >= 0.8  # Consider correct if 80% or better
        
        # Generate overall feedback
        if is_correct:
            feedback = "Well done!"
        else:
            incorrect_count = total_blanks - int(correct_blanks)
            feedback = f"{incorrect_count} blank(s) incorrect. "
            if question.explanation:
                feedback += question.explanation
        
        return {
            "is_correct": is_correct,
            "partial_credit": partial_credit,
            "points_earned": points_earned,
            "feedback": feedback,
            "auto_feedback": {
                "type": "cloze",
                "blanks": detailed_feedback,
                "score_breakdown": f"{correct_blanks:.1f}/{total_blanks}"
            }
        }
    
    def _grade_matching(self, question: ExamQuestion, user_answer: Any) -> Dict[str, Any]:
        """Grade matching question"""
        
        if not isinstance(user_answer, dict):
            return self._create_error_result("Invalid answer format for matching question")
        
        correct_pairs = question.correct_answer
        user_pairs = user_answer
        
        total_pairs = len(correct_pairs)
        correct_matches = 0
        
        for key, correct_value in correct_pairs.items():
            user_value = user_pairs.get(key)
            if user_value and self._normalize_text(user_value) == self._normalize_text(correct_value):
                correct_matches += 1
        
        partial_credit = correct_matches / total_pairs if total_pairs > 0 else 0.0
        points_earned = question.points * partial_credit
        is_correct = partial_credit >= 0.8
        
        return {
            "is_correct": is_correct,
            "partial_credit": partial_credit,
            "points_earned": points_earned,
            "feedback": f"Matched {correct_matches} out of {total_pairs} pairs correctly.",
            "auto_feedback": {
                "type": "matching",
                "correct_matches": correct_matches,
                "total_pairs": total_pairs
            }
        }
    
    def _grade_reorder(self, question: ExamQuestion, user_answer: Any) -> Dict[str, Any]:
        """Grade sentence reordering question"""
        
        if not isinstance(user_answer, list):
            return self._create_error_result("Invalid answer format for reorder question")
        
        correct_order = question.correct_answer
        user_order = user_answer
        
        # Check for exact sequence match
        is_correct = user_order == correct_order
        
        if not is_correct:
            # Calculate partial credit based on correct positions
            correct_positions = sum(
                1 for i, (user_item, correct_item) in enumerate(zip(user_order, correct_order))
                if user_item == correct_item
            )
            partial_credit = correct_positions / len(correct_order) if correct_order else 0.0
        else:
            partial_credit = 1.0
        
        points_earned = question.points * partial_credit
        
        return {
            "is_correct": is_correct,
            "partial_credit": partial_credit,
            "points_earned": points_earned,
            "feedback": f"Word order: {partial_credit*100:.0f}% correct",
            "auto_feedback": {
                "type": "reorder",
                "expected": correct_order,
                "received": user_order
            }
        }
    
    def _grade_writing(self, question: ExamQuestion, user_answer: Any) -> Dict[str, Any]:
        """Grade writing question (basic keyword matching)"""
        
        if not isinstance(user_answer, str):
            return self._create_error_result("Invalid answer format for writing question")
        
        # For now, implement basic keyword matching
        # In a full system, this would use LLM for more sophisticated evaluation
        
        required_keywords = question.content.get("required_keywords", [])
        user_text = user_answer.lower()
        
        found_keywords = []
        for keyword in required_keywords:
            if keyword.lower() in user_text:
                found_keywords.append(keyword)
        
        partial_credit = len(found_keywords) / len(required_keywords) if required_keywords else 0.5
        points_earned = question.points * partial_credit
        is_correct = partial_credit >= 0.7
        
        return {
            "is_correct": is_correct,
            "partial_credit": partial_credit,
            "points_earned": points_earned,
            "feedback": f"Found {len(found_keywords)} of {len(required_keywords)} required elements.",
            "auto_feedback": {
                "type": "writing",
                "found_keywords": found_keywords,
                "required_keywords": required_keywords,
                "word_count": len(user_answer.split())
            }
        }
    
    def _fuzzy_match(self, user_input: str, acceptable_answers: List[str]) -> Tuple[bool, float, str]:
        """Check for fuzzy string matching using Levenshtein similarity"""
        
        user_normalized = self._normalize_text(user_input)
        best_score = 0.0
        best_match = ""
        
        for answer in acceptable_answers:
            answer_normalized = self._normalize_text(answer)
            score = SequenceMatcher(None, user_normalized, answer_normalized).ratio()
            
            if score > best_score:
                best_score = score
                best_match = answer
        
        is_match = best_score >= self.fuzzy_threshold
        return is_match, best_score, best_match
    
    async def _check_morphology_match(
        self,
        db: Session,
        user_input: str,
        acceptable_answers: List[str]
    ) -> Dict[str, Any]:
        """Check for morphologically equivalent answers (same lemma, different form)"""
        
        # Find the lemma for user input
        user_lemma = await self._find_lemma_for_form(db, user_input)
        
        if not user_lemma:
            return {"is_match": False, "feedback": "Unknown word form"}
        
        # Check if any acceptable answer has the same lemma
        for answer in acceptable_answers:
            answer_lemma = await self._find_lemma_for_form(db, answer)
            
            if answer_lemma and answer_lemma.id == user_lemma.id:
                return {
                    "is_match": True,
                    "feedback": f"Correct lemma '{user_lemma.lemma}', but expected form '{answer}'"
                }
        
        return {"is_match": False, "feedback": "Different word/lemma"}
    
    async def _find_lemma_for_form(self, db: Session, word_form: str) -> Optional[WordLemma]:
        """Find the lemma for a given word form"""
        
        # First try exact lemma match
        lemma = db.query(WordLemma).filter(
            WordLemma.lemma.ilike(word_form)
        ).first()
        
        if lemma:
            return lemma
        
        # Then try word form match
        word_form_entry = db.query(WordForm).filter(
            WordForm.form.ilike(word_form)
        ).first()
        
        if word_form_entry:
            return word_form_entry.lemma
        
        return None
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation for comparison
        text = re.sub(r'[^\w\säöüß]', '', text)
        
        # Normalize umlauts (optional - might not want this for German)
        # text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
        
        return text
    
    def _create_error_result(self, message: str) -> Dict[str, Any]:
        """Create error result for invalid responses"""
        return {
            "is_correct": False,
            "partial_credit": 0.0,
            "points_earned": 0.0,
            "feedback": f"Error: {message}",
            "auto_feedback": {"error": message}
        }