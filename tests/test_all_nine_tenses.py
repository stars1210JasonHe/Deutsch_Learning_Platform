#!/usr/bin/env python3
"""
Test for verbs with all 9 German tenses
"""
import sqlite3
from collections import defaultdict

def test_nine_tenses():
    """Find verbs that have all 9 German tenses"""
    
    print("=== Testing for Verbs with ALL 9 German Tenses ===")
    
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    # All required German tenses
    required_tenses = [
        'praesens', 'praeteritum', 'perfekt', 'plusquamperfekt', 
        'futur_i', 'futur_ii', 'imperativ', 'konjunktiv_i', 'konjunktiv_ii'
    ]
    
    print(f"Looking for verbs with all {len(required_tenses)} tenses:")
    for tense in required_tenses:
        try:
            print(f"  - {tense}")
        except UnicodeEncodeError:
            print(f"  - [tense]")
    
    # Get verbs with conjugation data
    cursor.execute("""
        SELECT DISTINCT wl.lemma, wl.id
        FROM word_lemmas wl
        JOIN word_forms wf ON wl.id = wf.lemma_id
        WHERE wl.pos = 'verb' AND wf.feature_key = 'tense'
        ORDER BY wl.lemma
    """)
    
    verbs_with_forms = cursor.fetchall()
    print(f"\nFound {len(verbs_with_forms)} verbs with some conjugation forms")
    
    complete_verbs = []
    
    for lemma, lemma_id in verbs_with_forms:
        # Get all tenses for this verb
        cursor.execute("""
            SELECT DISTINCT SUBSTRING(feature_value, 1, INSTR(feature_value, '_') - 1) as tense
            FROM word_forms 
            WHERE lemma_id = ? AND feature_key = 'tense' AND feature_value LIKE '%_%'
            ORDER BY tense
        """, (lemma_id,))
        
        tenses_result = cursor.fetchall()
        verb_tenses = [row[0] for row in tenses_result if row[0]]
        
        # Check if has all required tenses
        has_all_tenses = all(tense in verb_tenses for tense in required_tenses)
        
        if has_all_tenses:
            complete_verbs.append((lemma, lemma_id, verb_tenses))
            try:
                print(f"OK COMPLETE: {lemma} - has all {len(verb_tenses)} tenses")
            except UnicodeEncodeError:
                print(f"✓ COMPLETE: [German verb] - has all {len(verb_tenses)} tenses")
    
    print(f"\n=== RESULTS ===")
    print(f"Verbs with ALL 9 tenses: {len(complete_verbs)}")
    
    if complete_verbs:
        print(f"\nComplete verbs ready for frontend testing:")
        for lemma, lemma_id, tenses in complete_verbs[:5]:  # Show first 5
            try:
                print(f"  - {lemma} (ID: {lemma_id})")
            except UnicodeEncodeError:
                print(f"  - [German verb] (ID: {lemma_id})")
        
        if len(complete_verbs) > 5:
            print(f"  ... and {len(complete_verbs) - 5} more")
        
        # Test one complete verb in detail
        test_lemma, test_id, test_tenses = complete_verbs[0]
        print(f"\n=== DETAILED TEST: {test_id} ===")
        
        cursor.execute("""
            SELECT feature_value, form
            FROM word_forms 
            WHERE lemma_id = ? AND feature_key = 'tense'
            ORDER BY feature_value
        """, (test_id,))
        
        forms = cursor.fetchall()
        
        # Group by tense
        tense_groups = defaultdict(list)
        for feature_value, form in forms:
            if "_" in feature_value:
                tense = feature_value.split("_")[0]
                tense_groups[tense].append(form)
        
        print(f"Tense breakdown:")
        for tense in required_tenses:
            count = len(tense_groups.get(tense, []))
            try:
                print(f"  {tense}: {count} forms")
            except UnicodeEncodeError:
                print(f"  [tense]: {count} forms")
    else:
        print("X No verbs found with all 9 tenses yet.")
        
        # Show what tenses are missing most commonly
        print(f"\nAnalyzing missing tenses...")
        
        tense_counts = defaultdict(int)
        for lemma, lemma_id in verbs_with_forms[:10]:  # Check first 10 verbs
            cursor.execute("""
                SELECT DISTINCT SUBSTRING(feature_value, 1, INSTR(feature_value, '_') - 1) as tense
                FROM word_forms 
                WHERE lemma_id = ? AND feature_key = 'tense' AND feature_value LIKE '%_%'
            """, (lemma_id,))
            
            verb_tenses = [row[0] for row in cursor.fetchall() if row[0]]
            for tense in verb_tenses:
                tense_counts[tense] += 1
        
        print(f"Most common tenses in database:")
        for tense, count in sorted(tense_counts.items(), key=lambda x: x[1], reverse=True):
            try:
                print(f"  {tense}: {count}/10 verbs")
            except UnicodeEncodeError:
                print(f"  [tense]: {count}/10 verbs")
    
    conn.close()

if __name__ == "__main__":
    test_nine_tenses()