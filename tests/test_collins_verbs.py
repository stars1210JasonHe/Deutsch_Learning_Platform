#!/usr/bin/env python3
"""
Test specifically for Collins verbs with 9 tenses
"""
import sqlite3
from collections import defaultdict

def test_collins_verbs():
    """Find Collins verbs and check their tense completeness"""
    
    print("=== Testing Collins Verbs with Enhanced Tenses ===")
    
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    # Get Collins verbs specifically
    cursor.execute("""
        SELECT lemma, id
        FROM word_lemmas 
        WHERE pos = 'verb' AND notes LIKE '%Collins%'
        ORDER BY created_at DESC
        LIMIT 20
    """)
    
    collins_verbs = cursor.fetchall()
    print(f"Found {len(collins_verbs)} Collins verbs")
    
    complete_verbs = []
    
    for lemma, lemma_id in collins_verbs:
        try:
            print(f"\n--- Testing {lemma} (ID: {lemma_id}) ---")
        except UnicodeEncodeError:
            print(f"\n--- Testing [German verb] (ID: {lemma_id}) ---")
        
        # Get all tense forms for this verb
        cursor.execute("""
            SELECT feature_value, form
            FROM word_forms 
            WHERE lemma_id = ? AND feature_key = 'tense'
            ORDER BY feature_value
        """, (lemma_id,))
        
        forms = cursor.fetchall()
        print(f"  Total forms: {len(forms)}")
        
        # Group by tense (extract tense from feature_value like 'praesens_ich')
        tense_groups = defaultdict(list)
        for feature_value, form in forms:
            if "_" in feature_value:
                tense = feature_value.split("_")[0]
                tense_groups[tense].append(form)
        
        print(f"  Available tenses: {list(tense_groups.keys())}")
        
        # Check if has all 9 required tenses
        required_tenses = {
            'praesens', 'praeteritum', 'perfekt', 'plusquamperfekt', 
            'futur_i', 'futur_ii', 'imperativ', 'konjunktiv_i', 'konjunktiv_ii'
        }
        present_tenses = set(tense_groups.keys())
        
        if required_tenses.issubset(present_tenses):
            complete_verbs.append((lemma, lemma_id))
            print(f"  ✅ COMPLETE! Has all 9 tenses")
        else:
            missing = required_tenses - present_tenses
            try:
                print(f"  ❌ Missing: {', '.join(missing)}")
            except UnicodeEncodeError:
                print(f"  X Missing: {len(missing)} tenses")
        
        # Show first few forms as examples
        if forms:
            print(f"  Sample forms:")
            for i, (feature_value, form) in enumerate(forms[:6]):
                try:
                    print(f"    {feature_value}: {form}")
                except UnicodeEncodeError:
                    print(f"    {feature_value}: [German form]")
                if i >= 5:
                    print(f"    ... and {len(forms) - 6} more")
                    break
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Collins verbs with ALL 9 tenses: {len(complete_verbs)}")
    
    if complete_verbs:
        print(f"Complete verbs ready for frontend:")
        for lemma, lemma_id in complete_verbs:
            try:
                print(f"  - {lemma} (ID: {lemma_id})")
            except UnicodeEncodeError:
                print(f"  - [German verb] (ID: {lemma_id})")
    
    conn.close()

if __name__ == "__main__":
    test_collins_verbs()