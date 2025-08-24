#!/usr/bin/env python3
"""
Fix missing articles and plurals for nouns using OpenAI in batches.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm


class NounFixer:
    def __init__(self, batch_size=10):
        self.batch_size = batch_size
    
    def get_nouns_missing_data(self, db: Session, limit=50):
        """Get nouns missing articles or plurals"""
        
        all_nouns = db.query(WordLemma).filter(WordLemma.pos == 'noun').limit(limit).all()
        
        missing_data = []
        
        for noun in all_nouns:
            article_form = db.query(WordForm).filter(
                WordForm.lemma_id == noun.id,
                WordForm.feature_key == 'article'
            ).first()
            
            plural_form = db.query(WordForm).filter(
                WordForm.lemma_id == noun.id,
                WordForm.feature_key == 'number',
                WordForm.feature_value == 'plural'
            ).first()
            
            missing_article = article_form is None
            missing_plural = plural_form is None
            
            if missing_article or missing_plural:
                missing_data.append({
                    'noun': noun,
                    'missing_article': missing_article,
                    'missing_plural': missing_plural
                })
        
        return missing_data
    
    async def fix_noun_with_openai(self, noun_data: dict):
        """Fix a single noun using OpenAI"""
        
        noun = noun_data['noun']
        
        prompt = f"""
Analyze the German noun "{noun.lemma}" and provide the missing grammatical information.

Return JSON with this structure:
{{
    "article": "der/die/das or null if this word doesn't need an article",
    "plural": "plural form or null if this word has no plural",
    "notes": "brief explanation if article/plural is null"
}}

Rules:
- Return null for article if the word doesn't need one (proper nouns, some foreign words, etc.)
- Return null for plural if the word has no plural form (mass nouns, abstract concepts, etc.)
- Be accurate about German grammar
"""

        try:
            from openai import AsyncOpenAI
            from app.core.config import settings
            
            client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
            
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a German grammar expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"OpenAI error for {noun.lemma}: {e}")
            return None
    
    async def apply_fixes(self, db: Session, missing_data: list):
        """Apply fixes to missing data"""
        
        print(f"Fixing {len(missing_data)} nouns...")
        
        fixed_count = 0
        
        for i, noun_data in enumerate(missing_data):
            try:
                noun = noun_data['noun']
                
                print(f"[{i+1}/{len(missing_data)}] Fixing: {noun.lemma}")
                
                # Get OpenAI data
                openai_data = await self.fix_noun_with_openai(noun_data)
                
                if not openai_data:
                    continue
                
                # Add missing article
                if noun_data['missing_article'] and openai_data.get('article'):
                    article_form = WordForm(
                        lemma_id=noun.id,
                        form=openai_data['article'],
                        feature_key='article',
                        feature_value='article'
                    )
                    db.add(article_form)
                    print(f"  + Added article: {openai_data['article']}")
                
                # Add missing plural
                if noun_data['missing_plural'] and openai_data.get('plural'):
                    plural_form = WordForm(
                        lemma_id=noun.id,
                        form=openai_data['plural'],
                        feature_key='number',
                        feature_value='plural'
                    )
                    db.add(plural_form)
                    print(f"  + Added plural: {openai_data['plural']}")
                
                # Also add singular if missing
                singular_form = db.query(WordForm).filter(
                    WordForm.lemma_id == noun.id,
                    WordForm.feature_key == 'number',
                    WordForm.feature_value == 'singular'
                ).first()
                
                if not singular_form:
                    singular_form = WordForm(
                        lemma_id=noun.id,
                        form=noun.lemma,
                        feature_key='number',
                        feature_value='singular'
                    )
                    db.add(singular_form)
                    print(f"  + Added singular: {noun.lemma}")
                
                fixed_count += 1
                
                # Commit every 10 nouns
                if i % 10 == 0:
                    db.commit()
                    print(f"  ✓ Committed batch")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error fixing {noun.lemma}: {e}")
                continue
        
        # Final commit
        try:
            db.commit()
            print(f"\n✅ Fixed {fixed_count} nouns!")
        except Exception as e:
            print(f"Error committing final changes: {e}")
    
    async def run_fix(self, limit=50):
        """Main fix function"""
        
        print(f"=== Fixing Missing Noun Data (first {limit} nouns) ===")
        print()
        
        db = SessionLocal()
        
        try:
            # Get nouns with missing data
            missing_data = self.get_nouns_missing_data(db, limit)
            
            if not missing_data:
                print("No nouns need fixing!")
                return
            
            print(f"Found {len(missing_data)} nouns with missing data")
            
            # Show what will be fixed
            for noun_data in missing_data[:10]:
                issues = []
                if noun_data['missing_article']:
                    issues.append("article")
                if noun_data['missing_plural']:
                    issues.append("plural")
                
                print(f"  - {noun_data['noun'].lemma}: missing {', '.join(issues)}")
            
            if len(missing_data) > 10:
                print(f"  ... and {len(missing_data) - 10} more")
            
            response = input(f"\nFix these {len(missing_data)} nouns? (y/n): ").lower().strip()
            
            if response == 'y':
                await self.apply_fixes(db, missing_data)
            else:
                print("Cancelled")
        
        finally:
            db.close()


async def main():
    """Main entry point"""
    if sys.platform == "win32":
        os.system("chcp 65001")
    
    limit = 100  # Fix first 100 nouns
    
    fixer = NounFixer()
    await fixer.run_fix(limit)


if __name__ == "__main__":
    asyncio.run(main())