#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix verbs missing Imperativ conjugations
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


async def get_imperativ_from_openai(openai_service: OpenAIService, lemma: str) -> dict:
    """Get Imperativ forms for a verb using OpenAI"""
    
    prompt = f"""
    Generate the German Imperativ (imperative) forms for the verb "{lemma}".
    
    Return a JSON response:
    {{
        "verb": "{lemma}",
        "imperativ_du": "du form (e.g., geh!, nimm!)",
        "imperativ_ihr": "ihr form (e.g., geht!, nehmt!)", 
        "imperativ_Sie": "Sie form (e.g., gehen Sie!, nehmen Sie!)"
    }}
    
    Examples:
    - gehen: {{"imperativ_du": "geh", "imperativ_ihr": "geht", "imperativ_Sie": "gehen Sie"}}
    - nehmen: {{"imperativ_du": "nimm", "imperativ_ihr": "nehmt", "imperativ_Sie": "nehmen Sie"}}
    - sein: {{"imperativ_du": "sei", "imperativ_ihr": "seid", "imperativ_Sie": "seien Sie"}}
    """
    
    try:
        response = await openai_service.client.chat.completions.create(
            model=openai_service.model,
            messages=[
                {"role": "system", "content": "You are a German grammar expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )
        
        analysis = json.loads(response.choices[0].message.content)
        return analysis
        
    except Exception as e:
        print(f"Error getting Imperativ for {lemma}: {e}")
        return {}


async def fix_missing_imperativ():
    """Find and fix verbs missing Imperativ forms"""
    
    print("Finding verbs missing Imperativ forms...")
    
    openai_service = OpenAIService()
    db = SessionLocal()
    
    try:
        # Find verbs that don't have any imperativ forms
        verbs_missing_imperativ = db.query(WordLemma).filter(
            WordLemma.pos.in_(['verb', 'VERB']),
            ~WordLemma.forms.any(
                (WordForm.feature_key == 'tense') & 
                (WordForm.feature_value.like('imperativ_%'))
            )
        ).limit(20).all()  # Limit to avoid too many API calls
        
        print(f"Found {len(verbs_missing_imperativ)} verbs missing Imperativ forms")
        
        fixed_count = 0
        
        for verb in verbs_missing_imperativ:
            print(f"Processing: {verb.lemma}")
            
            # Get Imperativ forms from OpenAI
            imperativ_data = await get_imperativ_from_openai(openai_service, verb.lemma)
            
            if imperativ_data and 'imperativ_du' in imperativ_data:
                # Add imperativ_du
                if imperativ_data.get('imperativ_du'):
                    form = WordForm(
                        lemma_id=verb.id,
                        form=imperativ_data['imperativ_du'],
                        feature_key='tense',
                        feature_value='imperativ_du'
                    )
                    db.add(form)
                
                # Add imperativ_ihr  
                if imperativ_data.get('imperativ_ihr'):
                    form = WordForm(
                        lemma_id=verb.id,
                        form=imperativ_data['imperativ_ihr'],
                        feature_key='tense',
                        feature_value='imperativ_ihr'
                    )
                    db.add(form)
                
                # Add imperativ_Sie
                if imperativ_data.get('imperativ_Sie'):
                    form = WordForm(
                        lemma_id=verb.id,
                        form=imperativ_data['imperativ_Sie'],
                        feature_key='tense',
                        feature_value='imperativ_Sie'
                    )
                    db.add(form)
                
                fixed_count += 1
                print(f"  -> Added Imperativ: du={imperativ_data.get('imperativ_du')}, ihr={imperativ_data.get('imperativ_ihr')}, Sie={imperativ_data.get('imperativ_Sie')}")
                
                # Commit every 5 verbs
                if fixed_count % 5 == 0:
                    db.commit()
                    print(f"Committed progress: {fixed_count} verbs fixed")
            
            else:
                print(f"  -> Failed to get Imperativ for {verb.lemma}")
        
        # Final commit
        db.commit()
        print(f"\nCompleted! Fixed {fixed_count} verbs with Imperativ forms")
        
        # Test a few key verbs
        print("\nVerifying key verbs:")
        for test_verb in ['nehmen', 'sein', 'haben', 'machen', 'kommen']:
            word = db.query(WordLemma).filter(WordLemma.lemma == test_verb).first()
            if word:
                imperativ_forms = db.query(WordForm).filter(
                    WordForm.lemma_id == word.id,
                    WordForm.feature_key == 'tense',
                    WordForm.feature_value.like('imperativ_%')
                ).all()
                
                if imperativ_forms:
                    print(f"{test_verb}: {len(imperativ_forms)} Imperativ forms")
                    for form in imperativ_forms:
                        print(f"  {form.feature_value}: {form.form}")
                else:
                    print(f"{test_verb}: No Imperativ forms found")
        
    except Exception as e:
        print(f"Error during fix: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(fix_missing_imperativ())