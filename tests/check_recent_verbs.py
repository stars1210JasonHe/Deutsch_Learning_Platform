#!/usr/bin/env python3
"""
Check recently processed Collins verbs and their conjugation data
"""
import sqlite3
import json

def check_recent_verbs():
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    # Get recent Collins verbs
    cursor.execute("""
        SELECT lemma, id, created_at 
        FROM word_lemmas 
        WHERE notes LIKE '%Collins Dictionary - Complete%' 
        AND pos = 'verb' 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    verbs = cursor.fetchall()
    print(f"Found {len(verbs)} recent Collins verbs:")
    
    for lemma, lemma_id, created_at in verbs:
        print(f"\n--- {lemma} (ID: {lemma_id}) ---")
        
        # Check what tenses exist
        cursor.execute("""
            SELECT DISTINCT feature_value 
            FROM word_forms 
            WHERE lemma_id = ? AND feature_key = 'tense'
            ORDER BY feature_value
        """, (lemma_id,))
        
        tenses = [row[0] for row in cursor.fetchall()]
        print(f"  Tenses: {', '.join(tenses) if tenses else 'None'}")
        
        # Count total forms
        cursor.execute("""
            SELECT COUNT(*) 
            FROM word_forms 
            WHERE lemma_id = ?
        """, (lemma_id,))
        
        total_forms = cursor.fetchone()[0]
        print(f"  Total forms: {total_forms}")
        
        # Check if has all 5 required tenses
        required_tenses = ['präsens', 'präteritum', 'perfekt', 'plusquamperfekt', 'imperativ']
        missing_tenses = [t for t in required_tenses if t not in tenses]
        
        if missing_tenses:
            try:
                print(f"  X Missing: {', '.join(missing_tenses)}")
            except UnicodeEncodeError:
                print(f"  X Missing: {len(missing_tenses)} tenses")
        else:
            print(f"  OK Has all 5 tenses!")
    
    conn.close()

if __name__ == "__main__":
    check_recent_verbs()