#!/usr/bin/env python3
"""
Systematic noun enhancement - fix Unicode encoding issues
"""
import asyncio
import sys
import os
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm
from app.services.openai_service import OpenAIService


async def enhance_noun_with_openai(openai_service: OpenAIService, lemma: str) -> Optional[Dict[str, Any]]:
    """Get article and plural for a noun using OpenAI"""
    
    prompt = f"""
    Analyze the German noun "{lemma}" and return a JSON response with its grammatical information.
    
    Return:
    {{
        "word": "{lemma}",
        "article": "der|die|das",
        "plural": "plural form",
        "gender": "masculine|feminine|neuter"
    }}
    
    Examples:
    - Tisch: {{"word": "Tisch", "article": "der", "plural": "Tische", "gender": "masculine"}}
    - Raum: {{"word": "Raum", "article": "der", "plural": "Räume", "gender": "masculine"}}
    - Bank (furniture): {{"word": "Bank", "article": "die", "plural": "Bänke", "gender": "feminine"}}
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
        print(f"Error analyzing {lemma}: {e}")
        return None


async def fix_nouns_systematically():
    """Fix all nouns that are missing article and plural data"""
    
    # Force UTF-8 encoding for Windows
    if sys.platform == "win32":
        import locale
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass
    
    print("Starting systematic noun enhancement...")
    
    openai_service = OpenAIService()
    db = SessionLocal()
    
    try:
        # Find all nouns without article data
        nouns_without_article = db.query(WordLemma).filter(
            WordLemma.pos.in_(['noun', 'NOUN']),
            ~WordLemma.forms.any(WordForm.feature_key == 'article')
        ).all()
        
        print(f"Found {len(nouns_without_article)} nouns without article data")
        
        enhanced_count = 0
        
        for noun in nouns_without_article:
            print(f"Processing: {noun.lemma}")
            
            # Get OpenAI analysis
            analysis = await enhance_noun_with_openai(openai_service, noun.lemma)
            
            if analysis and analysis.get('article') and analysis.get('plural'):
                # Add article
                article_form = WordForm(
                    lemma_id=noun.id,
                    form=analysis['article'],
                    feature_key='article',
                    feature_value='definite'
                )
                db.add(article_form)
                
                # Add plural
                plural_form = WordForm(
                    lemma_id=noun.id,
                    form=analysis['plural'],
                    feature_key='plural',
                    feature_value='plural'
                )
                db.add(plural_form)
                
                # Add gender if available
                if analysis.get('gender'):
                    gender_form = WordForm(
                        lemma_id=noun.id,
                        form=analysis['gender'],
                        feature_key='gender',
                        feature_value='gender'
                    )
                    db.add(gender_form)
                
                enhanced_count += 1
                print(f"  -> Enhanced: {analysis['article']} {noun.lemma}, Plural: {analysis['plural']}")
                
                # Commit every 5 words to avoid losing progress
                if enhanced_count % 5 == 0:
                    db.commit()
                    print(f"Committed progress: {enhanced_count} nouns enhanced")
            
            else:
                print(f"  -> Failed to get analysis for {noun.lemma}")
        
        # Final commit
        db.commit()
        print(f"\nCompleted! Enhanced {enhanced_count} nouns total")
        
    except Exception as e:
        print(f"Error during enhancement: {e}")
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(fix_nouns_systematically())