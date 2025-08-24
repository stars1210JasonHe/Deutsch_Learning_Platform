#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive fix for ALL verbs - check every verb in database and use OpenAI to fill missing conjugations
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
    - kommen: Präsens "ich komme", Präteritum "ich kam", Perfekt "ich bin gekommen"
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


async def fix_all_verbs_comprehensive():
    """Fix ALL verbs in the database - no limits, check everything"""
    
    print("Starting comprehensive verb conjugation fix for ALL verbs in database...")
    
    openai_service = OpenAIService()
    db = SessionLocal()
    
    try:
        # Get ALL verbs in database - NO LIMIT
        print("Fetching ALL verbs from database...")
        all_verbs = db.query(WordLemma).filter(
            WordLemma.pos.in_(['verb', 'VERB'])
        ).all()  # NO LIMIT - get everything
        
        print(f"Found {len(all_verbs)} total verbs in database")
        
        verbs_needing_fix = []
        
        print("\nChecking each verb for missing conjugations...")
        for i, verb in enumerate(all_verbs, 1):
            if i % 20 == 0:
                print(f"  Processed {i}/{len(all_verbs)} verbs...")
            
            # Check if verb has basic Präsens, Präteritum, Perfekt
            existing_forms = db.query(WordForm).filter(
                WordForm.lemma_id == verb.id,
                WordForm.feature_key == 'tense'
            ).all()
            
            form_dict = {f.feature_value: f.form for f in existing_forms}
            
            # Check if missing essential forms
            essential_forms = [
                'praesens_ich', 'praesens_du', 'praesens_er_sie_es', 
                'praeteritum_ich', 'praeteritum_du', 'praeteritum_er_sie_es',
                'perfekt_ich', 'perfekt_du', 'perfekt_er_sie_es'
            ]
            
            missing_count = sum(1 for form in essential_forms if form not in form_dict)
            
            if missing_count > 0:  # If missing ANY essential forms
                verbs_needing_fix.append((verb, form_dict, missing_count))
        
        print(f"\nFound {len(verbs_needing_fix)} verbs needing conjugation fixes:")
        for verb, _, missing_count in verbs_needing_fix[:10]:  # Show first 10
            print(f"  - {verb.lemma}: missing {missing_count} essential forms")
        if len(verbs_needing_fix) > 10:
            print(f"  ... and {len(verbs_needing_fix) - 10} more")
        
        if len(verbs_needing_fix) == 0:
            print("All verbs already have complete conjugation data!")
            return
        
        print(f"\nProcessing ALL {len(verbs_needing_fix)} incomplete verbs...")
        fixed_count = 0
        
        for i, (verb, existing_forms, missing_count) in enumerate(verbs_needing_fix, 1):
            print(f"\n[{i}/{len(verbs_needing_fix)}] Processing: {verb.lemma}")
            
            # Get complete conjugation from OpenAI
            conjugation_data = await get_complete_conjugation(openai_service, verb.lemma)
            
            if conjugation_data and 'praesens_ich' in conjugation_data:
                added_count = 0
                
                # Add all missing forms
                all_forms = [
                    'praesens_ich', 'praesens_du', 'praesens_er_sie_es', 'praesens_wir', 'praesens_ihr', 'praesens_sie_Sie',
                    'praeteritum_ich', 'praeteritum_du', 'praeteritum_er_sie_es', 'praeteritum_wir', 'praeteritum_ihr', 'praeteritum_sie_Sie',
                    'perfekt_ich', 'perfekt_du', 'perfekt_er_sie_es', 'perfekt_wir', 'perfekt_ihr', 'perfekt_sie_Sie'
                ]
                
                for form_key in all_forms:
                    if form_key not in existing_forms and conjugation_data.get(form_key):
                        form = WordForm(
                            lemma_id=verb.id,
                            form=conjugation_data[form_key],
                            feature_key='tense',
                            feature_value=form_key
                        )
                        db.add(form)
                        added_count += 1
                
                if added_count > 0:
                    print(f"  -> Added {added_count} conjugation forms")
                    fixed_count += 1
                    
                    # Show some examples
                    for tense in ['praesens', 'praeteritum', 'perfekt']:
                        ich_form = conjugation_data.get(f'{tense}_ich')
                        if ich_form:
                            print(f"    {tense}: {ich_form}")
                    
                    # Commit every 10 verbs to avoid huge transactions
                    if fixed_count % 10 == 0:
                        db.commit()
                        print(f"  Committed progress: {fixed_count} verbs fixed")
            
            else:
                print(f"  -> Failed to get conjugation for {verb.lemma}")
        
        # Final commit
        db.commit()
        print(f"\n🎉 COMPLETED! Fixed {fixed_count} out of {len(verbs_needing_fix)} verbs with complete conjugations")
        
        # Test key problematic verbs
        print("\n📊 Testing key verbs:")
        test_verbs = ['bringen', 'kommen', 'machen', 'sehen', 'geben', 'haben', 'sein', 'werden', 'können', 'müssen']
        
        for test_verb in test_verbs:
            word = db.query(WordLemma).filter(WordLemma.lemma == test_verb).first()
            if word:
                tense_forms = db.query(WordForm).filter(
                    WordForm.lemma_id == word.id,
                    WordForm.feature_key == 'tense'
                ).all()
                
                # Count by tense type
                praesens_count = sum(1 for f in tense_forms if f.feature_value.startswith('praesens_'))
                praeteritum_count = sum(1 for f in tense_forms if f.feature_value.startswith('praeteritum_'))
                perfekt_count = sum(1 for f in tense_forms if f.feature_value.startswith('perfekt_'))
                imperativ_count = sum(1 for f in tense_forms if f.feature_value.startswith('imperativ_'))
                
                status = "✅ COMPLETE" if praesens_count >= 6 and praeteritum_count >= 6 and perfekt_count >= 6 else "❌ INCOMPLETE"
                print(f"  {test_verb}: {status} - Präsens={praesens_count}, Präteritum={praeteritum_count}, Perfekt={perfekt_count}, Imperativ={imperativ_count}")
            else:
                print(f"  {test_verb}: ❓ NOT FOUND")
        
    except Exception as e:
        print(f"Error during comprehensive fix: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(fix_all_verbs_comprehensive())