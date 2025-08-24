#!/usr/bin/env python3
"""
Check if Apfel exists in database and what data it has.
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm, Translation


def check_apfel():
    """Check Apfel in database"""
    
    db = SessionLocal()
    
    try:
        print("Checking for Apfel in database...")
        
        # Look for Apfel
        apfel = db.query(WordLemma).filter(
            WordLemma.lemma == 'Apfel',
            WordLemma.pos == 'noun'
        ).first()
        
        if apfel:
            print(f"Found Apfel (ID: {apfel.id})")
            
            # Check its forms
            forms = db.query(WordForm).filter(WordForm.lemma_id == apfel.id).all()
            print(f"Word forms: {len(forms)}")
            for form in forms:
                print(f"  - {form.feature_key}={form.feature_value}: '{form.form}'")
            
            # Check translations
            translations = db.query(Translation).filter(Translation.lemma_id == apfel.id).all()
            print(f"Translations: {len(translations)}")
            for trans in translations:
                print(f"  - {trans.lang_code}: '{trans.text}'")
        else:
            print("Apfel NOT FOUND")
            
            # Look for similar words
            similar = db.query(WordLemma).filter(
                WordLemma.lemma.like('%pfel%')
            ).all()
            
            if similar:
                print("Similar words found:")
                for word in similar:
                    print(f"  - {word.lemma} (ID: {word.id}, POS: {word.pos})")
            else:
                print("No similar words found")
        
        # Also check for the plural form Äpfel directly
        print("\nChecking for existing Äpfel forms...")
        apfel_forms = db.query(WordForm).filter(WordForm.form == 'Äpfel').all()
        
        if apfel_forms:
            print("Found Äpfel forms:")
            for form in apfel_forms:
                word = db.query(WordLemma).filter(WordLemma.id == form.lemma_id).first()
                print(f"  - Linked to: {word.lemma if word else 'Unknown'} (ID: {form.lemma_id})")
        else:
            print("No Äpfel forms found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    check_apfel()