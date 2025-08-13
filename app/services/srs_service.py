"""
Spaced Repetition System (SRS) Service - Phase 2
Implements simplified SM-2 algorithm for vocabulary learning
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import math

from app.models.exam import SRSCard, LearningSession, UserProgress
from app.models.word import WordLemma
from app.models.user import User


class SRSService:
    def __init__(self):
        # SM-2 algorithm constants
        self.min_ease_factor = 1.3
        self.initial_ease_factor = 2.5
        self.max_ease_factor = 4.0
        
        # Performance thresholds
        self.pass_threshold = 3  # Quality 3+ = pass
        self.mature_interval = 21  # Days for card to be considered mature
    
    def get_due_cards(
        self,
        db: Session,
        user: User,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get cards due for review"""
        
        now = datetime.utcnow()
        
        due_cards = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.is_active == True,
            SRSCard.next_review_date <= now
        ).order_by(
            SRSCard.next_review_date.asc()
        ).limit(limit).all()
        
        result = []
        for card in due_cards:
            word_data = {
                "card_id": card.id,
                "lemma": card.lemma.lemma,
                "pos": card.lemma.pos,
                "translations_en": [t.text for t in card.lemma.translations if t.lang_code == "en"],
                "translations_zh": [t.text for t in card.lemma.translations if t.lang_code == "zh"],
                "examples": [
                    {
                        "de": ex.de_text,
                        "en": ex.en_text,
                        "zh": ex.zh_text
                    }
                    for ex in card.lemma.examples
                ],
                "ease_factor": card.ease_factor,
                "interval_days": card.interval_days,
                "repetition_count": card.repetition_count,
                "streak": card.streak,
                "is_mature": card.is_mature,
                "days_overdue": (now - card.next_review_date).days if card.next_review_date else 0
            }
            result.append(word_data)
        
        return result
    
    def review_card(
        self,
        db: Session,
        user: User,
        card_id: int,
        quality: int,
        response_time_ms: int = None
    ) -> Dict[str, Any]:
        """Process a card review using SM-2 algorithm"""
        
        card = db.query(SRSCard).filter(
            SRSCard.id == card_id,
            SRSCard.user_id == user.id
        ).first()
        
        if not card:
            return {"error": "Card not found"}
        
        # Validate quality (0-5 scale)
        quality = max(0, min(5, quality))
        
        # Update performance tracking
        if quality >= self.pass_threshold:
            card.correct_count += 1
            card.streak += 1
        else:
            card.incorrect_count += 1
            card.streak = 0
        
        # Apply SM-2 algorithm
        old_interval = card.interval_days
        old_ease = card.ease_factor
        
        if quality >= self.pass_threshold:
            # Successful review
            if card.repetition_count == 0:
                card.interval_days = 1
            elif card.repetition_count == 1:
                card.interval_days = 6
            else:
                card.interval_days = round(card.interval_days * card.ease_factor)
            
            card.repetition_count += 1
            
            # Update ease factor
            card.ease_factor = max(
                self.min_ease_factor,
                card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            )
        else:
            # Failed review - reset interval but keep ease factor reduction
            card.repetition_count = 0
            card.interval_days = 1
            card.ease_factor = max(
                self.min_ease_factor,
                card.ease_factor - 0.2
            )
        
        # Cap ease factor
        card.ease_factor = min(self.max_ease_factor, card.ease_factor)
        
        # Set next review date
        card.next_review_date = datetime.utcnow() + timedelta(days=card.interval_days)
        card.last_reviewed_at = datetime.utcnow()
        
        # Update maturity status
        card.is_mature = card.interval_days >= self.mature_interval
        
        # Track question types
        if response_time_ms:
            # You can add response time analysis here
            pass
        
        db.commit()
        
        # Update user progress
        self._update_user_progress(db, user)
        
        return {
            "success": True,
            "quality": quality,
            "old_interval": old_interval,
            "new_interval": card.interval_days,
            "old_ease": old_ease,
            "new_ease": card.ease_factor,
            "next_review": card.next_review_date.isoformat(),
            "is_mature": card.is_mature,
            "streak": card.streak
        }
    
    def add_word_to_srs(
        self,
        db: Session,
        user: User,
        lemma_id: int,
        initial_quality: int = 3
    ) -> Dict[str, Any]:
        """Add a new word to user's SRS deck"""
        
        # Check if card already exists
        existing_card = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.lemma_id == lemma_id
        ).first()
        
        if existing_card:
            if not existing_card.is_active:
                existing_card.is_active = True
                db.commit()
                return {"success": True, "message": "Card reactivated", "card_id": existing_card.id}
            else:
                return {"error": "Card already exists"}
        
        # Verify lemma exists
        lemma = db.query(WordLemma).filter(WordLemma.id == lemma_id).first()
        if not lemma:
            return {"error": "Word not found"}
        
        # Create new SRS card
        card = SRSCard(
            user_id=user.id,
            lemma_id=lemma_id,
            ease_factor=self.initial_ease_factor,
            interval_days=1,
            repetition_count=0,
            next_review_date=datetime.utcnow() + timedelta(days=1),
            is_active=True,
            is_mature=False
        )
        
        db.add(card)
        db.commit()
        db.refresh(card)
        
        # Update user progress
        self._update_user_progress(db, user)
        
        return {
            "success": True,
            "card_id": card.id,
            "lemma": lemma.lemma,
            "next_review": card.next_review_date.isoformat()
        }
    
    def get_srs_stats(self, db: Session, user: User) -> Dict[str, Any]:
        """Get user's SRS statistics"""
        
        now = datetime.utcnow()
        
        # Count cards by status
        total_cards = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.is_active == True
        ).count()
        
        due_cards = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.is_active == True,
            SRSCard.next_review_date <= now
        ).count()
        
        mature_cards = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.is_active == True,
            SRSCard.is_mature == True
        ).count()
        
        learning_cards = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.is_active == True,
            SRSCard.is_mature == False
        ).count()
        
        # Get review history for last 7 days
        week_ago = now - timedelta(days=7)
        recent_reviews = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.last_reviewed_at >= week_ago
        ).count()
        
        # Calculate accuracy
        cards_with_reviews = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.correct_count + SRSCard.incorrect_count > 0
        ).all()
        
        if cards_with_reviews:
            total_reviews = sum(card.correct_count + card.incorrect_count for card in cards_with_reviews)
            total_correct = sum(card.correct_count for card in cards_with_reviews)
            accuracy = (total_correct / total_reviews * 100) if total_reviews > 0 else 0
        else:
            accuracy = 0
        
        return {
            "total_cards": total_cards,
            "due_cards": due_cards,
            "mature_cards": mature_cards,
            "learning_cards": learning_cards,
            "recent_reviews": recent_reviews,
            "accuracy_percentage": round(accuracy, 1),
            "next_review_in_minutes": self._get_next_review_time(db, user)
        }
    
    def _get_next_review_time(self, db: Session, user: User) -> Optional[int]:
        """Get minutes until next review"""
        
        now = datetime.utcnow()
        
        next_card = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.is_active == True,
            SRSCard.next_review_date > now
        ).order_by(SRSCard.next_review_date.asc()).first()
        
        if next_card:
            time_diff = next_card.next_review_date - now
            return int(time_diff.total_seconds() / 60)
        
        return None
    
    def _update_user_progress(self, db: Session, user: User):
        """Update user's learning progress statistics"""
        
        # Get or create progress record
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user.id
        ).first()
        
        if not progress:
            progress = UserProgress(user_id=user.id)
            db.add(progress)
        
        # Update vocabulary size
        progress.vocabulary_size = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.is_active == True
        ).count()
        
        # Update words learned (mature cards)
        progress.total_words_learned = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.is_active == True,
            SRSCard.is_mature == True
        ).count()
        
        # Calculate average accuracy
        cards_with_reviews = db.query(SRSCard).filter(
            SRSCard.user_id == user.id,
            SRSCard.correct_count + SRSCard.incorrect_count > 0
        ).all()
        
        if cards_with_reviews:
            total_reviews = sum(card.correct_count + card.incorrect_count for card in cards_with_reviews)
            total_correct = sum(card.correct_count for card in cards_with_reviews)
            progress.average_accuracy = (total_correct / total_reviews) if total_reviews > 0 else 0
        
        db.commit()
    
    def create_learning_session(
        self,
        db: Session,
        user: User,
        session_type: str = "srs_review"
    ) -> Dict[str, Any]:
        """Start a new learning session"""
        
        session = LearningSession(
            user_id=user.id,
            session_type=session_type,
            started_at=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return {
            "session_id": session.id,
            "started_at": session.started_at.isoformat(),
            "type": session_type
        }
    
    def end_learning_session(
        self,
        db: Session,
        session_id: int,
        questions_answered: int = 0,
        correct_answers: int = 0,
        topics_covered: List[str] = None,
        words_practiced: List[int] = None
    ) -> Dict[str, Any]:
        """End a learning session and record statistics"""
        
        session = db.query(LearningSession).filter(
            LearningSession.id == session_id
        ).first()
        
        if not session:
            return {"error": "Session not found"}
        
        # Update session
        now = datetime.utcnow()
        session.ended_at = now
        session.duration_seconds = int((now - session.started_at).total_seconds())
        session.questions_answered = questions_answered
        session.correct_answers = correct_answers
        session.accuracy_percentage = (correct_answers / questions_answered * 100) if questions_answered > 0 else 0
        session.topics_covered = topics_covered or []
        session.words_practiced = words_practiced or []
        
        db.commit()
        
        return {
            "success": True,
            "duration_minutes": round(session.duration_seconds / 60, 1),
            "accuracy": session.accuracy_percentage,
            "questions_answered": questions_answered
        }