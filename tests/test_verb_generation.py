#!/usr/bin/env python3
"""
Test verb conjugation generation
"""
import asyncio
import sqlite3
import json
from complete_collins_rebuild import CompleteCollinsRebuilder

async def test_verb_conjugation():
    """Test complete verb conjugation generation"""
    
    rebuilder = CompleteCollinsRebuilder()
    
    # Test with a verb entry
    test_entry = {
        "lemma": "gehen",
        "pos": "verb",
        "translations": ["to go", "to walk"],
        "basic_info": {}
    }
    
    print("Testing verb: gehen")
    
    try:
        # Generate complete verb data
        complete_data = await rebuilder.generate_complete_verb_data(
            test_entry["lemma"],
            test_entry["translations"]
        )
        
        print("Generated verb data:")
        
        # Show tables structure
        if complete_data.get('tables'):
            tables = complete_data['tables']
            for tense, forms in tables.items():
                print(f"\n{tense}:")
                if isinstance(forms, dict):
                    for person, form in forms.items():
                        print(f"  {person}: {form}")
        
        # Show verb properties
        if complete_data.get('verb_props'):
            print("\nVerb properties:")
            for key, value in complete_data['verb_props'].items():
                print(f"  {key}: {value}")
        
        # Show examples
        if complete_data.get('examples'):
            print("\nExamples:")
            for ex in complete_data['examples']:
                print(f"  DE: {ex.get('de', '')}")
                print(f"  EN: {ex.get('en', '')}")
        
        # Save to database
        success = rebuilder.save_complete_entry(
            test_entry["lemma"],
            test_entry["pos"],
            complete_data
        )
        
        print(f"\nSave result: {success}")
        
        if success:
            # Check how many word forms were saved
            conn = sqlite3.connect('data/app.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM word_forms wf
                JOIN word_lemmas wl ON wf.lemma_id = wl.id
                WHERE wl.lemma = 'gehen'
            """)
            
            form_count = cursor.fetchone()[0]
            print(f"Saved {form_count} word forms for conjugation")
            
            # Check examples
            cursor.execute("""
                SELECT COUNT(*) FROM examples e
                JOIN word_lemmas wl ON e.lemma_id = wl.id  
                WHERE wl.lemma = 'gehen'
            """)
            
            example_count = cursor.fetchone()[0]
            print(f"Saved {example_count} examples")
            
            conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_verb_conjugation())