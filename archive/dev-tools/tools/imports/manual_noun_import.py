#!/usr/bin/env python3
"""
Manual noun import - interactive version for faster processing.
"""

import asyncio
import sys
import os
import json
from pathlib import Path
import pandas as pd

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, WordForm, Translation, Example


class ManualNounImporter:
    def __init__(self):
        pass
        
    async def get_remaining_nouns(self):
        """Get list of nouns not yet in database"""
        excel_files = [
            "german_vocabulary_A1_sample.xlsx",
            "german_vocabulary_A2_sample.xlsx", 
            "german_vocabulary_B1_sample.xlsx"
        ]
        
        all_nouns = set()
        
        for file_path in excel_files:
            if not os.path.exists(file_path):
                continue
                
            try:
                df = pd.read_excel(file_path)
                
                if len(df.columns) > 0:
                    column_a_data = df.iloc[:, 0].dropna()
                    
                    for value in column_a_data:
                        if isinstance(value, str) and value.strip():
                            noun = value.strip()
                            if self.is_valid_noun(noun):
                                all_nouns.add(noun)
                                
            except Exception as e:
                print(f"Error reading {file_path}: limited due to encoding")
                continue
        
        # Filter out existing nouns
        db = SessionLocal()
        remaining_nouns = []
        
        try:
            for noun in all_nouns:
                clean_lemma = noun.replace('der ', '').replace('die ', '').replace('das ', '').strip()
                
                existing = db.query(WordLemma).filter(
                    WordLemma.lemma == clean_lemma,
                    WordLemma.pos == 'noun'
                ).first()
                
                if not existing:
                    remaining_nouns.append(noun)
                    
        finally:
            db.close()
            
        return remaining_nouns
    
    def is_valid_noun(self, text: str) -> bool:
        """Check if the text looks like a valid German noun"""
        if len(text) < 2 or text.isdigit():
            return False
        return text[0].isupper() or text.startswith(('der ', 'die ', 'das '))
    
    async def process_noun_batch(self, nouns, batch_size=5):
        """Process a batch of nouns"""
        
        print(f"Processing batch of {len(nouns)} nouns...")
        
        for i, noun in enumerate(nouns, 1):
            print(f"\n[{i}/{len(nouns)}] Processing: {noun}")
            
            # Ask user if they want to process this noun
            response = input("Process this noun? (y/n/s=stop): ").lower().strip()
            
            if response == 's':
                print("Stopping batch processing")
                break
            elif response != 'y':
                print("Skipped")
                continue
            
            try:
                # Quick processing without extensive OpenAI calls
                await self.quick_add_noun(noun)
                print(f"✓ Added {noun}")
                
            except Exception as e:
                print(f"✗ Error: {e}")
    
    async def quick_add_noun(self, noun):
        """Add noun with basic info (faster than full OpenAI enhancement)"""
        
        clean_lemma = noun.replace('der ', '').replace('die ', '').replace('das ', '').strip()
        
        # Determine article from noun if present
        if noun.startswith('der '):
            article = 'der'
        elif noun.startswith('die '):
            article = 'die'
        elif noun.startswith('das '):
            article = 'das'
        else:
            article = 'das'  # default
        
        db = SessionLocal()
        
        try:
            # Create basic noun entry
            word_lemma = WordLemma(
                lemma=clean_lemma,
                pos='noun',
                frequency=5,
                cefr='A1'
            )
            db.add(word_lemma)
            db.flush()
            
            # Add basic forms
            forms = [
                (article, 'article', 'article'),
                (clean_lemma, 'number', 'singular'),
                (f"{clean_lemma}s", 'number', 'plural')  # basic plural
            ]
            
            for form, key, value in forms:
                word_form = WordForm(
                    lemma_id=word_lemma.id,
                    form=form,
                    feature_key=key,
                    feature_value=value
                )
                db.add(word_form)
            
            # Add basic translations
            trans_en = Translation(
                lemma_id=word_lemma.id,
                lang_code='en',
                text='translation needed'
            )
            db.add(trans_en)
            
            trans_zh = Translation(
                lemma_id=word_lemma.id,
                lang_code='zh',
                text='需要翻译'
            )
            db.add(trans_zh)
            
            db.commit()
            
        finally:
            db.close()
    
    async def interactive_import(self):
        """Interactive import process"""
        
        print("=== Manual Noun Import ===")
        print()
        
        # Get remaining nouns
        remaining = await self.get_remaining_nouns()
        
        if not remaining:
            print("✅ No remaining nouns to import!")
            return
        
        print(f"Found {len(remaining)} nouns not yet in database:")
        for i, noun in enumerate(remaining[:10], 1):
            print(f"  {i}. {noun}")
        
        if len(remaining) > 10:
            print(f"  ... and {len(remaining) - 10} more")
        
        print()
        print("Options:")
        print("1. Process all remaining nouns interactively")
        print("2. Process first 10 nouns")
        print("3. Process specific noun manually")
        print("4. Show remaining noun list")
        print("5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == '1':
            await self.process_noun_batch(remaining)
        elif choice == '2':
            await self.process_noun_batch(remaining[:10])
        elif choice == '3':
            noun = input("Enter noun to process: ").strip()
            if noun:
                await self.quick_add_noun(noun)
                print(f"✓ Added {noun}")
        elif choice == '4':
            print("\nRemaining nouns:")
            for i, noun in enumerate(remaining, 1):
                print(f"  {i:2d}. {noun}")
        else:
            print("Exiting")


async def main():
    """Main entry point"""
    if sys.platform == "win32":
        os.system("chcp 65001")
    
    importer = ManualNounImporter()
    await importer.interactive_import()


if __name__ == "__main__":
    asyncio.run(main())