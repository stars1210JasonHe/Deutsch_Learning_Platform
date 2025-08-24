#!/usr/bin/env python3
"""
Test the search for Äpfel to reproduce the error.
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import asyncio
from app.services.enhanced_search_service import EnhancedSearchService
from app.db.session import SessionLocal


async def test_apfel_search():
    """Test searching for Äpfel to see the error"""
    
    print("Testing search for 'Äpfel'...")
    
    db = SessionLocal()
    
    try:
        search_service = EnhancedSearchService()
        
        # Test the search that's failing
        result = await search_service.search_word(db, "Äpfel")
        
        print("Search result:", result)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_apfel_search())