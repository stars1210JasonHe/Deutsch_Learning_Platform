"""
Test script for trinke search redirect
"""
import asyncio
from app.core.deps import get_db
from app.services.enhanced_search_service import EnhancedSearchService
from app.models.user import User

async def test_search():
    print('=== TESTING ENHANCED SEARCH FOR trinke ===')
    
    # Create a dummy database session
    db = next(get_db())
    
    # Create a dummy user
    user = User(id=1, username='test', email='test@test.com')
    
    # Create enhanced search service
    enhanced_search = EnhancedSearchService()
    
    # Test search for trinke
    try:
        result = await enhanced_search.search_with_suggestions(
            db=db,
            query='trinke',
            user=user,
            max_suggestions=5
        )
        
        print('Search result for trinke:')
        print(f'Found: {result.get("found")}')
        if result.get('found'):
            word_data = result.get("word", {})
            print(f'Word: {word_data.get("lemma", "N/A")}')
            print(f'Source: {result.get("source")}')
            if result.get('inflection_info'):
                print(f'Inflection info: {result["inflection_info"]}')
        else:
            print(f'Message: {result.get("message")}')
            suggestions = result.get('suggestions_with_scores', [])
            print(f'Suggestions: {len(suggestions)}')
            for s in suggestions[:3]:
                print(f'  - {s.get("word")} (similarity: {s.get("similarity")})')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_search())