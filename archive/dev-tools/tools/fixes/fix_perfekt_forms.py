#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix verbs missing complete Perfekt conjugation forms
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


async def get_perfekt_from_openai(openai_service: OpenAIService, lemma: str, existing_forms: dict) -> dict:
    """Get complete Perfekt forms for a verb using OpenAI"""
    
    # Check if we already have some Perfekt data to help OpenAI
    existing_perfekt = {k: v for k, v in existing_forms.items() if k.startswith('perfekt_')}
    
    prompt = f"""
    Complete the German Perfekt (present perfect) conjugation for the verb "{lemma}".
    
    Existing data: {existing_perfekt if existing_perfekt else 'None'}
    
    Return a JSON response with ALL Perfekt forms:
    {{
        "verb": "{lemma}",
        "perfekt_ich": "ich form with aux + partizip (e.g., habe genommen)",
        "perfekt_du": "du form with aux + partizip (e.g., hast genommen)", 
        "perfekt_er_sie_es": "er/sie/es form with aux + partizip (e.g., hat genommen)",
        "perfekt_wir": "wir form with aux + partizip (e.g., haben genommen)",
        "perfekt_ihr": "ihr form with aux + partizip (e.g., habt genommen)",
        "perfekt_sie_Sie": "sie/Sie form with aux + partizip (e.g., haben genommen)"
    }}
    
    Examples:
    - nehmen: uses "haben" auxiliary → "ich habe genommen", "du hast genommen", etc.
    - gehen: uses "sein" auxiliary → "ich bin gegangen", "du bist gegangen", etc.
    - arbeiten: "ich habe gearbeitet", "du hast gearbeitet", etc.
    """
    
    try:
        response = await openai_service.client.chat.completions.create(
            model=openai_service.model,
            messages=[
                {"role": "system", "content": "You are a German grammar expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=400
        )
        
        analysis = json.loads(response.choices[0].message.content)
        return analysis
        
    except Exception as e:
        print(f"Error getting Perfekt for {lemma}: {e}")
        return {}


async def fix_incomplete_perfekt():
    """Find and fix verbs with incomplete Perfekt forms"""
    
    print("Finding verbs with incomplete Perfekt forms...")
    
    openai_service = OpenAIService()
    db = SessionLocal()
    
    try:
        # Find verbs that have some Perfekt but not all 6 forms
        all_verbs = db.query(WordLemma).filter(
            WordLemma.pos.in_(['verb', 'VERB'])
        ).limit(30).all()
        
        verbs_to_fix = []
        
        for verb in all_verbs:
            # Count Perfekt forms
            perfekt_forms = db.query(WordForm).filter(
                WordForm.lemma_id == verb.id,
                WordForm.feature_key == 'tense',
                WordForm.feature_value.like('perfekt_%')
            ).all()
            
            if len(perfekt_forms) < 6:  # Should have 6 Perfekt forms
                verbs_to_fix.append((verb, perfekt_forms))
                print(f"Found {verb.lemma}: has {len(perfekt_forms)} Perfekt forms, needs 6")
        
        print(f"Found {len(verbs_to_fix)} verbs needing Perfekt fixes")
        
        fixed_count = 0
        
        for verb, existing_forms in verbs_to_fix[:10]:  # Process first 10
            print(f"Processing: {verb.lemma}")
            
            # Get existing tense data
            all_forms = db.query(WordForm).filter(
                WordForm.lemma_id == verb.id,
                WordForm.feature_key == 'tense'
            ).all()
            existing_dict = {f.feature_value: f.form for f in all_forms}
            
            # Get complete Perfekt forms from OpenAI
            perfekt_data = await get_perfekt_from_openai(openai_service, verb.lemma, existing_dict)
            
            if perfekt_data and 'perfekt_ich' in perfekt_data:
                # Add missing Perfekt forms
                perfekt_forms_to_add = [
                    'perfekt_ich', 'perfekt_du', 'perfekt_er_sie_es',
                    'perfekt_wir', 'perfekt_ihr', 'perfekt_sie_Sie'
                ]
                
                added_count = 0
                for form_key in perfekt_forms_to_add:
                    if form_key not in existing_dict and perfekt_data.get(form_key):
                        form = WordForm(
                            lemma_id=verb.id,
                            form=perfekt_data[form_key],
                            feature_key='tense',
                            feature_value=form_key
                        )
                        db.add(form)
                        added_count += 1
                        print(f"  -> Added {form_key}: {perfekt_data[form_key]}")
                
                if added_count > 0:
                    fixed_count += 1
                    
                    # Commit every 3 verbs
                    if fixed_count % 3 == 0:
                        db.commit()
                        print(f"Committed progress: {fixed_count} verbs fixed")
            
            else:
                print(f"  -> Failed to get Perfekt for {verb.lemma}")
        
        # Final commit
        db.commit()
        print(f"\nCompleted! Fixed {fixed_count} verbs with complete Perfekt forms")
        
        # Test nehmen specifically
        print("\nTesting nehmen Perfekt forms:")
        nehmen = db.query(WordLemma).filter(WordLemma.lemma == 'nehmen').first()
        if nehmen:
            perfekt_forms = db.query(WordForm).filter(
                WordForm.lemma_id == nehmen.id,
                WordForm.feature_key == 'tense',
                WordForm.feature_value.like('perfekt_%')
            ).all()
            
            print(f"nehmen now has {len(perfekt_forms)} Perfekt forms:")
            for form in perfekt_forms:
                print(f"  {form.feature_value}: {form.form}")
        
    except Exception as e:
        print(f"Error during fix: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(fix_incomplete_perfekt())