#!/usr/bin/env python3
"""
Fix Apfel/Äpfel Unicode issue by ensuring proper word forms exist.
"""

import sys
import os
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm


def fix_apfel_unicode():
    """Fix the Apfel/Äpfel Unicode issue"""
    
    if sys.platform == "win32":
        os.system("chcp 65001")
    
    db = SessionLocal()
    
    try:
        print("Fixing Apfel/Unicode issue...")
        
        # Find Apfel
        apfel = db.query(WordLemma).filter(
            WordLemma.lemma == 'Apfel',
            WordLemma.pos == 'noun'
        ).first()
        
        if not apfel:
            print("Apfel not found - need to create it")
            return
        
        print(f"Found Apfel (ID: {apfel.id})")
        
        # Check existing forms
        existing_forms = db.query(WordForm).filter(WordForm.lemma_id == apfel.id).all()
        
        form_types = {}
        for form in existing_forms:
            key = f"{form.feature_key}={form.feature_value}"
            form_types[key] = form.form
        
        print("Existing forms:")
        for key, form_value in form_types.items():
            print(f"  {key}: {repr(form_value)}")
        
        # Add missing forms if needed
        needed_forms = [
            ('article', 'article', 'der'),
            ('number', 'singular', 'Apfel'),
            ('number', 'plural', 'Äpfel')
        ]
        
        added_count = 0
        
        for feature_key, feature_value, form_text in needed_forms:
            key = f"{feature_key}={feature_value}"
            
            if key not in form_types:
                print(f"Adding missing form: {key} = {form_text}")
                
                new_form = WordForm(
                    lemma_id=apfel.id,
                    form=form_text,
                    feature_key=feature_key,
                    feature_value=feature_value
                )
                db.add(new_form)
                added_count += 1
            else:
                print(f"Form exists: {key} = {form_types[key]}")
        
        if added_count > 0:
            db.commit()
            print(f"Added {added_count} missing forms")
        else:
            print("No forms needed to be added")
            
        print("Apfel should now work correctly!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    fix_apfel_unicode()