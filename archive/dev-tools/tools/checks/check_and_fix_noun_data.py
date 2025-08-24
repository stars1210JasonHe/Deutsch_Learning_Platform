#!/usr/bin/env python3
"""
Check imported nouns for missing articles and plurals, and fix them.
Some nouns may legitimately not have articles or plurals, so we'll check carefully.
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
from app.models.word import WordLemma, WordForm, Translation, Example


class NounDataChecker:
    def __init__(self):
        pass
    
    def check_noun_completeness(self, db: Session):
        """Check all nouns for missing articles and plurals"""
        
        print("=== Checking Noun Data Completeness ===")
        print()
        
        # Get all nouns from today's imports
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        recent_nouns = db.query(WordLemma).filter(
            WordLemma.pos == 'noun',
            WordLemma.created_at >= today
        ).all()
        
        print(f"Checking {len(recent_nouns)} nouns added today...")
        print()
        
        missing_articles = []
        missing_plurals = []
        complete_nouns = []
        
        for noun in recent_nouns:
            # Check for article
            article_form = db.query(WordForm).filter(
                WordForm.lemma_id == noun.id,
                WordForm.feature_key == 'article'
            ).first()
            
            # Check for plural
            plural_form = db.query(WordForm).filter(
                WordForm.lemma_id == noun.id,
                WordForm.feature_key == 'number',
                WordForm.feature_value == 'plural'
            ).first()
            
            has_article = article_form is not None
            has_plural = plural_form is not None
            
            status = {
                'noun': noun,
                'has_article': has_article,
                'has_plural': has_plural,
                'article_form': article_form.form if article_form else None,
                'plural_form': plural_form.form if plural_form else None
            }
            
            if not has_article:
                missing_articles.append(status)
            if not has_plural:
                missing_plurals.append(status)
            if has_article and has_plural:
                complete_nouns.append(status)
        
        # Report results
        print(f"✅ Complete nouns: {len(complete_nouns)}")
        for status in complete_nouns:
            print(f"  {status['noun'].lemma} - {status['article_form']} {status['noun'].lemma}, plural: {status['plural_form']}")
        
        print(f"\n❌ Missing articles: {len(missing_articles)}")
        for status in missing_articles:
            print(f"  {status['noun'].lemma} (ID: {status['noun'].id})")
        
        print(f"\n❌ Missing plurals: {len(missing_plurals)}")
        for status in missing_plurals:
            print(f"  {status['noun'].lemma} (ID: {status['noun'].id})")
        
        return {
            'complete': complete_nouns,
            'missing_articles': missing_articles,
            'missing_plurals': missing_plurals
        }
    
    async def fix_missing_data_with_openai(self, noun_data: dict):
        """Use OpenAI to fix missing article and plural data"""
        
        noun = noun_data['noun']
        
        print(f"Fixing data for: {noun.lemma}")
        
        prompt = f"""
Analyze the German noun "{noun.lemma}" and provide the missing grammatical information.

Return a JSON object with this structure:
{{
    "lemma": "{noun.lemma}",
    "article": "der/die/das or null if no article needed",
    "plural": "plural form or null if no plural form exists",
    "notes": "any special notes about this noun"
}}

Rules:
- Some nouns don't have articles (proper nouns, some foreign words)
- Some nouns don't have plurals (mass nouns, abstract concepts, etc.)
- Return null for article/plural if they don't exist for this noun
- Be accurate about German grammar rules
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
                    {"role": "system", "content": "You are a German language expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=400
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"OpenAI result: article={result.get('article')}, plural={result.get('plural')}")
            return result
            
        except Exception as e:
            print(f"OpenAI error for {noun.lemma}: {e}")
            return None
    
    async def apply_fixes(self, db: Session, missing_data: dict):
        """Apply fixes to missing data"""
        
        print("\n=== Applying Fixes ===")
        
        # Fix missing articles
        for noun_data in missing_data['missing_articles']:
            try:
                openai_data = await self.fix_missing_data_with_openai(noun_data)
                
                if openai_data and openai_data.get('article'):
                    article = openai_data['article']
                    
                    # Add article form
                    article_form = WordForm(
                        lemma_id=noun_data['noun'].id,
                        form=article,
                        feature_key='article',
                        feature_value='article'
                    )
                    db.add(article_form)
                    print(f"✅ Added article '{article}' for {noun_data['noun'].lemma}")
                else:
                    print(f"ℹ️ {noun_data['noun'].lemma} doesn't need an article")
                
                # Small delay to avoid rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error fixing article for {noun_data['noun'].lemma}: {e}")
        
        # Fix missing plurals
        for noun_data in missing_data['missing_plurals']:
            # Skip if we already processed this noun for articles
            if noun_data in missing_data['missing_articles']:
                # Use the same OpenAI data
                continue
            
            try:
                openai_data = await self.fix_missing_data_with_openai(noun_data)
                
                if openai_data and openai_data.get('plural'):
                    plural = openai_data['plural']
                    
                    # Add plural form
                    plural_form = WordForm(
                        lemma_id=noun_data['noun'].id,
                        form=plural,
                        feature_key='number',
                        feature_value='plural'
                    )
                    db.add(plural_form)
                    print(f"✅ Added plural '{plural}' for {noun_data['noun'].lemma}")
                else:
                    print(f"ℹ️ {noun_data['noun'].lemma} doesn't have a plural form")
                
                # Small delay to avoid rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error fixing plural for {noun_data['noun'].lemma}: {e}")
        
        # Commit all changes
        try:
            db.commit()
            print("\n✅ All fixes committed to database")
        except Exception as e:
            print(f"\n❌ Error committing fixes: {e}")
            db.rollback()
    
    async def run_check_and_fix(self):
        """Main function to check and fix noun data"""
        
        db = SessionLocal()
        
        try:
            # Step 1: Check completeness
            missing_data = self.check_noun_completeness(db)
            
            total_issues = len(missing_data['missing_articles']) + len(missing_data['missing_plurals'])
            
            if total_issues == 0:
                print("\n🎉 All nouns have complete data!")
                return
            
            print(f"\n🔧 Found {total_issues} issues to fix")
            
            # Ask user if they want to proceed with fixes
            response = input("\nFix missing data using OpenAI? (y/n): ").lower().strip()
            
            if response == 'y':
                await self.apply_fixes(db, missing_data)
                
                # Re-check after fixes
                print("\n=== Re-checking after fixes ===")
                final_check = self.check_noun_completeness(db)
                final_issues = len(final_check['missing_articles']) + len(final_check['missing_plurals'])
                
                if final_issues == 0:
                    print("\n🎉 All issues fixed!")
                else:
                    print(f"\n📝 {final_issues} issues remain (some nouns may legitimately not need articles/plurals)")
            else:
                print("Skipping fixes")
        
        finally:
            db.close()


async def main():
    """Main entry point"""
    if sys.platform == "win32":
        os.system("chcp 65001")
    
    checker = NounDataChecker()
    await checker.run_check_and_fix()


if __name__ == "__main__":
    asyncio.run(main())