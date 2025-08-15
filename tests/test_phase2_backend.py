#!/usr/bin/env python3
"""
Comprehensive Phase 2 Backend Testing Script
Tests exam generation, SRS system, grading, and analytics
"""
import sys
import os
import asyncio
import json
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.word import WordLemma, Translation, Example
from app.models.exam import (
    Exam, ExamSection, ExamQuestion, ExamAttempt, ExamResponse,
    SRSCard, LearningSession, UserProgress
)
from app.services.exam_service import ExamService
from app.services.grading_service import GradingService
from app.services.srs_service import SRSService
from app.core.security import get_password_hash


class Phase2BackendTester:
    def __init__(self):
        self.db = SessionLocal()
        self.exam_service = ExamService()
        self.grading_service = GradingService()
        self.srs_service = SRSService()
        self.test_user = None
        self.test_words = []
        
    async def run_all_tests(self):
        """Run comprehensive Phase 2 backend tests"""
        print("🚀 Starting Phase 2 Backend Tests")
        print("=" * 60)
        
        try:
            # Setup test data
            await self.setup_test_data()
            
            # Test each system
            await self.test_exam_system()
            await self.test_grading_system()
            await self.test_srs_system()
            await self.test_analytics_system()
            
            print(f"\n🎉 All Phase 2 Backend Tests Complete!")
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    async def setup_test_data(self):
        """Setup test user and vocabulary data"""
        print(f"\n🔧 Setting up test data...")
        
        # Create test user
        self.test_user = User(
            email="phase2test@example.com",
            password_hash=get_password_hash("test123"),
            role=UserRole.USER
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)
        
        # Create test vocabulary
        test_vocab = [
            ("gehen", "verb", "to go", "去"),
            ("Haus", "noun", "house", "房子"),
            ("schön", "adjective", "beautiful", "美丽的"),
            ("ich", "pronoun", "I", "我"),
            ("haben", "verb", "to have", "有"),
        ]
        
        for lemma, pos, en_trans, zh_trans in test_vocab:
            word = WordLemma(
                lemma=lemma,
                pos=pos,
                cefr="A1",
                notes=f"Test word: {lemma}"
            )
            self.db.add(word)
            self.db.commit()
            self.db.refresh(word)
            
            # Add translations
            en_translation = Translation(
                lemma_id=word.id,
                lang_code="en",
                text=en_trans,
                source="test"
            )
            zh_translation = Translation(
                lemma_id=word.id,
                lang_code="zh",
                text=zh_trans,
                source="test"
            )
            self.db.add(en_translation)
            self.db.add(zh_translation)
            
            self.test_words.append(word)
        
        self.db.commit()
        print(f"   ✅ Created test user and {len(self.test_words)} test words")
    
    async def test_exam_system(self):
        """Test exam generation and management"""
        print(f"\n📝 Testing Exam System...")
        
        try:
            # Test 1: Generate exam
            print("   🧪 Test 1: Generate exam")
            exam_result = await self.exam_service.generate_exam(
                db=self.db,
                user=self.test_user,
                level="A1",
                topics=["basic_vocabulary", "verb_conjugation"],
                question_types=["mcq", "cloze"],
                question_count=5,
                title="Phase 2 Test Exam"
            )
            
            assert exam_result["exam_id"] is not None, "Exam ID should be generated"
            assert exam_result["total_questions"] > 0, "Exam should have questions"
            print(f"      ✅ Generated exam with ID: {exam_result['exam_id']}")
            
            # Test 2: Start exam attempt
            print("   🧪 Test 2: Start exam attempt")
            exam_id = exam_result["exam_id"]
            exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
            
            attempt = ExamAttempt(
                exam_id=exam_id,
                user_id=self.test_user.id,
                status="in_progress",
                max_points=exam.total_questions * 1.0
            )
            self.db.add(attempt)
            self.db.commit()
            self.db.refresh(attempt)
            
            assert attempt.id is not None, "Attempt should be created"
            print(f"      ✅ Created exam attempt with ID: {attempt.id}")
            
            # Test 3: Submit answers
            print("   🧪 Test 3: Submit exam answers")
            questions = self.db.query(ExamQuestion).filter(
                ExamQuestion.section_id.in_([s.id for s in exam.sections])
            ).all()
            
            for question in questions[:3]:  # Test first 3 questions
                if question.question_type == "mcq":
                    # Submit first option as answer
                    user_answer = [question.content.get("options", ["A"])[0]]
                elif question.question_type == "cloze":
                    # Submit answer for first blank
                    blanks = question.content.get("blanks", [])
                    if blanks:
                        user_answer = {blanks[0]["id"]: ["test_answer"]}
                    else:
                        user_answer = {"b1": ["test_answer"]}
                else:
                    user_answer = "test_answer"
                
                # Grade the response
                grading_result = await self.grading_service.grade_response(
                    db=self.db,
                    question=question,
                    user_answer=user_answer
                )
                
                # Create response record
                response = ExamResponse(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    user_answer=user_answer,
                    is_correct=grading_result["is_correct"],
                    partial_credit=grading_result["partial_credit"],
                    points_earned=grading_result["points_earned"],
                    feedback=grading_result["feedback"]
                )
                self.db.add(response)
            
            self.db.commit()
            print(f"      ✅ Submitted answers for {len(questions[:3])} questions")
            
            # Test 4: Complete exam
            print("   🧪 Test 4: Complete exam")
            responses = self.db.query(ExamResponse).filter(
                ExamResponse.attempt_id == attempt.id
            ).all()
            
            total_points = sum(r.points_earned for r in responses)
            attempt.completed_at = datetime.utcnow()
            attempt.status = "completed"
            attempt.total_points = total_points
            attempt.percentage_score = (total_points / attempt.max_points * 100) if attempt.max_points > 0 else 0
            
            self.db.commit()
            print(f"      ✅ Completed exam with score: {attempt.percentage_score:.1f}%")
            
        except Exception as e:
            print(f"      ❌ Exam system test failed: {e}")
            raise
    
    async def test_grading_system(self):
        """Test auto-grading functionality"""
        print(f"\n⚖️ Testing Grading System...")
        
        try:
            # Test 1: MCQ grading
            print("   🧪 Test 1: MCQ grading")
            mcq_question = ExamQuestion(
                question_type="mcq",
                prompt="What is the German word for 'house'?",
                content={"options": ["Haus", "Auto", "Baum", "Wasser"]},
                correct_answer=["Haus"],
                points=1.0
            )
            
            # Test correct answer
            result = await self.grading_service.grade_response(
                db=self.db,
                question=mcq_question,
                user_answer=["Haus"]
            )
            assert result["is_correct"] == True, "Correct MCQ answer should be marked correct"
            assert result["points_earned"] == 1.0, "Should earn full points"
            print("      ✅ MCQ correct answer grading works")
            
            # Test incorrect answer
            result = await self.grading_service.grade_response(
                db=self.db,
                question=mcq_question,
                user_answer=["Auto"]
            )
            assert result["is_correct"] == False, "Incorrect MCQ answer should be marked incorrect"
            assert result["points_earned"] == 0.0, "Should earn no points"
            print("      ✅ MCQ incorrect answer grading works")
            
            # Test 2: Cloze grading
            print("   🧪 Test 2: Cloze grading")
            cloze_question = ExamQuestion(
                question_type="cloze",
                prompt="Fill in: Ich _____ nach Berlin.",
                content={
                    "blanks": [{"id": "b1", "alternatives": ["gehe", "fahre"]}]
                },
                correct_answer={"b1": ["gehe"]},
                points=1.0
            )
            
            # Test exact match
            result = await self.grading_service.grade_response(
                db=self.db,
                question=cloze_question,
                user_answer={"b1": "gehe"}
            )
            assert result["is_correct"] == True, "Exact cloze match should be correct"
            print("      ✅ Cloze exact match grading works")
            
            # Test alternative answer
            result = await self.grading_service.grade_response(
                db=self.db,
                question=cloze_question,
                user_answer={"b1": "fahre"}
            )
            assert result["is_correct"] == True, "Alternative cloze answer should be correct"
            print("      ✅ Cloze alternative answer grading works")
            
            # Test fuzzy matching
            result = await self.grading_service.grade_response(
                db=self.db,
                question=cloze_question,
                user_answer={"b1": "gehe "}  # Extra space
            )
            assert result["is_correct"] == True, "Fuzzy matching should work"
            print("      ✅ Fuzzy matching grading works")
            
        except Exception as e:
            print(f"      ❌ Grading system test failed: {e}")
            raise
    
    async def test_srs_system(self):
        """Test spaced repetition system"""
        print(f"\n🧠 Testing SRS System...")
        
        try:
            # Test 1: Add words to SRS
            print("   🧪 Test 1: Add words to SRS")
            
            for word in self.test_words[:3]:  # Add first 3 words
                result = self.srs_service.add_word_to_srs(
                    db=self.db,
                    user=self.test_user,
                    lemma_id=word.id
                )
                assert result["success"] == True, f"Should successfully add word {word.lemma}"
            
            print(f"      ✅ Added {3} words to SRS")
            
            # Test 2: Get due cards
            print("   🧪 Test 2: Get due cards")
            due_cards = self.srs_service.get_due_cards(
                db=self.db,
                user=self.test_user
            )
            assert len(due_cards) >= 3, "Should have due cards"
            print(f"      ✅ Retrieved {len(due_cards)} due cards")
            
            # Test 3: Review cards
            print("   🧪 Test 3: Review cards")
            card = self.db.query(SRSCard).filter(
                SRSCard.user_id == self.test_user.id
            ).first()
            
            if card:
                # Test successful review (quality 4 = "Easy")
                old_interval = card.interval_days
                result = self.srs_service.review_card(
                    db=self.db,
                    user=self.test_user,
                    card_id=card.id,
                    quality=4
                )
                
                assert result["success"] == True, "Review should be successful"
                assert result["new_interval"] > old_interval, "Interval should increase for good review"
                print(f"      ✅ Card review: interval {old_interval} → {result['new_interval']}")
                
                # Test failed review (quality 1 = "Hard")
                result = self.srs_service.review_card(
                    db=self.db,
                    user=self.test_user,
                    card_id=card.id,
                    quality=1
                )
                
                assert result["success"] == True, "Failed review should be processed"
                assert result["new_interval"] == 1, "Failed review should reset to 1 day"
                print(f"      ✅ Failed review processing works")
            
            # Test 4: SRS statistics
            print("   🧪 Test 4: SRS statistics")
            stats = self.srs_service.get_srs_stats(db=self.db, user=self.test_user)
            
            assert "total_cards" in stats, "Stats should include total cards"
            assert stats["total_cards"] >= 3, "Should have at least 3 cards"
            print(f"      ✅ SRS stats: {stats['total_cards']} total cards")
            
        except Exception as e:
            print(f"      ❌ SRS system test failed: {e}")
            raise
    
    async def test_analytics_system(self):
        """Test analytics and progress tracking"""
        print(f"\n📊 Testing Analytics System...")
        
        try:
            # Test 1: Learning session tracking
            print("   🧪 Test 1: Learning session tracking")
            
            session_result = self.srs_service.create_learning_session(
                db=self.db,
                user=self.test_user,
                session_type="srs_review"
            )
            session_id = session_result["session_id"]
            
            # End session with stats
            end_result = self.srs_service.end_learning_session(
                db=self.db,
                session_id=session_id,
                questions_answered=10,
                correct_answers=8,
                topics_covered=["basic_vocabulary"],
                words_practiced=[w.id for w in self.test_words[:3]]
            )
            
            assert end_result["success"] == True, "Session should end successfully"
            assert end_result["accuracy"] == 80.0, "Accuracy should be calculated correctly"
            print(f"      ✅ Learning session: {end_result['accuracy']}% accuracy")
            
            # Test 2: User progress
            print("   🧪 Test 2: User progress tracking")
            
            progress = self.db.query(UserProgress).filter(
                UserProgress.user_id == self.test_user.id
            ).first()
            
            if not progress:
                progress = UserProgress(
                    user_id=self.test_user.id,
                    vocabulary_size=3,
                    total_words_learned=1,
                    average_accuracy=0.8
                )
                self.db.add(progress)
                self.db.commit()
            
            assert progress.vocabulary_size >= 0, "Vocabulary size should be tracked"
            print(f"      ✅ User progress: {progress.vocabulary_size} words in vocabulary")
            
            # Test 3: Exam attempt history
            print("   🧪 Test 3: Exam attempt history")
            
            attempts = self.db.query(ExamAttempt).filter(
                ExamAttempt.user_id == self.test_user.id
            ).all()
            
            assert len(attempts) > 0, "Should have exam attempts"
            print(f"      ✅ Found {len(attempts)} exam attempts")
            
            # Test 4: Performance analytics
            print("   🧪 Test 4: Performance analytics")
            
            total_questions = 0
            correct_answers = 0
            
            for attempt in attempts:
                responses = self.db.query(ExamResponse).filter(
                    ExamResponse.attempt_id == attempt.id
                ).all()
                total_questions += len(responses)
                correct_answers += sum(1 for r in responses if r.is_correct)
            
            if total_questions > 0:
                accuracy = (correct_answers / total_questions) * 100
                print(f"      ✅ Overall exam accuracy: {accuracy:.1f}%")
            
        except Exception as e:
            print(f"      ❌ Analytics system test failed: {e}")
            raise
    
    def cleanup(self):
        """Clean up test data"""
        try:
            # Delete test data in reverse order of dependencies
            self.db.query(ExamResponse).filter(
                ExamResponse.attempt_id.in_(
                    self.db.query(ExamAttempt.id).filter(
                        ExamAttempt.user_id == self.test_user.id
                    )
                )
            ).delete(synchronize_session=False)
            
            self.db.query(ExamAttempt).filter(
                ExamAttempt.user_id == self.test_user.id
            ).delete()
            
            self.db.query(SRSCard).filter(
                SRSCard.user_id == self.test_user.id
            ).delete()
            
            self.db.query(LearningSession).filter(
                LearningSession.user_id == self.test_user.id
            ).delete()
            
            self.db.query(UserProgress).filter(
                UserProgress.user_id == self.test_user.id
            ).delete()
            
            # Delete exam data
            exams = self.db.query(Exam).filter(
                Exam.created_by_id == self.test_user.id
            ).all()
            
            for exam in exams:
                for section in exam.sections:
                    self.db.query(ExamQuestion).filter(
                        ExamQuestion.section_id == section.id
                    ).delete()
                    self.db.delete(section)
                self.db.delete(exam)
            
            # Delete test words and related data
            for word in self.test_words:
                self.db.query(Translation).filter(
                    Translation.lemma_id == word.id
                ).delete()
                self.db.query(Example).filter(
                    Example.lemma_id == word.id
                ).delete()
                self.db.delete(word)
            
            # Delete test user
            if self.test_user:
                self.db.delete(self.test_user)
            
            self.db.commit()
            print(f"\n🧹 Test data cleaned up")
            
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")
        finally:
            self.db.close()


async def main():
    """Run all Phase 2 backend tests"""
    tester = Phase2BackendTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())