#!/usr/bin/env python3
"""
Test the updated dynamic tense system
"""
import sys
import os
import asyncio
import sqlite3
from collections import defaultdict

sys.path.append(os.getcwd())

# Mock WordForm for testing
class MockWordForm:
    def __init__(self, feature_key, feature_value, form):
        self.feature_key = feature_key
        self.feature_value = feature_value
        self.form = form

async def test_dynamic_tenses():
    """Test the updated tense formatting system"""
    
    print("=== Testing Dynamic Tense System ===")
    
    # Get verb data from database
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    # Get a verb with lots of conjugations
    cursor.execute("""
        SELECT lemma, id 
        FROM word_lemmas 
        WHERE pos = 'verb' AND lemma IN ('fahren', 'haben', 'sein', 'gehen')
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if not result:
        print("No suitable verb found!")
        return
        
    lemma, lemma_id = result
    try:
        print(f"Testing verb: {lemma} (ID: {lemma_id})")
    except UnicodeEncodeError:
        print(f"Testing verb: [German word] (ID: {lemma_id})")
    
    # Get all forms for this verb
    cursor.execute("""
        SELECT feature_key, feature_value, form
        FROM word_forms 
        WHERE lemma_id = ? AND feature_key = 'tense'
        ORDER BY feature_value
    """, (lemma_id,))
    
    forms_data = cursor.fetchall()
    conn.close()
    
    # Create MockWordForm objects
    mock_forms = []
    for feature_key, feature_value, form in forms_data:
        mock_forms.append(MockWordForm(feature_key, feature_value, form))
    
    print(f"Found {len(mock_forms)} conjugation forms")
    
    # Test the updated vocabulary service
    try:
        from app.services.vocabulary_service import VocabularyService
        service = VocabularyService()
        
        # Format the tables
        tables = service._format_verb_tables(mock_forms)
        
        if tables:
            print(f"\n=== Service Results ({len(tables)} tenses) ===")
            
            for tense, persons in tables.items():
                try:
                    print(f"\n{tense.upper()}:")
                    for person, form in list(persons.items())[:3]:  # Show first 3 persons
                        print(f"  {person}: {form}")
                    if len(persons) > 3:
                        print(f"  ... and {len(persons)-3} more forms")
                except UnicodeEncodeError:
                    print(f"\n[TENSE]: {len(persons)} forms")
            
            # Test frontend compatibility
            print(f"\n=== Frontend Compatibility Test ===")
            
            expected_frontend_tenses = [
                'praesens', 'praeteritum', 'perfekt', 'plusquamperfekt',
                'imperativ', 'futur_i', 'futur_ii', 'konjunktiv_i', 'konjunktiv_ii'
            ]
            
            available_tenses = set(tables.keys())
            supported_count = 0
            
            for expected in expected_frontend_tenses:
                if expected in available_tenses:
                    supported_count += 1
                    try:
                        print(f"  ✓ {expected} - Available ({len(tables[expected])} forms)")
                    except UnicodeEncodeError:
                        print(f"  OK [tense] - Available")
                else:
                    try:
                        print(f"  ✗ {expected} - Missing")
                    except UnicodeEncodeError:
                        print(f"  X [tense] - Missing")
            
            print(f"\nFrontend compatibility: {supported_count}/{len(expected_frontend_tenses)} tenses supported")
            
            # Show any additional tenses not in expected list
            additional_tenses = available_tenses - set(expected_frontend_tenses)
            if additional_tenses:
                print(f"Additional tenses available: {list(additional_tenses)}")
            
        else:
            print("❌ Service returned no tables!")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Service test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_dynamic_tenses())