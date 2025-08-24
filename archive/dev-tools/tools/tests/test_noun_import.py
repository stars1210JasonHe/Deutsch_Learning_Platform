#!/usr/bin/env python3
"""
Test script to import a few German nouns from Excel files into the database.
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
from app.services.openai_service import OpenAIService


class TestNounImporter:
    def __init__(self):
        self.openai_service = OpenAIService()
        
    async def test_excel_reading(self):
        """Test reading Excel files and show structure"""
        excel_files = [
            "german_vocabulary_A1_sample.xlsx",
            "german_vocabulary_A2_sample.xlsx", 
            "german_vocabulary_B1_sample.xlsx"
        ]
        
        for file_path in excel_files:
            if not os.path.exists(file_path):
                print(f"Warning: File {file_path} not found, skipping...")
                continue
                
            try:
                print(f"\n=== Reading {file_path} ===")
                df = pd.read_excel(file_path)
                
                print(f"Columns: {list(df.columns)}")
                print(f"Shape: {df.shape}")
                print("First 10 rows of column A:")
                
                if len(df.columns) > 0:
                    column_a_data = df.iloc[:10, 0].dropna()  # First 10 rows of column A
                    for i, value in enumerate(column_a_data):
                        print(f"  Row {i+1}: {value}")
                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    async def test_openai_enhancement(self):
        """Test OpenAI enhancement with a simple noun"""
        test_noun = "das Thema"
        
        print(f"\n=== Testing OpenAI enhancement for '{test_noun}' ===")
        
        prompt = f"""
Analyze the German noun "{test_noun}" and provide complete grammatical information.

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
            print(f"OpenAI response: {result}")
            return result
            
        except Exception as e:
            print(f"Error with OpenAI: {e}")
            return None

    def test_database_connection(self):
        """Test database connection and check existing nouns"""
        print(f"\n=== Testing database connection ===")
        
        try:
            db = SessionLocal()
            
            # Count existing nouns
            noun_count = db.query(WordLemma).filter(WordLemma.pos == 'noun').count()
            print(f"Existing nouns in database: {noun_count}")
            
            # Show a few examples
            sample_nouns = db.query(WordLemma).filter(WordLemma.pos == 'noun').limit(5).all()
            print("Sample nouns:")
            for noun in sample_nouns:
                print(f"  - {noun.lemma} (ID: {noun.id})")
            
            db.close()
            
        except Exception as e:
            print(f"Database error: {e}")

    async def run_tests(self):
        """Run all tests"""
        print("Starting noun import tests...")
        
        # Test 1: Database connection
        self.test_database_connection()
        
        # Test 2: Excel reading
        await self.test_excel_reading()
        
        # Test 3: OpenAI enhancement
        await self.test_openai_enhancement()
        
        print("\nTests completed!")


async def main():
    """Main entry point"""
    tester = TestNounImporter()
    await tester.run_tests()


if __name__ == "__main__":
    # Ensure proper encoding for German characters
    if sys.platform == "win32":
        os.system("chcp 65001")
    
    asyncio.run(main())