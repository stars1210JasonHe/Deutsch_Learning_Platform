#!/usr/bin/env python3
"""
Fix specific nouns with ASCII-safe data to test the solution
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm


def fix_ascii_nouns():
    """Add article and plural data for specific test nouns (ASCII only)"""
    
    db = SessionLocal()
    
    # Define specific nouns with ASCII-safe data
    noun_data = [
        ('Raum', 'der', 'Raeume'),  # Using ae instead of ä
        ('Bank', 'die', 'Baenke'),  # Using ae instead of ä
        ('Fenster', 'das', 'Fenster'),
        ('Auto', 'das', 'Autos'),
        ('Tag', 'der', 'Tage'),
        ('Jahr', 'das', 'Jahre'),
        ('Leben', 'das', 'Leben'),
        ('Arbeit', 'die', 'Arbeiten'),
        ('Welt', 'die', 'Welten'),
    ]
    
    try:
        for lemma_text, article, plural in noun_data:
            # Find the word
            word = db.query(WordLemma).filter(WordLemma.lemma == lemma_text).first()
            if not word:
                print(f"Word '{lemma_text}' not found in database")
                continue
            
            # Check if article already exists
            existing_article = db.query(WordForm).filter(
                WordForm.lemma_id == word.id,
                WordForm.feature_key == 'article'
            ).first()
            
            if not existing_article:
                # Add article
                article_form = WordForm(
                    lemma_id=word.id,
                    form=article,
                    feature_key='article',
                    feature_value='definite'
                )
                db.add(article_form)
                print(f"Added article '{article}' for {lemma_text}")
            
            # Check if plural already exists
            existing_plural = db.query(WordForm).filter(
                WordForm.lemma_id == word.id,
                WordForm.feature_key == 'plural'
            ).first()
            
            if not existing_plural:
                # Add plural
                plural_form = WordForm(
                    lemma_id=word.id,
                    form=plural,
                    feature_key='plural',
                    feature_value='plural'
                )
                db.add(plural_form)
                print(f"Added plural '{plural}' for {lemma_text}")
        
        # Commit all changes
        db.commit()
        print("\nAll changes committed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    fix_ascii_nouns()