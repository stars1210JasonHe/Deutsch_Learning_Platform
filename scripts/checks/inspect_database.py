#!/usr/bin/env python3
"""
Database inspection script to check data format and completeness
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.models.word import WordLemma, Translation, Example, WordForm
from app.models.user import User
from app.models.search import SearchHistory, SearchCache
from sqlalchemy import text

def inspect_database():
    """Inspect database structure and data completeness"""
    print("🔍 Database Inspection Report")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Check table counts
        print("\n📊 Table Statistics:")
        tables = [
            ("Users", User),
            ("Word Lemmas", WordLemma), 
            ("Translations", Translation),
            ("Examples", Example),
            ("Word Forms", WordForm),
            ("Search History", SearchHistory),
            ("Search Cache", SearchCache),
        ]
        
        for table_name, model_class in tables:
            try:
                count = db.query(model_class).count()
                print(f"   {table_name}: {count} records")
            except Exception as e:
                print(f"   {table_name}: ERROR - {e}")
        
        # Check word lemma data quality
        print(f"\n📝 Word Lemma Data Quality:")
        words = db.query(WordLemma).all()
        
        missing_pos = 0
        missing_translations = 0
        missing_examples = 0
        incomplete_verbs = 0
        
        for word in words:
            # Check POS
            if not word.pos or word.pos == "unknown":
                missing_pos += 1
            
            # Check translations
            if not word.translations:
                missing_translations += 1
            
            # Check examples
            if not word.examples:
                missing_examples += 1
            
            # Check verb forms
            if word.pos == "verb" and not word.forms:
                incomplete_verbs += 1
        
        total_words = len(words)
        print(f"   Total words: {total_words}")
        print(f"   Missing/unknown POS: {missing_pos} ({missing_pos/total_words*100:.1f}%)")
        print(f"   Missing translations: {missing_translations} ({missing_translations/total_words*100:.1f}%)")
        print(f"   Missing examples: {missing_examples} ({missing_examples/total_words*100:.1f}%)")
        print(f"   Incomplete verbs: {incomplete_verbs}")
        
        # Sample problematic words
        print(f"\n🔧 Sample Issues:")
        problematic_words = db.query(WordLemma).filter(
            (WordLemma.pos == "unknown") | (WordLemma.pos == None)
        ).limit(10).all()
        
        for word in problematic_words:
            print(f"   '{word.lemma}' - POS: {word.pos}, Translations: {len(word.translations)}, Examples: {len(word.examples)}")
        
        # Check translation language distribution
        print(f"\n🌍 Translation Languages:")
        en_translations = db.query(Translation).filter(Translation.lang_code == "en").count()
        zh_translations = db.query(Translation).filter(Translation.lang_code == "zh").count()
        other_translations = db.query(Translation).filter(
            ~Translation.lang_code.in_(["en", "zh"])
        ).count()
        
        print(f"   English: {en_translations}")
        print(f"   Chinese: {zh_translations}")
        print(f"   Other: {other_translations}")
        
        # Check example completeness
        print(f"\n📝 Example Quality:")
        empty_examples = db.query(Example).filter(
            (Example.de_text == "") | (Example.de_text == None)
        ).count()
        total_examples = db.query(Example).count()
        
        if total_examples > 0:
            print(f"   Total examples: {total_examples}")
            print(f"   Empty German text: {empty_examples} ({empty_examples/total_examples*100:.1f}%)")
        
        # Check search history patterns
        print(f"\n🔍 Search History Analysis:")
        recent_searches = db.query(SearchHistory).order_by(SearchHistory.timestamp.desc()).limit(10).all()
        print("   Recent searches:")
        for search in recent_searches:
            print(f"     '{search.query_text}' - {search.query_type}")
        
        # Database schema info
        print(f"\n🗄️ Schema Information:")
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = result.fetchall()
        print(f"   Tables: {[table[0] for table in tables]}")
        
        return {
            "total_words": total_words,
            "missing_pos": missing_pos,
            "missing_translations": missing_translations,
            "missing_examples": missing_examples,
            "incomplete_verbs": incomplete_verbs
        }
        
    finally:
        db.close()

def generate_fix_recommendations(stats):
    """Generate recommendations for fixing database issues"""
    print(f"\n💡 Recommendations:")
    
    if stats["missing_pos"] > 0:
        print(f"   1. Fix {stats['missing_pos']} words with missing/unknown POS using OpenAI")
    
    if stats["missing_translations"] > 0:
        print(f"   2. Add translations for {stats['missing_translations']} words")
    
    if stats["missing_examples"] > 0:
        print(f"   3. Generate examples for {stats['missing_examples']} words")
    
    if stats["incomplete_verbs"] > 0:
        print(f"   4. Complete verb conjugations for {stats['incomplete_verbs']} verbs")
    
    print(f"   5. Consider running Excel import to add more vocabulary")

if __name__ == "__main__":
    try:
        stats = inspect_database()
        generate_fix_recommendations(stats)
    except Exception as e:
        print(f"❌ Inspection failed: {e}")
        import traceback
        traceback.print_exc()