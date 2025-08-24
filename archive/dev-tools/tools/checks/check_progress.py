#!/usr/bin/env python3
"""
Simple script to check current noun count and progress.
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma


def check_current_progress():
    """Check current noun count and recent additions"""
    
    db = SessionLocal()
    
    try:
        # Total noun count
        total_nouns = db.query(WordLemma).filter(WordLemma.pos == 'noun').count()
        print(f"Current total nouns: {total_nouns}")
        
        # Show the 5 most recently added nouns
        recent_nouns = db.query(WordLemma).filter(
            WordLemma.pos == 'noun'
        ).order_by(WordLemma.id.desc()).limit(5).all()
        
        print("\nMost recently added nouns:")
        for noun in recent_nouns:
            print(f"  {noun.id}: {noun.lemma} (created: {noun.created_at})")
            
        # Count today's additions (rough estimate)
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        today_count = db.query(WordLemma).filter(
            WordLemma.pos == 'noun',
            WordLemma.created_at >= today
        ).count()
        
        print(f"\nNouns added today: {today_count}")
        
    finally:
        db.close()


if __name__ == "__main__":
    check_current_progress()