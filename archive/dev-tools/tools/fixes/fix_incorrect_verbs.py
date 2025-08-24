"""
Fix incorrect verb forms automatically
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fix_verbs():
    """Fix known incorrect verb forms"""
    
    # Direct corrections
    corrections = {
        'trinke': 'trinken',
        'Kommst': 'kommen',
        'Willst': 'wollen', 
        'isst': 'essen',
        'werde': 'werden',
        'Show': '',  # Delete this - not German
    }
    
    # Special cases to update  
    special_updates = {
        'erinnern (sich)': 'sich erinnern',
        'fertig sein': 'fertig sein',  # This is actually correct as compound
        'leid tun': 'leidtun',
        'unterhalten (sich)': 'sich unterhalten', 
        'zu sein': '',  # Delete - this is not a verb lemma
    }
    
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    print("=== FIXING VERB FORMS ===")
    
    fixed_count = 0
    deleted_count = 0
    
    # Fix direct corrections
    for wrong_form, correct_form in corrections.items():
        if not correct_form:  # Delete entry
            try:
                cursor.execute('SELECT id FROM word_lemmas WHERE lemma = ? AND pos = "verb"', (wrong_form,))
                result = cursor.fetchone()
                if result:
                    verb_id = result[0]
                    
                    # Delete word forms first
                    cursor.execute('DELETE FROM word_forms WHERE lemma_id = ?', (verb_id,))
                    # Delete translations
                    cursor.execute('DELETE FROM translations WHERE lemma_id = ?', (verb_id,))
                    # Delete examples
                    cursor.execute('DELETE FROM examples WHERE lemma_id = ?', (verb_id,))
                    # Delete the verb itself
                    cursor.execute('DELETE FROM word_lemmas WHERE id = ?', (verb_id,))
                    
                    print(f"DELETED: '{wrong_form}' (not a German verb)")
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting '{wrong_form}': {e}")
        else:  # Update entry
            try:
                cursor.execute(
                    'UPDATE word_lemmas SET lemma = ? WHERE lemma = ? AND pos = "verb"',
                    (correct_form, wrong_form)
                )
                if cursor.rowcount > 0:
                    print(f"FIXED: '{wrong_form}' -> '{correct_form}'")
                    fixed_count += 1
            except Exception as e:
                print(f"Error fixing '{wrong_form}': {e}")
    
    # Fix special cases
    for wrong_form, correct_form in special_updates.items():
        if not correct_form:  # Delete
            try:
                cursor.execute('SELECT id FROM word_lemmas WHERE lemma = ? AND pos = "verb"', (wrong_form,))
                result = cursor.fetchone()
                if result:
                    verb_id = result[0]
                    cursor.execute('DELETE FROM word_forms WHERE lemma_id = ?', (verb_id,))
                    cursor.execute('DELETE FROM translations WHERE lemma_id = ?', (verb_id,))
                    cursor.execute('DELETE FROM examples WHERE lemma_id = ?', (verb_id,))
                    cursor.execute('DELETE FROM word_lemmas WHERE id = ?', (verb_id,))
                    print(f"DELETED: '{wrong_form}'")
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting '{wrong_form}': {e}")
        else:  # Update
            try:
                cursor.execute(
                    'UPDATE word_lemmas SET lemma = ? WHERE lemma = ? AND pos = "verb"',
                    (correct_form, wrong_form)
                )
                if cursor.rowcount > 0:
                    print(f"UPDATED: '{wrong_form}' -> '{correct_form}'")
                    fixed_count += 1
            except Exception as e:
                print(f"Error updating '{wrong_form}': {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n=== RESULTS ===")
    print(f"Fixed: {fixed_count} verbs")
    print(f"Deleted: {deleted_count} invalid entries")
    print(f"Total changes: {fixed_count + deleted_count}")

if __name__ == "__main__":
    fix_verbs()