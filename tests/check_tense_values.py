#!/usr/bin/env python3
"""
Check what tense values actually exist in the database
"""
import sqlite3

def check_tense_values():
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    # Get all unique tense values
    cursor.execute("""
        SELECT DISTINCT feature_value, COUNT(*) as count
        FROM word_forms 
        WHERE feature_key = 'tense'
        GROUP BY feature_value
        ORDER BY feature_value
    """)
    
    tense_values = cursor.fetchall()
    print("All tense values in database:")
    
    for tense, count in tense_values:
        try:
            print(f"  {tense}: {count} forms")
        except UnicodeEncodeError:
            print(f"  [tense]: {count} forms")
    
    # Check if we have the expected German tense names
    expected_tenses = ['präsens', 'präteritum', 'perfekt', 'plusquamperfekt', 'imperativ']
    
    print(f"\nLooking for expected tenses:")
    found_tenses = [row[0] for row in tense_values]
    
    for expected in expected_tenses:
        if expected in found_tenses:
            try:
                print(f"  ✓ {expected} - FOUND")
            except UnicodeEncodeError:
                print(f"  OK {expected} - FOUND")
        else:
            try:
                print(f"  ✗ {expected} - MISSING")
            except UnicodeEncodeError:
                print(f"  X {expected} - MISSING")
    
    # Check one specific verb to see its forms
    cursor.execute("""
        SELECT wl.lemma, wf.feature_value, wf.form
        FROM word_lemmas wl
        JOIN word_forms wf ON wl.id = wf.lemma_id
        WHERE wl.pos = 'verb' AND wf.feature_key = 'tense' AND wl.lemma = 'fahren'
        ORDER BY wf.feature_value
        LIMIT 15
    """)
    
    verb_forms = cursor.fetchall()
    if verb_forms:
        print(f"\nExample verb 'fahren' conjugations:")
        for lemma, tense, form in verb_forms:
            try:
                print(f"  {tense}: {form}")
            except UnicodeEncodeError:
                print(f"  {tense}: [form]")
    
    conn.close()

if __name__ == "__main__":
    check_tense_values()