#!/usr/bin/env python3
"""
Test script to import specific nouns that we know don't exist yet.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm, Translation, Example


class SpecificNounImporter:
    def __init__(self):
        pass
        
    async def enhance_noun_with_openai(self, noun: str) -> dict:
        """Use OpenAI to get complete noun information"""
        print(f"Enhancing noun: {noun}")
        
        prompt = f"""
Analyze the German noun "{noun}" and provide complete grammatical information.

Return a JSON object with this exact structure:
{{
    "lemma": "base form without article",
    "article": "der/die/das", 
    "plural": "plural form",
    "translations_en": ["english translation 1", "english translation 2"],
    "translations_zh": ["中文翻译1", "中文翻译2"],
    "example_de": "German example sentence using the noun",
    "example_en": "English translation of the example",
    "example_zh": "中文例句翻译",
    "gender": "masculine/feminine/neuter"
}}

Important:
- lemma should be the noun without article (e.g., "Thema" not "das Thema")  
- article should be der/die/das only
- provide 1-2 common translations in each language
- example should be a natural German sentence
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
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"Enhanced {noun}: {result.get('lemma', noun)} ({result.get('article', 'unknown')})")
            return result
            
        except Exception as e:
            print(f"Error enhancing noun {noun}: {e}")
            return {
                "lemma": noun.replace('der ', '').replace('die ', '').replace('das ', '').strip(),
                "article": "das",  # default
                "plural": noun,
                "translations_en": ["unknown"],
                "translations_zh": ["未知"],
                "example_de": f"Das ist {noun}.",
                "example_en": f"This is {noun}.",
                "example_zh": f"这是{noun}。",
                "gender": "neuter"
            }
    
    def noun_exists_in_db(self, db: Session, lemma: str) -> bool:
        """Check if noun already exists in database"""
        existing = db.query(WordLemma).filter(
            WordLemma.lemma == lemma,
            WordLemma.pos == 'noun'
        ).first()
        return existing is not None
    
    async def create_noun_in_db(self, db: Session, noun_data: dict) -> WordLemma:
        """Create complete noun entry in database"""
        lemma = noun_data['lemma']
        
        # Create WordLemma
        word_lemma = WordLemma(
            lemma=lemma,
            pos='noun',
            frequency=5,
            cefr='A1'
        )
        db.add(word_lemma)
        db.flush()  # Get the ID
        
        # Create article WordForm
        article_form = WordForm(
            lemma_id=word_lemma.id,
            form=noun_data['article'],
            feature_key='article',
            feature_value='article'
        )
        db.add(article_form)
        
        # Create singular WordForm  
        singular_form = WordForm(
            lemma_id=word_lemma.id,
            form=lemma,
            feature_key='number',
            feature_value='singular'
        )
        db.add(singular_form)
        
        # Create plural WordForm
        plural_form = WordForm(
            lemma_id=word_lemma.id,
            form=noun_data['plural'],
            feature_key='number', 
            feature_value='plural'
        )
        db.add(plural_form)
        
        # Create English translations
        for translation in noun_data.get('translations_en', []):
            trans = Translation(
                lemma_id=word_lemma.id,
                lang_code='en',
                text=translation
            )
            db.add(trans)
        
        # Create Chinese translations
        for translation in noun_data.get('translations_zh', []):
            trans = Translation(
                lemma_id=word_lemma.id,
                lang_code='zh',
                text=translation
            )
            db.add(trans)
        
        # Create example
        if noun_data.get('example_de'):
            example = Example(
                lemma_id=word_lemma.id,
                de_text=noun_data['example_de'],
                en_text=noun_data.get('example_en', ''),
                zh_text=noun_data.get('example_zh', '')
            )
            db.add(example)
        
        return word_lemma
    
    async def process_specific_nouns(self):
        """Process specific nouns that are likely not in the database"""
        print("Testing noun import with specific nouns...")
        
        # Test nouns from the Excel files that are likely missing
        test_nouns = [
            "das Kfz",     # From the failed import
            "das EG", 
            "der Lkw",
            "die WG"
        ]
        
        # Process each noun
        db = SessionLocal()
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            for noun in test_nouns:
                try:
                    # Extract lemma (remove article if present)
                    clean_lemma = noun.replace('der ', '').replace('die ', '').replace('das ', '').strip()
                    
                    # Check if already exists
                    if self.noun_exists_in_db(db, clean_lemma):
                        print(f"Skipping {clean_lemma} - already exists")
                        skipped_count += 1
                        continue
                    
                    # Enhance with OpenAI
                    noun_data = await self.enhance_noun_with_openai(noun)
                    
                    # Create in database
                    await self.create_noun_in_db(db, noun_data)
                    db.commit()
                    
                    processed_count += 1
                    print(f"✓ Added {noun_data['lemma']} to database")
                    
                    # Rate limiting - pause between OpenAI calls
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error processing {noun}: {e}")
                    db.rollback()
                    continue
        
        finally:
            db.close()
        
        print(f"\nSpecific noun import completed!")
        print(f"Processed: {processed_count}")
        print(f"Skipped: {skipped_count}")  
        print(f"Errors: {error_count}")


async def main():
    """Main entry point"""
    importer = SpecificNounImporter()
    await importer.process_specific_nouns()


if __name__ == "__main__":
    # Ensure proper encoding for German characters
    if sys.platform == "win32":
        os.system("chcp 65001")
    
    asyncio.run(main())