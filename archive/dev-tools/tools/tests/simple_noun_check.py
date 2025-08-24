#!/usr/bin/env python3
"""
Simple check for noun data completeness without Unicode issues.
"""

import sys
from pathlib import Path
from datetime import datetime

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm


def check_noun_data():
    """Check noun data completeness"""
    
    db = SessionLocal()
    
    try:
        print("=== Checking Today's Imported Nouns ===")
        print()
        
        # Get today's nouns
        today = datetime.now().date()
        today_nouns = db.query(WordLemma).filter(
            WordLemma.pos == 'noun',
            WordLemma.created_at >= today
        ).all()
        
        print(f"Found {len(today_nouns)} nouns added today:")
        print()
        
        complete_count = 0
        missing_articles = []
        missing_plurals = []
        
        for noun in today_nouns:
            # Check forms
            article_form = db.query(WordForm).filter(
                WordForm.lemma_id == noun.id,
                WordForm.feature_key == 'article'
            ).first()
            
            plural_form = db.query(WordForm).filter(
                WordForm.lemma_id == noun.id,
                WordForm.feature_key == 'number',
                WordForm.feature_value == 'plural'
            ).first()
            
            has_article = article_form is not None
            has_plural = plural_form is not None
            
            # Report status
            status = "COMPLETE" if has_article and has_plural else "INCOMPLETE"
            article_text = f"article: {article_form.form}" if article_form else "article: MISSING"
            plural_text = f"plural: {plural_form.form}" if plural_form else "plural: MISSING"
            
            print(f"  {noun.lemma} (ID:{noun.id}) - {status}")
            print(f"    {article_text}, {plural_text}")
            
            if has_article and has_plural:
                complete_count += 1
            if not has_article:
                missing_articles.append(noun)
            if not has_plural:
                missing_plurals.append(noun)
        
        print()
        print(f"Summary:")
        print(f"  Complete: {complete_count}/{len(today_nouns)}")
        print(f"  Missing articles: {len(missing_articles)}")
        print(f"  Missing plurals: {len(missing_plurals)}")
        
        if missing_articles:
            print(f"\nNouns missing articles:")
            for noun in missing_articles:
                print(f"  - {noun.lemma} (ID: {noun.id})")
        
        if missing_plurals:
            print(f"\nNouns missing plurals:")
            for noun in missing_plurals:
                print(f"  - {noun.lemma} (ID: {noun.id})")
        
        if len(missing_articles) + len(missing_plurals) > 0:
            print(f"\nTo fix these issues, run:")
            print(f"  uv run python check_and_fix_noun_data.py")
        else:
            print(f"\nAll nouns have complete data!")
        
    finally:
        db.close()


if __name__ == "__main__":
    check_noun_data()