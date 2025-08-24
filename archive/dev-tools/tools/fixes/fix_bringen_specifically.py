#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix bringen specifically - add complete conjugation forms
"""
import asyncio
import sys
import os
import io
import json

# Set UTF-8 encoding for all output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm
from app.services.openai_service import OpenAIService


async def get_complete_conjugation(openai_service: OpenAIService, lemma: str) -> dict:
    """Get complete conjugation for a German verb using OpenAI"""
    
    prompt = f"""
    Generate complete German conjugation for the verb "{lemma}".
    
    Return JSON with ALL essential tenses:
    {{
        "verb": "{lemma}",
        "praesens_ich": "ich form",
        "praesens_du": "du form", 
        "praesens_er_sie_es": "er/sie/es form",
        "praesens_wir": "wir form",
        "praesens_ihr": "ihr form",
        "praesens_sie_Sie": "sie/Sie form",
        "praeteritum_ich": "ich form",
        "praeteritum_du": "du form",
        "praeteritum_er_sie_es": "er/sie/es form", 
        "praeteritum_wir": "wir form",
        "praeteritum_ihr": "ihr form",
        "praeteritum_sie_Sie": "sie/Sie form",
        "perfekt_ich": "ich form with aux",
        "perfekt_du": "du form with aux",
        "perfekt_er_sie_es": "er/sie/es form with aux",
        "perfekt_wir": "wir form with aux",
        "perfekt_ihr": "ihr form with aux", 
        "perfekt_sie_Sie": "sie/Sie form with aux"
    }}
    
    Examples:
    - bringen: Präsens "ich bringe", Präteritum "ich brachte", Perfekt "ich habe gebracht"
    - gehen: Präsens "ich gehe", Präteritum "ich ging", Perfekt "ich bin gegangen"
    """
    
    try:
        response = await openai_service.client.chat.completions.create(
            model=openai_service.model,
            messages=[
                {"role": "system", "content": "You are a German grammar expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=600
        )
        
        analysis = json.loads(response.choices[0].message.content)
        return analysis
        
    except Exception as e:
        print(f"Error getting conjugation for {lemma}: {e}")
        return {}


async def fix_bringen():
    """Fix bringen specifically"""
    
    print("Fixing 'bringen' verb conjugations...")
    
    openai_service = OpenAIService()
    db = SessionLocal()
    
    try:
        # Find bringen specifically
        bringen = db.query(WordLemma).filter(WordLemma.lemma == 'bringen').first()
        
        if not bringen:
            print("Error: 'bringen' not found in database!")
            return
        
        print(f"Found 'bringen' with ID {bringen.id}")
        
        # Check current forms
        current_forms = db.query(WordForm).filter(
            WordForm.lemma_id == bringen.id,
            WordForm.feature_key == 'tense'
        ).all()
        
        print(f"Current forms for 'bringen': {len(current_forms)}")
        for form in current_forms:
            print(f"  {form.feature_value}: {form.form}")
        
        # Get complete conjugation from OpenAI
        print("\nGetting complete conjugation from OpenAI...")
        conjugation_data = await get_complete_conjugation(openai_service, 'bringen')
        
        if conjugation_data and 'praesens_ich' in conjugation_data:
            print("OpenAI response:")
            for key, value in conjugation_data.items():
                if key != 'verb':
                    print(f"  {key}: {value}")
            
            # Get existing forms as dict
            existing_dict = {f.feature_value: f.form for f in current_forms}
            
            # Add all missing forms
            all_forms = [
                'praesens_ich', 'praesens_du', 'praesens_er_sie_es', 'praesens_wir', 'praesens_ihr', 'praesens_sie_Sie',
                'praeteritum_ich', 'praeteritum_du', 'praeteritum_er_sie_es', 'praeteritum_wir', 'praeteritum_ihr', 'praeteritum_sie_Sie',
                'perfekt_ich', 'perfekt_du', 'perfekt_er_sie_es', 'perfekt_wir', 'perfekt_ihr', 'perfekt_sie_Sie'
            ]
            
            added_count = 0
            for form_key in all_forms:
                if form_key not in existing_dict and conjugation_data.get(form_key):
                    form = WordForm(
                        lemma_id=bringen.id,
                        form=conjugation_data[form_key],
                        feature_key='tense',
                        feature_value=form_key
                    )
                    db.add(form)
                    added_count += 1
                    print(f"Added {form_key}: {conjugation_data[form_key]}")
            
            print(f"\nAdded {added_count} new conjugation forms")
            db.commit()
            
            # Test the result
            print("\nTesting updated 'bringen'...")
            updated_forms = db.query(WordForm).filter(
                WordForm.lemma_id == bringen.id,
                WordForm.feature_key == 'tense'
            ).all()
            
            # Count by tense type
            praesens_count = sum(1 for f in updated_forms if f.feature_value.startswith('praesens_'))
            praeteritum_count = sum(1 for f in updated_forms if f.feature_value.startswith('praeteritum_'))
            perfekt_count = sum(1 for f in updated_forms if f.feature_value.startswith('perfekt_'))
            imperativ_count = sum(1 for f in updated_forms if f.feature_value.startswith('imperativ_'))
            
            print(f"bringen now has:")
            print(f"  Präsens: {praesens_count} forms")
            print(f"  Präteritum: {praeteritum_count} forms") 
            print(f"  Perfekt: {perfekt_count} forms")
            print(f"  Imperativ: {imperativ_count} forms")
            print(f"  Total: {len(updated_forms)} forms")
            
        else:
            print("Failed to get conjugation data from OpenAI")
        
    except Exception as e:
        print(f"Error during fix: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(fix_bringen())