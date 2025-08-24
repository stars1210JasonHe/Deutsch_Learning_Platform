#!/usr/bin/env python3
"""
Simple diagnostic to see what happened with the check script.
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm


def quick_diagnosis():
    """Quick check to see the issue"""
    
    db = SessionLocal()
    
    try:
        print("=== Quick Diagnosis ===")
        
        # Count total nouns
        total_nouns = db.query(WordLemma).filter(WordLemma.pos == 'noun').count()
        print(f"Total nouns in database: {total_nouns}")
        
        # Count nouns with articles
        nouns_with_articles = db.query(WordLemma).join(WordForm).filter(
            WordLemma.pos == 'noun',
            WordForm.feature_key == 'article'
        ).distinct().count()
        
        # Count nouns with plurals
        nouns_with_plurals = db.query(WordLemma).join(WordForm).filter(
            WordLemma.pos == 'noun',
            WordForm.feature_key == 'number',
            WordForm.feature_value == 'plural'
        ).distinct().count()
        
        print(f"Nouns with articles: {nouns_with_articles}")
        print(f"Nouns with plurals: {nouns_with_plurals}")
        print(f"Nouns missing articles: {total_nouns - nouns_with_articles}")
        print(f"Nouns missing plurals: {total_nouns - nouns_with_plurals}")
        
        # Show a few examples of problematic nouns
        print(f"\nFirst 5 nouns missing articles:")
        missing_articles = db.query(WordLemma).filter(
            WordLemma.pos == 'noun',
            ~WordLemma.id.in_(
                db.query(WordForm.lemma_id).filter(WordForm.feature_key == 'article')
            )
        ).limit(5).all()
        
        for noun in missing_articles:
            print(f"  - {noun.lemma} (ID: {noun.id})")
        
        print(f"\nFirst 5 nouns missing plurals:")
        missing_plurals = db.query(WordLemma).filter(
            WordLemma.pos == 'noun',
            ~WordLemma.id.in_(
                db.query(WordForm.lemma_id).filter(
                    WordForm.feature_key == 'number',
                    WordForm.feature_value == 'plural'
                )
            )
        ).limit(5).all()
        
        for noun in missing_plurals:
            print(f"  - {noun.lemma} (ID: {noun.id})")
            
    except Exception as e:
        print(f"Error in diagnosis: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    quick_diagnosis()