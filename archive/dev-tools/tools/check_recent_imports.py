#!/usr/bin/env python3
"""
Simple database checker for recent Collins imports
"""
import sqlite3
import sys

def check_recent_imports():
    """Check recently imported Collins dictionary entries"""
    
    db_path = 'data/app.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check total word count
        cursor.execute("SELECT COUNT(*) FROM word_lemmas")
        total_words = cursor.fetchone()[0]
        print(f"Total words in database: {total_words}")
        
        # Check Collins imports
        cursor.execute("""
            SELECT COUNT(*) FROM word_lemmas 
            WHERE notes LIKE '%Collins Dictionary%'
        """)
        collins_count = cursor.fetchone()[0]
        print(f"Collins dictionary imports: {collins_count}")
        
        # Show recent Collins entries
        cursor.execute("""
            SELECT wl.lemma, wl.pos, wl.ipa, t.text
            FROM word_lemmas wl
            LEFT JOIN translations t ON wl.id = t.lemma_id AND t.lang_code = 'en'
            WHERE wl.notes LIKE '%Collins Dictionary%'
            ORDER BY wl.created_at DESC
            LIMIT 15
        """)
        
        print("\nRecent Collins imports:")
        for row in cursor.fetchall():
            lemma, pos, ipa, translation = row
            try:
                ipa_str = f" [{ipa}]" if ipa else ""
                print(f"  {lemma}{ipa_str} ({pos}): {translation}")
            except UnicodeEncodeError:
                # Handle encoding issues by skipping problem characters
                safe_lemma = lemma.encode('ascii', errors='replace').decode('ascii')
                safe_translation = (translation or '').encode('ascii', errors='replace').decode('ascii')
                print(f"  {safe_lemma} ({pos}): {safe_translation}")
        
        # Check words with articles
        cursor.execute("""
            SELECT wl.lemma, wf.form
            FROM word_lemmas wl
            JOIN word_forms wf ON wl.id = wf.lemma_id
            WHERE wf.feature_key = 'article'
            AND wl.notes LIKE '%Collins Dictionary%'
        """)
        
        print(f"\nWords with gender articles:")
        for row in cursor.fetchall():
            lemma, article = row
            print(f"  {article} {lemma}")
        
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_recent_imports()