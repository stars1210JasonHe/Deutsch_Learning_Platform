#!/usr/bin/env python3
"""
Find verbs with complete conjugation data (all 5 tenses)
"""
import sqlite3

def find_complete_verbs():
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    # Find verbs that have conjugation data
    cursor.execute("""
        SELECT DISTINCT wl.lemma, wl.id
        FROM word_lemmas wl
        JOIN word_forms wf ON wl.id = wf.lemma_id
        WHERE wl.pos = 'verb' AND wf.feature_key = 'tense'
        ORDER BY wl.lemma
        LIMIT 20
    """)
    
    verbs_with_forms = cursor.fetchall()
    print(f"Found {len(verbs_with_forms)} verbs with conjugation forms:")
    
    complete_verbs = []
    
    for lemma, lemma_id in verbs_with_forms:
        # Get all tenses for this verb
        cursor.execute("""
            SELECT DISTINCT feature_value 
            FROM word_forms 
            WHERE lemma_id = ? AND feature_key = 'tense'
            ORDER BY feature_value
        """, (lemma_id,))
        
        tenses = [row[0] for row in cursor.fetchall()]
        
        try:
            print(f"  {lemma}: {len(tenses)} tenses")
        except UnicodeEncodeError:
            print(f"  [German word]: {len(tenses)} tenses")
        
        # Check if has all 5 required tenses
        required_tenses = {'präsens', 'präteritum', 'perfekt', 'plusquamperfekt', 'imperativ'}
        present_tenses = set(tenses)
        
        if required_tenses.issubset(present_tenses):
            complete_verbs.append((lemma, lemma_id))
            try:
                print(f"    -> COMPLETE! Has all 5 tenses")
            except UnicodeEncodeError:
                print(f"    -> COMPLETE! Has all 5 tenses")
    
    print(f"\n=== COMPLETE VERBS ({len(complete_verbs)}) ===")
    for lemma, lemma_id in complete_verbs:
        try:
            print(f"  {lemma} (ID: {lemma_id})")
        except UnicodeEncodeError:
            print(f"  [German word] (ID: {lemma_id})")
    
    # Test one complete verb if found
    if complete_verbs:
        test_lemma, test_id = complete_verbs[0]
        print(f"\n=== Testing verb conjugations for ID {test_id} ===")
        
        cursor.execute("""
            SELECT feature_value, form
            FROM word_forms 
            WHERE lemma_id = ? AND feature_key = 'tense'
            ORDER BY feature_value, form
        """, (test_id,))
        
        forms = cursor.fetchall()
        for tense, form in forms[:10]:  # Show first 10 forms
            try:
                print(f"  {tense}: {form}")
            except UnicodeEncodeError:
                print(f"  {tense}: [German form]")
    
    conn.close()

if __name__ == "__main__":
    find_complete_verbs()