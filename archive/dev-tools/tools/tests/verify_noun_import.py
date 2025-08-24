#!/usr/bin/env python3
"""
Verify that the imported nouns are correctly stored in the database.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm, Translation, Example


def verify_imported_nouns():
    """Check that our imported nouns are in the database with complete data"""
    
    test_nouns = ['Kfz', 'EG', 'Lkw', 'WG']
    
    db = SessionLocal()
    
    try:
        print("=== Verifying Imported Nouns ===\n")
        
        for noun_lemma in test_nouns:
            print(f"Checking: {noun_lemma}")
            
            # Find the word lemma
            word = db.query(WordLemma).filter(
                WordLemma.lemma == noun_lemma,
                WordLemma.pos == 'noun'
            ).first()
            
            if not word:
                print(f"  ❌ Not found in database")
                continue
                
            print(f"  ✅ Found (ID: {word.id})")
            
            # Check word forms
            forms = db.query(WordForm).filter(WordForm.lemma_id == word.id).all()
            print(f"  📝 Word forms: {len(forms)}")
            for form in forms:
                print(f"    - {form.feature_key}={form.feature_value}: '{form.form}'")
            
            # Check translations  
            translations = db.query(Translation).filter(Translation.lemma_id == word.id).all()
            print(f"  🌍 Translations: {len(translations)}")
            for trans in translations:
                print(f"    - {trans.lang_code}: '{trans.text}'")
            
            # Check examples
            examples = db.query(Example).filter(Example.lemma_id == word.id).all()
            print(f"  📚 Examples: {len(examples)}")
            for example in examples:
                print(f"    - DE: '{example.de_text}'")
                print(f"    - EN: '{example.en_text}'")
                print(f"    - ZH: '{example.zh_text}'")
            
            print()
    
    finally:
        db.close()


if __name__ == "__main__":
    verify_imported_nouns()