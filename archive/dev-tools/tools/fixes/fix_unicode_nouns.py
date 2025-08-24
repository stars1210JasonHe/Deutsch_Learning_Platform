#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix German nouns with correct Unicode characters (ä, ö, ü, ß)
"""
import sys
import os
import io

# Set UTF-8 encoding for all output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm


def fix_unicode_nouns():
    """Fix German nouns with correct Unicode characters"""
    
    db = SessionLocal()
    
    # Define nouns with CORRECT German spelling
    correct_noun_data = [
        ('Raum', 'der', 'Räume'),  # Correct: Räume not Raeume
        ('Bank', 'die', 'Bänke'),  # Correct: Bänke not Baenke
        ('Tür', 'die', 'Türen'),
        ('Buch', 'das', 'Bücher'),
        ('Stadt', 'die', 'Städte'),
        ('Land', 'das', 'Länder'),
        ('Möbel', 'das', 'Möbel'),
        ('Käse', 'der', 'Käse'),
        ('Größe', 'die', 'Größen'),
        ('Straße', 'die', 'Straßen'),
        ('Haus', 'das', 'Häuser'),
        ('Maus', 'die', 'Mäuse'),
        ('Auto', 'das', 'Autos'),
        ('Fenster', 'das', 'Fenster'),
        ('Tag', 'der', 'Tage'),
        ('Jahr', 'das', 'Jahre'),
        ('Leben', 'das', 'Leben'),
        ('Arbeit', 'die', 'Arbeiten'),
        ('Welt', 'die', 'Welten'),
        ('Mensch', 'der', 'Menschen'),
        ('Zeit', 'die', 'Zeiten'),
        ('Wasser', 'das', 'Wasser'),
        ('Tisch', 'der', 'Tische'),
    ]
    
    try:
        fixed_count = 0
        for lemma_text, correct_article, correct_plural in correct_noun_data:
            print(f"Processing: {lemma_text}")
            
            # Find the word
            word = db.query(WordLemma).filter(WordLemma.lemma == lemma_text).first()
            if not word:
                print(f"  Word '{lemma_text}' not found in database")
                continue
            
            # Check current article
            existing_article = db.query(WordForm).filter(
                WordForm.lemma_id == word.id,
                WordForm.feature_key == 'article'
            ).first()
            
            if existing_article:
                if existing_article.form != correct_article:
                    print(f"  Fixing article: {existing_article.form} → {correct_article}")
                    existing_article.form = correct_article
                    fixed_count += 1
                else:
                    print(f"  Article already correct: {correct_article}")
            else:
                # Add new article
                article_form = WordForm(
                    lemma_id=word.id,
                    form=correct_article,
                    feature_key='article',
                    feature_value='definite'
                )
                db.add(article_form)
                print(f"  Added article: {correct_article}")
                fixed_count += 1
            
            # Check current plural
            existing_plural = db.query(WordForm).filter(
                WordForm.lemma_id == word.id,
                WordForm.feature_key == 'plural'
            ).first()
            
            if existing_plural:
                if existing_plural.form != correct_plural:
                    print(f"  Fixing plural: {existing_plural.form} → {correct_plural}")
                    existing_plural.form = correct_plural
                    fixed_count += 1
                else:
                    print(f"  Plural already correct: {correct_plural}")
            else:
                # Add new plural
                plural_form = WordForm(
                    lemma_id=word.id,
                    form=correct_plural,
                    feature_key='plural',
                    feature_value='plural'
                )
                db.add(plural_form)
                print(f"  Added plural: {correct_plural}")
                fixed_count += 1
            
            print()
        
        # Commit all changes
        db.commit()
        print(f"Successfully fixed {fixed_count} entries with correct German spelling!")
        
        # Verify specific corrections
        print("\nVerifying key corrections:")
        
        for lemma_text, expected_article, expected_plural in [
            ('Raum', 'der', 'Räume'),
            ('Bank', 'die', 'Bänke'),
            ('Haus', 'das', 'Häuser')
        ]:
            word = db.query(WordLemma).filter(WordLemma.lemma == lemma_text).first()
            if word:
                article_form = db.query(WordForm).filter(
                    WordForm.lemma_id == word.id,
                    WordForm.feature_key == 'article'
                ).first()
                plural_form = db.query(WordForm).filter(
                    WordForm.lemma_id == word.id,
                    WordForm.feature_key == 'plural'
                ).first()
                
                article = article_form.form if article_form else "None"
                plural = plural_form.form if plural_form else "None"
                
                print(f"{lemma_text}: {article} {lemma_text}, Plural: {plural}")
                
                if article == expected_article and plural == expected_plural:
                    print(f"  ✓ Correct!")
                else:
                    print(f"  ✗ Expected: {expected_article} {lemma_text}, Plural: {expected_plural}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    fix_unicode_nouns()