"""
Fix the trinke/trinken duplicate issue
"""
import sqlite3

def fix_trinke_duplicate():
    """Handle the trinke/trinken duplicate"""
    
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    print("=== FIXING TRINKE/TRINKEN DUPLICATE ===")
    
    # Find both entries
    cursor.execute('SELECT id, lemma FROM word_lemmas WHERE lemma IN ("trinke", "trinken") AND pos = "verb"')
    results = cursor.fetchall()
    
    print(f"Found entries: {results}")
    
    # Find the IDs
    trinke_id = None
    trinken_id = None
    
    for verb_id, lemma in results:
        if lemma == 'trinke':
            trinke_id = verb_id
        elif lemma == 'trinken':
            trinken_id = verb_id
    
    if trinke_id and trinken_id:
        print(f"Both 'trinke' (ID {trinke_id}) and 'trinken' (ID {trinken_id}) exist")
        
        # Check which one has more data
        cursor.execute('SELECT COUNT(*) FROM word_forms WHERE lemma_id = ?', (trinke_id,))
        trinke_forms = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM word_forms WHERE lemma_id = ?', (trinken_id,))
        trinken_forms = cursor.fetchone()[0]
        
        print(f"'trinke' has {trinke_forms} word forms")
        print(f"'trinken' has {trinken_forms} word forms")
        
        # Delete the incorrect 'trinke' entry and keep 'trinken'
        cursor.execute('DELETE FROM word_forms WHERE lemma_id = ?', (trinke_id,))
        cursor.execute('DELETE FROM translations WHERE lemma_id = ?', (trinke_id,))
        cursor.execute('DELETE FROM examples WHERE lemma_id = ?', (trinke_id,))
        cursor.execute('DELETE FROM word_lemmas WHERE id = ?', (trinke_id,))
        
        print(f"DELETED: 'trinke' (ID {trinke_id}) - keeping correct 'trinken' (ID {trinken_id})")
        
    elif trinke_id and not trinken_id:
        # Just rename trinke to trinken
        cursor.execute('UPDATE word_lemmas SET lemma = "trinken" WHERE id = ?', (trinke_id,))
        print(f"RENAMED: 'trinke' -> 'trinken' (ID {trinke_id})")
        
    else:
        print("No trinke/trinken issue found")
    
    conn.commit()
    conn.close()
    print("Done!")

if __name__ == "__main__":
    fix_trinke_duplicate()