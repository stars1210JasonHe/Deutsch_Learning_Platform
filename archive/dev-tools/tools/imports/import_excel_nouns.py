#!/usr/bin/env python3
"""
Script to import German nouns from Excel files into the database.
Reads column A from A1, A2, B1 level vocabulary Excel files.
Enhances nouns with articles, plurals, and examples using OpenAI.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    import pandas as pd
except ImportError:
    print("Installing pandas...")
    os.system("uv add pandas openpyxl")
    import pandas as pd

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm, Translation, Example
from app.services.openai_service import OpenAIService
from app.services.cache_service import CacheService


class NounImporter:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.cache_service = CacheService()
        
    async def read_excel_files(self):
        """Read nouns from column A of all three Excel files"""
        excel_files = [
            "german_vocabulary_A1_sample.xlsx",
            "german_vocabulary_A2_sample.xlsx", 
            "german_vocabulary_B1_sample.xlsx"
        ]
        
        all_nouns = set()  # Use set to avoid duplicates
        
        for file_path in excel_files:
            if not os.path.exists(file_path):
                print(f"Warning: File {file_path} not found, skipping...")
                continue
                
            try:
                print(f"Reading {file_path}...")
                df = pd.read_excel(file_path)
                
                # Display file structure for debugging
                print(f"Columns in {file_path}: {list(df.columns)}")
                print(f"First few rows:")
                print(df.head())
                
                # Read column A (first column, index 0)
                if len(df.columns) > 0:
                    column_a_data = df.iloc[:, 0].dropna()  # First column, drop empty cells
                    
                    for value in column_a_data:
                        if isinstance(value, str) and value.strip():
                            # Clean the value
                            noun = value.strip()
                            
                            # Skip if it looks like a header or non-noun
                            if not self.is_valid_noun(noun):
                                continue
                                
                            all_nouns.add(noun)
                            print(f"Found noun: {noun}")
                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
        
        print(f"Total unique nouns found: {len(all_nouns)}")
        return list(all_nouns)
    
    def is_valid_noun(self, text: str) -> bool:
        """Check if the text looks like a valid German noun"""
        # Skip obvious headers or non-words
        if len(text) < 2:
            return False
            
        # Skip numbers or mixed content
        if text.isdigit():
            return False
            
        # Basic German noun patterns (should start with capital letter or article)
        if text[0].isupper() or text.startswith(('der ', 'die ', 'das ')):
            return True
            
        return False
    
    async def enhance_noun_with_openai(self, noun: str) -> dict:
        """Use OpenAI to get complete noun information"""
        print(f"Enhancing noun: {noun}")
        
        # Check cache first  
        cache_key = f"noun_enhancement_{noun}"
        try:
            cached = await self.cache_service.get_cached_response(cache_key)
            if cached:
                print(f"Using cached data for {noun}")
                return cached
        except:
            pass  # Cache miss or error, continue
        
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
- if plural is same as singular, still include it
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
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Cache the result
            try:
                await self.cache_service.cache_response(cache_key, result, expire_seconds=86400)  # 24 hours
            except:
                pass  # Cache error, continue
            
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
            frequency=5,  # default frequency
            cefr='A1'  # can be adjusted based on source file
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
    
    async def process_all_nouns(self):
        """Main processing function"""
        print("Starting noun import process...")
        
        # Read all nouns from Excel files
        nouns = await self.read_excel_files()
        
        if not nouns:
            print("No nouns found in Excel files!")
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
                        try:
                            print(f"Skipping {clean_lemma} - already exists")
                        except UnicodeEncodeError:
                            print(f"Skipping noun - already exists (Unicode display error)")
                        skipped_count += 1
                        continue
                    
                    # Enhance with OpenAI
                    noun_data = await self.enhance_noun_with_openai(noun)
                    
                    # Create in database
                    await self.create_noun_in_db(db, noun_data)
                    db.commit()
                    
                    processed_count += 1
                    try:
                        print(f"✓ Added {noun_data['lemma']} to database")
                    except UnicodeEncodeError:
                        print(f"✓ Added noun to database (Unicode display error)")
                    
                    # Rate limiting - pause between OpenAI calls
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error processing {noun}: {e}")
                    db.rollback()
                    continue
        
        finally:
            db.close()
        
        print(f"\nImport completed!")
        print(f"Processed: {processed_count}")
        print(f"Skipped: {skipped_count}")  
        print(f"Errors: {error_count}")


async def main():
    """Main entry point"""
    importer = NounImporter()
    await importer.process_all_nouns()


if __name__ == "__main__":
    # Ensure proper encoding for German characters
    if sys.platform == "win32":
        os.system("chcp 65001")
    
    asyncio.run(main())