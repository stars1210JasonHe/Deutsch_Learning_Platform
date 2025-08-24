"""
Simple test for essen search
"""
import asyncio
from app.services.enhanced_vocabulary_service import EnhancedVocabularyService
from app.core.deps import get_db

async def test_essen():
    print("=== TESTING ESSEN SEARCH ===")
    
    # Get database session
    db = next(get_db())
    
    # Create dummy user object (minimal)
    class DummyUser:
        def __init__(self):
            self.id = 1
            self.username = "test"
            self.email = "test@test.com"
    
    user = DummyUser()
    
    # Create enhanced service
    service = EnhancedVocabularyService()
    
    try:
        # Test the enhanced lookup
        result = await service.get_or_create_word_enhanced(
            db=db,
            lemma="essen",
            user=user,
            force_enrich=False
        )
        
        print(f"Result found: {result.get('found', False)}")
        print(f"Multiple choices: {result.get('multiple_choices', False)}")
        if result.get('multiple_choices'):
            print(f"Choice count: {result.get('choice_count', 0)}")
            for i, choice in enumerate(result.get('choices', [])):
                print(f"  Choice {i+1}: {choice['display_name']} ({choice['pos_display']})")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_essen())