#!/usr/bin/env python3
"""
Check the specific forms for missing tenses
"""
import sqlite3

def check_missing_tenses():
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    # Get all unique tense patterns
    cursor.execute("""
        SELECT DISTINCT feature_value, COUNT(*) as count
        FROM word_forms 
        WHERE feature_key = 'tense'
        GROUP BY feature_value
        ORDER BY feature_value
    """)
    
    all_tenses = cursor.fetchall()
    print("All tense feature_values in database:")
    for tense, count in all_tenses:
        try:
            print(f"  {tense}: {count} forms")
        except UnicodeEncodeError:
            print(f"  [tense]: {count} forms")
    
    # Check specific problematic patterns
    print(f"\n=== Analyzing Tense Patterns ===")
    
    # Look for futur variants
    futur_patterns = [t for t, c in all_tenses if 'futur' in t.lower()]
    print(f"Futur patterns: {futur_patterns}")
    
    # Look for konjunktiv variants  
    konjunktiv_patterns = [t for t, c in all_tenses if 'konjunktiv' in t.lower()]
    print(f"Konjunktiv patterns: {konjunktiv_patterns}")
    
    conn.close()

if __name__ == "__main__":
    check_missing_tenses()