#!/usr/bin/env python3
"""
Check ALL nouns in the database for missing articles and plurals.
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm


def check_all_nouns():
    """Check ALL nouns for missing articles and plurals"""
    
    db = SessionLocal()
    
    try:
        print("=== Checking ALL Nouns in Database ===")
        print()
        
        # Get ALL nouns
        all_nouns = db.query(WordLemma).filter(WordLemma.pos == 'noun').all()
        
        print(f"Checking {len(all_nouns)} total nouns...")
        print()
        
        missing_articles = []
        missing_plurals = []
        complete_count = 0
        
        for noun in all_nouns:
            # Check for article
            article_form = db.query(WordForm).filter(
                WordForm.lemma_id == noun.id,
                WordForm.feature_key == 'article'
            ).first()
            
            # Check for plural
            plural_form = db.query(WordForm).filter(
                WordForm.lemma_id == noun.id,
                WordForm.feature_key == 'number',
                WordForm.feature_value == 'plural'
            ).first()
            
            has_article = article_form is not None
            has_plural = plural_form is not None
            
            if has_article and has_plural:
                complete_count += 1
            else:
                # Print incomplete nouns
                status_parts = []
                if not has_article:
                    status_parts.append("NO ARTICLE")
                    missing_articles.append(noun)
                if not has_plural:
                    status_parts.append("NO PLURAL")
                    missing_plurals.append(noun)
                
                status = " + ".join(status_parts)
                try:
                    print(f"  {noun.lemma} (ID:{noun.id}) - {status}")
                except UnicodeEncodeError:
                    print(f"  [Unicode Error] (ID:{noun.id}) - {status}")
        
        print()
        print(f"=== SUMMARY ===")
        print(f"Total nouns: {len(all_nouns)}")
        print(f"Complete: {complete_count}")
        print(f"Missing articles: {len(missing_articles)}")
        print(f"Missing plurals: {len(missing_plurals)}")
        print(f"Total incomplete: {len(missing_articles) + len(missing_plurals) - len(set(missing_articles) & set(missing_plurals))}")
        
        # Show first 20 nouns missing articles
        if missing_articles:
            print(f"\nFirst 20 nouns missing articles:")
            for noun in missing_articles[:20]:
                try:
                    print(f"  - {noun.lemma} (ID: {noun.id})")
                except UnicodeEncodeError:
                    print(f"  - [Unicode Error] (ID: {noun.id})")
            if len(missing_articles) > 20:
                print(f"  ... and {len(missing_articles) - 20} more")
        
        # Show first 20 nouns missing plurals  
        if missing_plurals:
            print(f"\nFirst 20 nouns missing plurals:")
            for noun in missing_plurals[:20]:
                try:
                    print(f"  - {noun.lemma} (ID: {noun.id})")
                except UnicodeEncodeError:
                    print(f"  - [Unicode Error] (ID: {noun.id})")
            if len(missing_plurals) > 20:
                print(f"  ... and {len(missing_plurals) - 20} more")
        
        return {
            'total': len(all_nouns),
            'complete': complete_count,
            'missing_articles': missing_articles,
            'missing_plurals': missing_plurals
        }
        
    finally:
        db.close()


if __name__ == "__main__":
    results = check_all_nouns()
    
    if results['missing_articles'] or results['missing_plurals']:
        print(f"\n" + "="*50)
        print(f"FOUND ISSUES! To fix them, you can:")
        print(f"1. Run the fix script: uv run python fix_missing_noun_data.py")
        print(f"2. Or manually add missing articles/plurals")
        print(f"="*50)
    else:
        print(f"\nALL NOUNS HAVE COMPLETE DATA! 🎉")