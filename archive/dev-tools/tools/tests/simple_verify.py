#!/usr/bin/env python3

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm, Translation, Example


def verify_nouns():
    test_nouns = ['Kfz', 'EG', 'Lkw', 'WG']
    
    db = SessionLocal()
    
    try:
        print("Checking imported nouns...")
        
        for noun_lemma in test_nouns:
            word = db.query(WordLemma).filter(
                WordLemma.lemma == noun_lemma,
                WordLemma.pos == 'noun'
            ).first()
            
            if word:
                print(f"{noun_lemma}: FOUND (ID: {word.id})")
                
                # Count related data
                forms_count = db.query(WordForm).filter(WordForm.lemma_id == word.id).count()
                trans_count = db.query(Translation).filter(Translation.lemma_id == word.id).count()
                examples_count = db.query(Example).filter(Example.lemma_id == word.id).count()
                
                print(f"  Forms: {forms_count}, Translations: {trans_count}, Examples: {examples_count}")
            else:
                print(f"{noun_lemma}: NOT FOUND")
    
    finally:
        db.close()


if __name__ == "__main__":
    verify_nouns()