#!/usr/bin/env python3
"""
Test the complete flow: search unknown word -> OpenAI -> save to database -> frontend format
"""
import asyncio
import sys
import os
import sqlite3

sys.path.append(os.getcwd())

async def test_complete_flow():
    """Test complete flow for unknown word"""
    
    print("=== Testing Complete Enhanced Flow ===")
    
    # Use a word that's unlikely to be in database
    test_word = "mitspielen"  # "to play along"
    print(f"Testing with word: {test_word}")
    
    try:
        from app.core.deps import get_db
        from app.services.vocabulary_service import VocabularyService
        from app.models.user import User
        
        # Create database session
        db = next(get_db())
        
        # Create mock user
        mock_user = User(id=1, email="test@example.com", password_hash="mock")
        
        # Initialize service
        vocab_service = VocabularyService()
        
        # Check if word exists in database first
        conn = sqlite3.connect('data/app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM word_lemmas WHERE lemma = ?", (test_word,))
        exists_before = cursor.fetchone()[0] > 0
        conn.close()
        
        print(f"Word exists in database before test: {exists_before}")
        
        if exists_before:
            print("Word already exists, using different test word...")
            test_word = "mittanzen"  # "to dance along"
            print(f"New test word: {test_word}")
        
        # Test the complete flow
        print("Calling vocabulary service...")
        result = await vocab_service.get_or_create_word(db, test_word, mock_user)
        
        print(f"\nService Response:")
        print(f"  Found: {result.get('found', False)}")
        print(f"  POS: {result.get('pos', 'unknown')}")
        print(f"  Source: {result.get('source', 'unknown')}")
        
        tables = result.get('tables', {})
        if tables:
            print(f"  Frontend tenses: {len(tables)}")
            for tense_name in tables.keys():
                person_count = len(tables[tense_name]) if isinstance(tables[tense_name], dict) else 0
                print(f"    - {tense_name}: {person_count} forms")
        
        # Check database after
        conn = sqlite3.connect('data/app.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM word_lemmas WHERE lemma = ?", (test_word,))
        lemma_result = cursor.fetchone()
        
        if lemma_result:
            lemma_id = lemma_result[0]
            print(f"\n  Word saved to database with ID: {lemma_id}")
            
            # Check tenses in database
            cursor.execute("""
                SELECT DISTINCT SUBSTRING(feature_value, 1, 
                    CASE 
                        WHEN INSTR(feature_value, '_') > 0 
                        THEN INSTR(feature_value, '_') - 1 
                        ELSE LENGTH(feature_value) 
                    END
                ) as tense
                FROM word_forms 
                WHERE lemma_id = ? AND feature_key = 'tense'
            """, (lemma_id,))
            
            db_tenses = [row[0] for row in cursor.fetchall()]
            print(f"  Database tenses: {len(db_tenses)}")
            for tense in db_tenses:
                print(f"    - {tense}")
            
            # Count total forms
            cursor.execute("SELECT COUNT(*) FROM word_forms WHERE lemma_id = ?", (lemma_id,))
            total_forms = cursor.fetchone()[0]
            print(f"  Total forms in database: {total_forms}")
            
            if len(db_tenses) >= 8:  # Should have most/all tenses
                print(f"  SUCCESS: Word has comprehensive tense coverage!")
            elif len(db_tenses) >= 5:
                print(f"  GOOD: Word has core tenses covered!")
            else:
                print(f"  WARNING: Limited tense coverage")
        else:
            print("  Word was not saved to database")
        
        conn.close()
        
    except Exception as e:
        print(f"Error in complete flow test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_flow())