#!/usr/bin/env python3
"""
Script to import a small number of German nouns from Excel files into the database.
This is a test version that processes only a few nouns to verify the functionality.
"""

import asyncio
import sys
import os
import json
from pathlib import Path
import pandas as pd

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm, Translation, Example


class LimitedNounImporter:
    def __init__(self, max_nouns=5):
        self.max_nouns = max_nouns
        
    async def read_few_nouns_from_excel(self):
        """Read only a few nouns from Excel files for testing"""
        excel_files = [
            "german_vocabulary_A1_sample.xlsx"  # Start with just A1
        ]
        
        all_nouns = []
        
        for file_path in excel_files:
            if not os.path.exists(file_path):
                print(f"Warning: File {file_path} not found, skipping...")
                continue
                
            try:
                print(f"Reading {file_path}...")
                df = pd.read_excel(file_path)
                
                # Read column A (German Word)
                if len(df.columns) > 0:
                    column_a_data = df.iloc[:20, 0].dropna()  # First 20 rows
                    
                    for value in column_a_data:
                        if isinstance(value, str) and value.strip():
                            noun = value.strip()
                            
                            if self.is_valid_noun(noun):
                                all_nouns.append(noun)
                                if len(all_nouns) >= self.max_nouns:
                                    break
                
                if len(all_nouns) >= self.max_nouns:
                    break
                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
        
        print(f"Selected {len(all_nouns)} nouns for testing: {all_nouns}")
        return all_nouns
    
    def is_valid_noun(self, text: str) -> bool:
        """Check if the text looks like a valid German noun"""
        if len(text) < 2:
            return False
            
        if text.isdigit():
            return False
            
        # Basic German noun patterns
        if text[0].isupper() or text.startswith(('der ', 'die ', 'das ')):
            return True
            
        return False
    
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
    
    async def process_few_nouns(self):
        """Process a small number of nouns"""
        print(f"Starting limited noun import (max {self.max_nouns} nouns)...")
        
        # Read few nouns from Excel
        nouns = await self.read_few_nouns_from_excel()
        
        if not nouns:
            print("No nouns found!")
            return
        
        # Process each noun
        db = SessionLocal()
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            for noun in nouns:
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
        
        print(f"\nLimited import completed!")
        print(f"Processed: {processed_count}")
        print(f"Skipped: {skipped_count}")  
        print(f"Errors: {error_count}")


async def main():
    """Main entry point"""
    # Test with only 3 nouns first
    importer = LimitedNounImporter(max_nouns=3)
    await importer.process_few_nouns()


if __name__ == "__main__":
    # Ensure proper encoding for German characters
    if sys.platform == "win32":
        os.system("chcp 65001")
    
    asyncio.run(main())