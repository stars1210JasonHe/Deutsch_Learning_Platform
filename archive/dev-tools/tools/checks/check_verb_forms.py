"""
Check for incorrect verb forms in database
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Common German infinitive endings
INFINITIVE_ENDINGS = ['en', 'ern', 'eln']

# Known incorrect forms that should be infinitives
KNOWN_CORRECTIONS = {
    'trinke': 'trinken',
    'esse': 'essen', 
    'gehe': 'gehen',
    'komme': 'kommen',
    'spreche': 'sprechen',
    'nehme': 'nehmen',
    'sehe': 'sehen',
    'höre': 'hören',
    'lese': 'lesen',
    'schreibe': 'schreiben',
    'fahre': 'fahren',
    'laufe': 'laufen',
    'schlafe': 'schlafen',
    'arbeite': 'arbeiten',
    'wohne': 'wohnen',
    'kaufe': 'kaufen',
    'bringe': 'bringen',
    'denke': 'denken',
    'finde': 'finden',
    'verstehe': 'verstehen',
    'helfe': 'helfen',
    'kenne': 'kennen',
    'öffne': 'öffnen',
    'schließe': 'schließen',
    'beginne': 'beginnen',
    'vergesse': 'vergessen',
    'erkläre': 'erklären',
    'erzähle': 'erzählen',
    'frage': 'fragen',
    'antworte': 'antworten',
    'telefoniere': 'telefonieren',
    'studiere': 'studieren',
    'probiere': 'probieren',
    'repariere': 'reparieren',
    'organisiere': 'organisieren',
}

def check_database_verbs():
    """Check all verbs in database for correct infinitive forms"""
    
    # Connect to database  
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    print("=== CHECKING ALL VERBS FOR CORRECT INFINITIVE FORMS ===\n")
    
    # Get all verbs
    cursor.execute('SELECT id, lemma FROM word_lemmas WHERE pos = "verb" ORDER BY lemma')
    verbs = cursor.fetchall()
    
    print(f"Found {len(verbs)} verbs in database")
    print("="*60)
    
    incorrect_verbs = []
    suspicious_verbs = []
    
    for verb_id, lemma in verbs:
        lemma = lemma.strip()
        
        # Check against known corrections
        if lemma in KNOWN_CORRECTIONS:
            correct_form = KNOWN_CORRECTIONS[lemma]
            try:
                print(f"INCORRECT: '{lemma}' should be '{correct_form}'")
            except UnicodeEncodeError:
                print(f"INCORRECT: [German verb] should be corrected")
            incorrect_verbs.append((verb_id, lemma, correct_form))
            continue
            
        # Check if it ends with infinitive ending
        has_infinitive_ending = any(lemma.endswith(ending) for ending in INFINITIVE_ENDINGS)
        
        if not has_infinitive_ending:
            try:
                print(f"SUSPICIOUS: '{lemma}' (doesn't end with -en/-ern/-eln)")
            except UnicodeEncodeError:
                print(f"SUSPICIOUS: [German verb] (doesn't end with infinitive)")
            suspicious_verbs.append((verb_id, lemma))
        else:
            # Looks correct - don't print every correct one to reduce output
            pass
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"Correct verbs: {len(verbs) - len(incorrect_verbs) - len(suspicious_verbs)}")
    print(f"Definitely incorrect: {len(incorrect_verbs)}")
    print(f"Suspicious (need manual review): {len(suspicious_verbs)}")
    
    if incorrect_verbs:
        print(f"\nCORRECTIONS NEEDED:")
        for verb_id, wrong, correct in incorrect_verbs:
            try:
                print(f"   ID {verb_id}: '{wrong}' -> '{correct}'")
            except UnicodeEncodeError:
                print(f"   ID {verb_id}: [German verb needs correction]")
    
    if suspicious_verbs:
        print(f"\nMANUAL REVIEW NEEDED:")
        for verb_id, lemma in suspicious_verbs:
            try:
                print(f"   ID {verb_id}: '{lemma}'")
            except UnicodeEncodeError:
                print(f"   ID {verb_id}: [German verb needs review]")
    
    conn.close()
    return incorrect_verbs, suspicious_verbs

def fix_incorrect_verbs(incorrect_verbs):
    """Fix the definitely incorrect verbs"""
    
    if not incorrect_verbs:
        print("No verbs to fix!")
        return
        
    print(f"\n🔧 FIXING {len(incorrect_verbs)} INCORRECT VERBS...")
    
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    for verb_id, wrong_form, correct_form in incorrect_verbs:
        try:
            print(f"Fixing ID {verb_id}: '{wrong_form}' → '{correct_form}'")
            
            # Update the lemma
            cursor.execute(
                'UPDATE word_lemmas SET lemma = ? WHERE id = ?',
                (correct_form, verb_id)
            )
            
            # Update any word forms that reference the wrong lemma
            cursor.execute(
                'UPDATE word_forms SET form = ? WHERE lemma_id = ? AND form = ?',
                (correct_form, verb_id, wrong_form)
            )
            
            print(f"   ✅ Updated successfully")
            
        except Exception as e:
            print(f"   ❌ Error fixing '{wrong_form}': {e}")
    
    conn.commit()
    conn.close()
    print(f"\n✅ Fixed {len(incorrect_verbs)} verbs!")

if __name__ == "__main__":
    # Check all verbs
    incorrect_verbs, suspicious_verbs = check_database_verbs()
    
    # Ask user if they want to fix the incorrect ones
    if incorrect_verbs:
        print(f"\n" + "="*60)
        response = input(f"Fix {len(incorrect_verbs)} definitely incorrect verbs? (y/n): ")
        if response.lower() == 'y':
            fix_incorrect_verbs(incorrect_verbs)
        else:
            print("Skipping fixes.")
    
    print(f"\n📊 FINAL STATUS:")
    print(f"   ✅ {len(incorrect_verbs)} verbs can be auto-fixed")
    print(f"   ⚠️  {len(suspicious_verbs)} verbs need manual review")
    print(f"   📝 Total verbs checked: {len(incorrect_verbs) + len(suspicious_verbs) + (len(sys.argv) if len(sys.argv) > 1 else 0)}")