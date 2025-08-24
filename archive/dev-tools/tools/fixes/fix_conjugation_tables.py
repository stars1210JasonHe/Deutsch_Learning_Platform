"""
Fix conjugation tables with wrong base forms
"""
import sqlite3
import sys
import os

def fix_conjugation_tables():
    """Fix conjugation tables that still reference incorrect forms"""
    
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    print("=== FIXING CONJUGATION TABLES ===")
    
    # 1. Fix "isst" forms - these should be "isst" for du/er_sie_es forms of "essen"
    print("\n1. Checking 'isst' forms...")
    cursor.execute('SELECT lemma_id, feature_key, feature_value FROM word_forms WHERE form = "isst"')
    isst_entries = cursor.fetchall()
    
    for lemma_id, feature_key, feature_value in isst_entries:
        # Check which verb this belongs to
        cursor.execute('SELECT lemma FROM word_lemmas WHERE id = ?', (lemma_id,))
        lemma_result = cursor.fetchone()
        
        if lemma_result:
            verb_lemma = lemma_result[0]
            print(f"  Found 'isst' form for verb '{verb_lemma}' (ID {lemma_id})")
            
            # If this is "essen", "isst" is actually correct for du/er_sie_es
            if verb_lemma == "essen" and feature_value in ["praesens_du", "praesens_er_sie_es"]:
                print(f"    OK: 'isst' is correct for {feature_value} of 'essen'")
            else:
                print(f"    ERROR: 'isst' should not be used for {feature_value} of '{verb_lemma}'")
        else:
            print(f"  ERROR: Orphaned 'isst' form with lemma_id {lemma_id}")
    
    # 2. Fix "werde" forms - these should be "werde" for ich form of "werden" 
    print("\n2. Checking 'werde' forms...")
    cursor.execute('SELECT lemma_id, feature_key, feature_value FROM word_forms WHERE form = "werde"')
    werde_entries = cursor.fetchall()
    
    for lemma_id, feature_key, feature_value in werde_entries:
        # Check which verb this belongs to
        cursor.execute('SELECT lemma FROM word_lemmas WHERE id = ?', (lemma_id,))
        lemma_result = cursor.fetchone()
        
        if lemma_result:
            verb_lemma = lemma_result[0]
            print(f"  Found 'werde' form for verb '{verb_lemma}' (ID {lemma_id})")
            
            # If this is "werden", "werde" is correct for ich, but not for imperativ_du
            if verb_lemma == "werden":
                if feature_value == "praesens_ich":
                    print(f"    OK: 'werde' is correct for {feature_value} of 'werden'")
                elif feature_value == "imperativ_du":
                    print(f"    ERROR: 'werde' should be 'wird' for imperativ_du of 'werden'")
                    # Fix the imperativ form
                    cursor.execute(
                        'UPDATE word_forms SET form = "wird" WHERE lemma_id = ? AND feature_value = "imperativ_du"',
                        (lemma_id,)
                    )
                    print(f"    FIXED: imperativ_du 'werde' -> 'wird'")
            else:
                print(f"    ERROR: 'werde' should not be used for '{verb_lemma}'")
        else:
            print(f"  ERROR: Orphaned 'werde' form with lemma_id {lemma_id}")
    
    # 3. Clean up orphaned word_forms
    print("\n3. Cleaning up orphaned word_forms...")
    cursor.execute('''
        DELETE FROM word_forms 
        WHERE lemma_id NOT IN (SELECT id FROM word_lemmas)
    ''')
    orphaned_deleted = cursor.rowcount
    print(f"  DELETED: {orphaned_deleted} orphaned word_forms")
    
    # 4. Verify conjugations for corrected verbs
    print("\n4. Verifying conjugations for corrected verbs...")
    corrected_verbs = ['trinken', 'kommen', 'wollen', 'essen', 'werden']
    
    for verb in corrected_verbs:
        cursor.execute('SELECT id FROM word_lemmas WHERE lemma = ? AND pos = "verb"', (verb,))
        result = cursor.fetchone()
        if result:
            lemma_id = result[0]
            cursor.execute('SELECT COUNT(*) FROM word_forms WHERE lemma_id = ?', (lemma_id,))
            form_count = cursor.fetchone()[0]
            print(f"  {verb} (ID {lemma_id}): {form_count} conjugation forms")
            
            # Check for essential conjugation forms
            essential_forms = ['praesens_ich', 'praesens_du', 'praesens_er_sie_es']
            for form_type in essential_forms:
                cursor.execute(
                    'SELECT form FROM word_forms WHERE lemma_id = ? AND feature_value = ?',
                    (lemma_id, form_type)
                )
                form_result = cursor.fetchone()
                if form_result:
                    print(f"    {form_type}: {form_result[0]}")
                else:
                    print(f"    MISSING: {form_type}")
    
    conn.commit()
    conn.close()
    print("\nCONJUGATION TABLE FIXES COMPLETED!")

if __name__ == "__main__":
    fix_conjugation_tables()