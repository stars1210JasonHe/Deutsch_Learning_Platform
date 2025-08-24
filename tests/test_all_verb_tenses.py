#!/usr/bin/env python3
"""
Test all available verb tenses and the service formatting
"""
import sys
import os
import sqlite3
from collections import defaultdict

sys.path.append(os.getcwd())

def test_verb_tenses():
    """Test verb tenses available in database and how they're formatted"""
    
    print("=== Testing Verb Tenses ===")
    
    # Connect to database
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    # Get a verb with lots of conjugations
    cursor.execute("""
        SELECT lemma, id 
        FROM word_lemmas 
        WHERE pos = 'verb' AND lemma IN ('fahren', 'haben', 'sein', 'gehen', 'bringen')
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
    
    forms = cursor.fetchall()
    print(f"Found {len(forms)} verb forms")
    
    # Group by tense (extract tense from feature_value)
    tense_groups = defaultdict(dict)
    
    for feature_key, feature_value, form in forms:
        if "_" in feature_value:
            tense, person = feature_value.split("_", 1)
            tense_groups[tense][person] = form
    
    print(f"\nAvailable tenses ({len(tense_groups)} total):")
    for tense, persons in tense_groups.items():
        try:
            print(f"  {tense}: {len(persons)} forms")
        except UnicodeEncodeError:
            print(f"  [tense]: {len(persons)} forms")
    
    # Test the vocabulary service formatting
    print(f"\n=== Testing Service Formatting ===")
    try:
        from app.services.vocabulary_service import VocabularyService
        from app.models.word_lemma import WordForm
        
        # Create mock WordForm objects
        mock_forms = []
        for feature_key, feature_value, form in forms:
            mock_form = type('MockWordForm', (), {
                'feature_key': feature_key,
                'feature_value': feature_value, 
                'form': form
            })()
            mock_forms.append(mock_form)
        
        # Test the formatting method
        service = VocabularyService()
        tables = service._format_verb_tables(mock_forms)
        
        if tables:
            print(f"Service returned {len(tables)} tenses:")
            for tense, forms in tables.items():
                try:
                    print(f"  {tense}: {list(forms.keys())[:3]}...")  # Show first 3 persons
                except UnicodeEncodeError:
                    print(f"  [tense]: {len(forms)} persons")
        else:
            print("Service returned no tables!")
            
    except Exception as e:
        print(f"Service test failed: {e}")
    
    # Frontend compatibility check
    print(f"\n=== Frontend Compatibility ===")
    frontend_tenses = [
        'praesens', 'präsens',           # Present (both spellings)
        'praeteritum', 'präteritum',     # Simple past (both spellings) 
        'perfekt',                       # Present perfect
        'plusquamperfekt',               # Past perfect
        'futur_i', 'futur1',             # Future I (both spellings)
        'futur_ii', 'futur2',            # Future II (both spellings)
        'imperativ',                     # Commands
        'konjunktiv_i',                  # Subjunctive I
        'konjunktiv_ii'                  # Subjunctive II
    ]
    
    available_tenses = set(tense_groups.keys())
    print(f"Database has: {sorted(available_tenses)}")
    
    frontend_supported = []
    missing_from_frontend = []
    
    for tense in available_tenses:
        # Check if frontend supports this tense (any variant)
        supported = False
        for frontend_tense in frontend_tenses:
            if tense == frontend_tense or tense.replace('ä', 'ae').replace('ü', 'ue') == frontend_tense:
                supported = True
                break
        
        if supported:
            frontend_supported.append(tense)
        else:
            missing_from_frontend.append(tense)
    
    print(f"\nFrontend supported tenses ({len(frontend_supported)}):")
    for tense in frontend_supported:
        try:
            print(f"  ✓ {tense}")
        except UnicodeEncodeError:
            print(f"  OK [tense]")
    
    if missing_from_frontend:
        print(f"\nTenses missing from frontend ({len(missing_from_frontend)}):")
        for tense in missing_from_frontend:
            try:
                print(f"  ✗ {tense}")
            except UnicodeEncodeError:
                print(f"  X [tense]")
    
    conn.close()

if __name__ == "__main__":
    test_verb_tenses()