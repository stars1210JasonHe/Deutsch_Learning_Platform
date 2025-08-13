#!/usr/bin/env python3
"""
Excel Vocabulary Importer for German Learning Platform
Imports A1, A2, B1 vocabulary from Excel files into the database
"""

import pandas as pd
import os
import sys
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.db.session import SessionLocal
from app.models.word import WordLemma, Translation, Example

class VocabularyImporter:
    def __init__(self):
        self.db = SessionLocal()
        self.stats = {
            'total_processed': 0,
            'new_words': 0,
            'updated_words': 0,
            'skipped_duplicates': 0,
            'errors': 0
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if pd.isna(text) or text is None:
            return ""
        return str(text).strip()
    
    def determine_pos(self, german_word: str, article: str, classification: str) -> str:
        """Determine part of speech from the data"""
        german_word = self.clean_text(german_word).lower()
        article = self.clean_text(article).lower()
        classification = self.clean_text(classification).lower()
        
        # Check for articles (nouns)
        if article in ['der', 'die', 'das']:
            return 'noun'
        
        # Check for common verb patterns
        if (german_word.endswith('en') or german_word.endswith('ern') or 
            german_word.startswith('sich ') or
            classification in ['action', 'movement', 'activity']):
            return 'verb'
        
        # Check for adjective patterns
        if (german_word.endswith('ig') or german_word.endswith('lich') or 
            german_word.endswith('bar') or german_word.endswith('los') or
            classification in ['description', 'quality', 'feeling']):
            return 'adjective'
        
        # Check for common adverb patterns
        if (german_word.endswith('weise') or german_word.endswith('falls') or
            german_word in ['sehr', 'auch', 'nur', 'noch', 'schon', 'immer', 'nie']):
            return 'adverb'
        
        # Check for prepositions
        if german_word in ['in', 'an', 'auf', 'bei', 'mit', 'nach', 'über', 'unter', 'von', 'zu']:
            return 'preposition'
        
        # Default to noun if we can't determine
        return 'noun'
    
    def parse_translations(self, translation_text: str) -> List[str]:
        """Parse translation text into individual translations"""
        if not translation_text or pd.isna(translation_text):
            return []
        
        # Split by common separators
        translations = []
        text = str(translation_text)
        
        # Split by comma, semicolon, or slash
        for sep in [',', ';', '/', '|']:
            if sep in text:
                parts = text.split(sep)
                translations = [part.strip() for part in parts if part.strip()]
                break
        
        # If no separators found, use the whole text
        if not translations:
            translations = [text.strip()]
        
        # Clean up translations
        clean_translations = []
        for trans in translations:
            trans = trans.strip()
            # Remove common prefixes like "to " for verbs
            if trans.startswith('to ') and len(trans) > 3:
                clean_translations.append(trans)
                clean_translations.append(trans[3:])  # Also add without "to"
            else:
                clean_translations.append(trans)
        
        return [t for t in clean_translations if t and len(t) > 1]
    
    def import_word(self, row: pd.Series, cefr_level: str) -> bool:
        """Import a single word from Excel row"""
        try:
            # Extract and clean data
            german_word = self.clean_text(row.get('German Word', ''))
            article = self.clean_text(row.get('Article', ''))
            noun_only = self.clean_text(row.get('Noun Only', ''))
            translation = self.clean_text(row.get('Translation', ''))
            example_sentence = self.clean_text(row.get('Example Sentence', ''))
            classification = self.clean_text(row.get('Classification', ''))
            page_number = row.get('Page Number', None)
            
            if not german_word or not translation:
                print(f"⚠️  Skipping row - missing German word or translation")
                return False
            
            # Use the base form (noun_only if available, otherwise german_word)
            lemma = noun_only if noun_only else german_word
            lemma = lemma.strip()
            
            # Check if word already exists
            existing_word = self.db.query(WordLemma).filter(
                func.lower(WordLemma.lemma) == func.lower(lemma)
            ).first()
            
            if existing_word:
                print(f"📝 Word '{lemma}' already exists (ID: {existing_word.id})")
                self.stats['skipped_duplicates'] += 1
                return True
            
            # Determine part of speech
            pos = self.determine_pos(german_word, article, classification)
            
            # Create new word entry
            word_lemma = WordLemma(
                lemma=lemma,
                pos=pos,
                cefr=cefr_level,
                frequency=None,  # We don't have frequency data
                notes=f"Imported from {cefr_level} vocabulary. Classification: {classification}"
            )
            
            self.db.add(word_lemma)
            self.db.flush()  # Get the ID
            
            # Add English translations
            translations = self.parse_translations(translation)
            for trans_text in translations:
                translation_obj = Translation(
                    lemma_id=word_lemma.id,
                    lang_code='en',
                    text=trans_text,
                    source='excel_import'
                )
                self.db.add(translation_obj)
            
            # Add example sentence if available
            if example_sentence:
                example_obj = Example(
                    lemma_id=word_lemma.id,
                    de_text=example_sentence,
                    en_text="",  # We don't have English translations of examples
                    zh_text="",  # We don't have Chinese translations
                    level=cefr_level
                )
                self.db.add(example_obj)
            
            self.db.commit()
            print(f"✅ Added '{lemma}' ({pos}) with {len(translations)} translations")
            self.stats['new_words'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Error importing word: {e}")
            self.db.rollback()
            self.stats['errors'] += 1
            return False
    
    def import_excel_file(self, file_path: str, cefr_level: str) -> bool:
        """Import vocabulary from a single Excel file"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        try:
            print(f"\n📖 Reading {file_path} ({cefr_level} level)...")
            df = pd.read_excel(file_path)
            
            print(f"📊 Found {len(df)} entries")
            print(f"📋 Columns: {list(df.columns)}")
            
            # Import each row
            for index, row in df.iterrows():
                self.stats['total_processed'] += 1
                
                if self.stats['total_processed'] % 50 == 0:
                    print(f"📈 Processed {self.stats['total_processed']} entries...")
                
                self.import_word(row, cefr_level)
            
            print(f"✅ Completed {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return False
    
    def import_all_files(self) -> None:
        """Import all three Excel files"""
        files = [
            ('german_vocabulary_A1_sample.xlsx', 'A1'),
            ('german_vocabulary_A2_sample.xlsx', 'A2'),
            ('german_vocabulary_B1_sample.xlsx', 'B1')
        ]
        
        print("🚀 Starting Excel vocabulary import...")
        print("=" * 60)
        
        for file_path, cefr_level in files:
            self.import_excel_file(file_path, cefr_level)
        
        # Print final statistics
        print("\n" + "=" * 60)
        print("📊 IMPORT SUMMARY:")
        print(f"📝 Total processed: {self.stats['total_processed']}")
        print(f"✅ New words added: {self.stats['new_words']}")
        print(f"📄 Updated words: {self.stats['updated_words']}")
        print(f"⏩ Skipped duplicates: {self.stats['skipped_duplicates']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print("=" * 60)
        
        # Verify database
        total_words = self.db.query(WordLemma).count()
        print(f"🗄️  Total words in database: {total_words}")

def main():
    """Main import function"""
    try:
        with VocabularyImporter() as importer:
            importer.import_all_files()
        print("\n🎉 Import completed successfully!")
    except Exception as e:
        print(f"\n💥 Import failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
