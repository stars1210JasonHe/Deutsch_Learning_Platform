#!/usr/bin/env python3
"""
Monitor the noun import progress by checking database changes in real-time.
"""

import time
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma


def monitor_import_progress():
    """Monitor the import progress in real-time"""
    
    print("=== Monitoring Noun Import Progress ===")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    # Get initial count
    db = SessionLocal()
    try:
        initial_count = db.query(WordLemma).filter(WordLemma.pos == 'noun').count()
        print(f"Starting noun count: {initial_count}")
        print()
        
        last_count = initial_count
        start_time = time.time()
        
        while True:
            time.sleep(5)  # Check every 5 seconds
            
            current_count = db.query(WordLemma).filter(WordLemma.pos == 'noun').count()
            
            if current_count != last_count:
                elapsed = time.time() - start_time
                added = current_count - initial_count
                
                print(f"⏰ {elapsed:.0f}s | Nouns: {current_count} (+{added} new) | Last 5s: +{current_count - last_count}")
                
                # Show the most recently added nouns
                recent_nouns = db.query(WordLemma).filter(
                    WordLemma.pos == 'noun'
                ).order_by(WordLemma.id.desc()).limit(3).all()
                
                if recent_nouns:
                    print("   Recent additions:", ", ".join([f"{noun.lemma} (ID:{noun.id})" for noun in recent_nouns]))
                
                last_count = current_count
            else:
                elapsed = time.time() - start_time
                print(f"⏰ {elapsed:.0f}s | No changes in last 5s (Total: {current_count} nouns)")
                
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")
    finally:
        db.close()


if __name__ == "__main__":
    monitor_import_progress()