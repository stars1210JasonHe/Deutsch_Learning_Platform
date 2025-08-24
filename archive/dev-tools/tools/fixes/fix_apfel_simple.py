#!/usr/bin/env python3
"""
Simple fix for Apfel without Unicode console output.
"""

import sys
import os
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm


def fix_apfel_simple():
    """Fix Apfel simply without Unicode display"""
    
    db = SessionLocal()
    
    try:
        print("Fixing Apfel...")
        
        # Find Apfel
        apfel = db.query(WordLemma).filter(
            WordLemma.lemma == 'Apfel',
            WordLemma.pos == 'noun'
        ).first()
        
        if not apfel:
            print("Apfel not found")
            return
        
        print(f"Found Apfel (ID: {apfel.id})")
        
        # Count existing forms
        existing_count = db.query(WordForm).filter(WordForm.lemma_id == apfel.id).count()
        print(f"Existing forms: {existing_count}")
        
        # Check if plural exists
        plural_form = db.query(WordForm).filter(
            WordForm.lemma_id == apfel.id,
            WordForm.feature_key == 'number',
            WordForm.feature_value == 'plural'
        ).first()
        
        if plural_form:
            print("Plural form exists")
        else:
            print("Adding plural form...")
            new_plural = WordForm(
                lemma_id=apfel.id,
                form='Äpfel',
                feature_key='number',
                feature_value='plural'
            )
            db.add(new_plural)
        
        # Check if singular exists
        singular_form = db.query(WordForm).filter(
            WordForm.lemma_id == apfel.id,
            WordForm.feature_key == 'number',
            WordForm.feature_value == 'singular'
        ).first()
        
        if singular_form:
            print("Singular form exists")
        else:
            print("Adding singular form...")
            new_singular = WordForm(
                lemma_id=apfel.id,
                form='Apfel',
                feature_key='number',
                feature_value='singular'
            )
            db.add(new_singular)
        
        # Commit changes
        db.commit()
        print("Apfel fixed successfully!")
        
        # Verify
        final_count = db.query(WordForm).filter(WordForm.lemma_id == apfel.id).count()
        print(f"Final form count: {final_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    fix_apfel_simple()