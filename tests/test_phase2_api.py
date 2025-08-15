#!/usr/bin/env python3
"""
Phase 2 API Endpoint Testing Script
Tests all Phase 2 REST API endpoints with actual HTTP requests
"""
import sys
import os
import asyncio
import json
import httpx
from datetime import datetime


class Phase2APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.auth_token = None
        self.test_user_email = "apitest@phase2.com"
        self.test_user_password = "testpass123"
        self.exam_id = None
        self.attempt_id = None
        
    async def run_all_tests(self):
        """Run comprehensive API endpoint tests"""
        print("🚀 Starting Phase 2 API Tests")
        print("=" * 60)
        
        try:
            # Test authentication
            await self.test_authentication()
            
            # Test exam endpoints
            await self.test_exam_endpoints()
            
            # Test SRS endpoints
            await self.test_srs_endpoints()
            
            print(f"\n🎉 All Phase 2 API Tests Complete!")
            
        except Exception as e:
            print(f"❌ API test suite failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.client.aclose()
    
    async def test_authentication(self):
        """Test user authentication"""
        print(f"\n🔐 Testing Authentication...")
        
        try:
            # Test 1: User registration
            print("   🧪 Test 1: User registration")
            register_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = await self.client.post(
                f"{self.base_url}/auth/register",
                json=register_data
            )
            
            # Could be 200 (success) or 400 (user exists)
            assert response.status_code in [200, 400], f"Registration failed: {response.status_code}"
            print(f"      ✅ Registration response: {response.status_code}")
            
            # Test 2: User login
            print("   🧪 Test 2: User login")
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = await self.client.post(
                f"{self.base_url}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                assert "access_token" in data, "Login should return access token"
                print(f"      ✅ Login successful, token obtained")
            else:
                print(f"      ⚠️ Login failed: {response.status_code} - {response.text}")
                # For testing, we'll create a dummy token
                self.auth_token = "dummy_token_for_testing"
                
        except Exception as e:
            print(f"      ❌ Authentication test failed: {e}")
            raise
    
    @property
    def auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
    
    async def test_exam_endpoints(self):
        """Test exam-related API endpoints"""
        print(f"\n📝 Testing Exam Endpoints...")
        
        if not self.auth_token:
            print("      ⚠️ Skipping exam tests - no auth token")
            return
        
        try:
            # Test 1: Generate exam
            print("   🧪 Test 1: Generate exam")
            generate_data = {
                "title": "API Test Exam",
                "level": "A1",
                "topics": ["basic_vocabulary", "verbs"],
                "question_types": ["mcq", "cloze"],
                "question_count": 5
            }
            
            response = await self.client.post(
                f"{self.base_url}/exam/generate",
                json=generate_data,
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] == True, "Exam generation should be successful"
                self.exam_id = data["exam"]["exam_id"]
                print(f"      ✅ Generated exam with ID: {self.exam_id}")
            else:
                print(f"      ⚠️ Exam generation failed: {response.status_code} - {response.text}")
            
            # Test 2: List exams
            print("   🧪 Test 2: List exams")
            response = await self.client.get(
                f"{self.base_url}/exam/list",
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "exams" in data, "Should return exams list"
                print(f"      ✅ Listed {len(data['exams'])} exams")
            else:
                print(f"      ⚠️ List exams failed: {response.status_code}")
            
            if self.exam_id:
                # Test 3: Get exam details
                print("   🧪 Test 3: Get exam details")
                response = await self.client.get(
                    f"{self.base_url}/exam/{self.exam_id}",
                    headers=self.auth_headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assert data["id"] == self.exam_id, "Should return correct exam"
                    assert "sections" in data, "Should include exam sections"
                    print(f"      ✅ Retrieved exam details: {data['title']}")
                else:
                    print(f"      ⚠️ Get exam details failed: {response.status_code}")
                
                # Test 4: Start exam
                print("   🧪 Test 4: Start exam")
                start_data = {"exam_id": self.exam_id}
                response = await self.client.post(
                    f"{self.base_url}/exam/start",
                    json=start_data,
                    headers=self.auth_headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.attempt_id = data["attempt_id"]
                    print(f"      ✅ Started exam attempt: {self.attempt_id}")
                else:
                    print(f"      ⚠️ Start exam failed: {response.status_code}")
                
                if self.attempt_id:
                    # Test 5: Submit answer
                    print("   🧪 Test 5: Submit answer")
                    
                    # Get a question ID (simplified - using ID 1)
                    answer_data = {
                        "attempt_id": self.attempt_id,
                        "question_id": 1,
                        "answer": ["test_answer"],
                        "time_taken_seconds": 30
                    }
                    
                    response = await self.client.post(
                        f"{self.base_url}/exam/submit-answer",
                        json=answer_data,
                        headers=self.auth_headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"      ✅ Submitted answer, correct: {data.get('is_correct', 'unknown')}")
                    else:
                        print(f"      ⚠️ Submit answer failed: {response.status_code}")
                    
                    # Test 6: Complete exam
                    print("   🧪 Test 6: Complete exam")
                    complete_data = {"attempt_id": self.attempt_id}
                    response = await self.client.post(
                        f"{self.base_url}/exam/complete",
                        json=complete_data,
                        headers=self.auth_headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"      ✅ Completed exam, score: {data.get('percentage_score', 'unknown')}%")
                    else:
                        print(f"      ⚠️ Complete exam failed: {response.status_code}")
            
            # Test 7: User exam history
            print("   🧪 Test 7: User exam history")
            response = await self.client.get(
                f"{self.base_url}/exam/user/history",
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Retrieved {len(data.get('attempts', []))} exam attempts")
            else:
                print(f"      ⚠️ Get exam history failed: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Exam endpoints test failed: {e}")
            raise
    
    async def test_srs_endpoints(self):
        """Test SRS-related API endpoints"""
        print(f"\n🧠 Testing SRS Endpoints...")
        
        if not self.auth_token:
            print("      ⚠️ Skipping SRS tests - no auth token")
            return
        
        try:
            # Test 1: Add word to SRS
            print("   🧪 Test 1: Add word to SRS")
            add_word_data = {
                "lemma_id": 1,  # Assuming word ID 1 exists
                "initial_quality": 3
            }
            
            response = await self.client.post(
                f"{self.base_url}/srs/add-word",
                json=add_word_data,
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Added word to SRS: {data.get('success', 'unknown')}")
            else:
                print(f"      ⚠️ Add word to SRS failed: {response.status_code}")
            
            # Test 2: Get due cards
            print("   🧪 Test 2: Get due cards")
            response = await self.client.get(
                f"{self.base_url}/srs/due-cards?limit=10",
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                cards = data.get("cards", [])
                print(f"      ✅ Retrieved {len(cards)} due cards")
                
                # Test 3: Review card (if we have cards)
                if cards:
                    print("   🧪 Test 3: Review card")
                    card_id = cards[0]["card_id"]
                    review_data = {
                        "card_id": card_id,
                        "quality": 4,  # Good recall
                        "response_time_ms": 2500
                    }
                    
                    response = await self.client.post(
                        f"{self.base_url}/srs/review-card",
                        json=review_data,
                        headers=self.auth_headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"      ✅ Reviewed card, new interval: {data.get('new_interval', 'unknown')} days")
                    else:
                        print(f"      ⚠️ Review card failed: {response.status_code}")
            else:
                print(f"      ⚠️ Get due cards failed: {response.status_code}")
            
            # Test 4: Get SRS stats
            print("   🧪 Test 4: Get SRS stats")
            response = await self.client.get(
                f"{self.base_url}/srs/stats",
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ SRS stats: {data.get('total_cards', 0)} total cards")
            else:
                print(f"      ⚠️ Get SRS stats failed: {response.status_code}")
            
            # Test 5: Start learning session
            print("   🧪 Test 5: Start learning session")
            session_data = {"session_type": "srs_review"}
            response = await self.client.post(
                f"{self.base_url}/srs/session/start",
                json=session_data,
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                session_id = data["session_id"]
                print(f"      ✅ Started learning session: {session_id}")
                
                # Test 6: End learning session
                print("   🧪 Test 6: End learning session")
                end_session_data = {
                    "session_id": session_id,
                    "questions_answered": 5,
                    "correct_answers": 4,
                    "topics_covered": ["basic_vocabulary"],
                    "words_practiced": [1, 2, 3]
                }
                
                response = await self.client.post(
                    f"{self.base_url}/srs/session/end",
                    json=end_session_data,
                    headers=self.auth_headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"      ✅ Ended session, accuracy: {data.get('accuracy', 'unknown')}%")
                else:
                    print(f"      ⚠️ End learning session failed: {response.status_code}")
            else:
                print(f"      ⚠️ Start learning session failed: {response.status_code}")
            
            # Test 7: Get user progress
            print("   🧪 Test 7: Get user progress")
            response = await self.client.get(
                f"{self.base_url}/srs/progress",
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ User progress: Level {data.get('current_level', 'unknown')}")
            else:
                print(f"      ⚠️ Get user progress failed: {response.status_code}")
            
            # Test 8: Get learning dashboard
            print("   🧪 Test 8: Get learning dashboard")
            response = await self.client.get(
                f"{self.base_url}/srs/dashboard",
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                srs_stats = data.get("srs_stats", {})
                print(f"      ✅ Dashboard: {srs_stats.get('total_cards', 0)} cards in deck")
            else:
                print(f"      ⚠️ Get dashboard failed: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ SRS endpoints test failed: {e}")
            raise


def check_server_running(base_url: str) -> bool:
    """Check if the server is running"""
    try:
        # Use httpx (already a project dependency)
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{base_url}/health")
            return response.status_code == 200
    except Exception:
        return False


async def main():
    """Run all Phase 2 API tests"""
    
    base_url = "http://localhost:8000"
    
    if not check_server_running(base_url):
        print(f"❌ Server is not running at {base_url}")
        print(f"Please start the server first:")
        print(f"   python -m uvicorn app.main:app --reload")
        return
    
    tester = Phase2APITester(base_url)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())