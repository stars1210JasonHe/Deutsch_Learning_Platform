#!/usr/bin/env python3
"""
Enhanced Collins Dictionary Importer
Following project guidelines: articles + plurals + examples for German words
"""
import asyncio
import sys
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv(".env")
sys.path.append(os.getcwd())

from app.services.openai_service import OpenAIService


class EnhancedCollinsImporter:
    """Enhanced Collins importer following project guidelines"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_path = 'data/app.db'
    
    async def extract_complete_entries(self, text_chunk: str) -> List[Dict[str, Any]]:
        """Extract complete German dictionary entries with all required information"""
        
        system_prompt = """You are a German dictionary expert. Extract complete information for German words.

For each German word, provide:
1. lemma - base German word
2. pos - part of speech ("noun", "verb", "adjective", etc.)
3. article - for nouns: "der", "die", or "das"
4. plural - for nouns: plural form (e.g., "Häuser", "Katzen")
5. translations - array of English meanings
6. examples - exactly 2 German sentences with English translations

Format:
{
  "entries": [
    {
      "lemma": "Haus",
      "pos": "noun", 
      "article": "das",
      "plural": "Häuser",
      "translations": ["house", "building"],
      "examples": [
        {
          "de": "Das Haus ist sehr groß.",
          "en": "The house is very big."
        },
        {
          "de": "Wir kaufen ein neues Haus.",
          "en": "We are buying a new house."
        }
      ]
    }
  ]
}

Focus on clear, common German words. Generate natural example sentences.
If no clear entries found, return {"entries": []}."""

        user_prompt = f"""Extract complete German dictionary entries from this Collins dictionary text:

{text_chunk[:2000]}

Return JSON with complete information including articles, plurals, and 2 examples per word."""

        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            response_content = response.choices[0].message.content
            result = json.loads(response_content.strip())
            
            return result.get('entries', [])
                
        except Exception as e:
            print(f"  Extraction error: {e}")
            return []
    
    async def enhance_existing_word(self, lemma: str, lemma_id: int, pos: str) -> bool:
        """Use OpenAI to enhance existing word with missing information"""
        
        system_prompt = f"""You are enhancing a German {pos} entry. Provide complete information.

For the German {pos} "{lemma}", provide:
1. article - "der", "die", or "das" (if noun)
2. plural - plural form (if noun)
3. examples - exactly 2 natural German sentences with English translations

Format:
{{
  "article": "der/die/das or null",
  "plural": "plural_form or null", 
  "examples": [
    {{"de": "German sentence", "en": "English translation"}},
    {{"de": "German sentence", "en": "English translation"}}
  ]
}}

Make examples natural and educational."""

        user_prompt = f'Enhance the German {pos} "{lemma}" with complete grammatical information and examples. Return JSON format with article, plural, and examples data.'

        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            enhancement = json.loads(response.choices[0].message.content)
            
            # Add missing word forms
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Add article if missing (for nouns)
                if pos == 'noun' and enhancement.get('article'):
                    cursor.execute(
                        "SELECT COUNT(*) FROM word_forms WHERE lemma_id = ? AND feature_key = 'article'",
                        (lemma_id,)
                    )
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, enhancement['article'], 'article', 'article'))
                        print(f"    Added article: {enhancement['article']}")
                
                # Add plural if missing (for nouns) 
                if pos == 'noun' and enhancement.get('plural'):
                    cursor.execute(
                        "SELECT COUNT(*) FROM word_forms WHERE lemma_id = ? AND feature_key = 'plural'",
                        (lemma_id,)
                    )
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, enhancement['plural'], 'plural', 'plural'))
                        print(f"    Added plural: {enhancement['plural']}")
                
                # Add examples if missing
                cursor.execute("SELECT COUNT(*) FROM examples WHERE lemma_id = ?", (lemma_id,))
                if cursor.fetchone()[0] == 0:
                    examples = enhancement.get('examples', [])
                    for example in examples[:2]:  # Limit to 2 examples
                        if example.get('de') and example.get('en'):
                            cursor.execute("""
                                INSERT INTO examples (lemma_id, de_text, en_text, level)
                                VALUES (?, ?, ?, ?)
                            """, (lemma_id, example['de'], example['en'], 'A1'))
                            print(f"    Added example: {example['de']}")
                
                conn.commit()
                conn.close()
                return True
                
            except Exception as db_error:
                print(f"    Database error enhancing {lemma}: {db_error}")
                conn.rollback()
                conn.close()
                return False
                
        except Exception as e:
            print(f"    Enhancement error for {lemma}: {e}")
            return False
    
    def insert_complete_entry(self, entry: Dict[str, Any]) -> bool:
        """Insert complete entry with all information"""
        
        lemma = entry.get('lemma', '').strip()
        if not lemma:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if exists
            cursor.execute("SELECT id FROM word_lemmas WHERE LOWER(lemma) = LOWER(?)", (lemma,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"  {lemma} already exists, skipping")
                conn.close()
                return False
            
            # Insert word lemma
            pos = entry.get('pos', 'other').lower()
            cursor.execute("""
                INSERT INTO word_lemmas (lemma, pos, cefr, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                lemma,
                pos,
                'A1',
                'Enhanced Collins Dictionary import',
                datetime.now().isoformat()
            ))
            
            lemma_id = cursor.lastrowid
            
            # Insert translations
            for translation in entry.get('translations', [])[:3]:
                if translation and len(translation) < 200:
                    cursor.execute("""
                        INSERT INTO translations (lemma_id, lang_code, text, source)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, 'en', translation, 'collins_enhanced'))
            
            # Insert article (for nouns)
            if pos == 'noun' and entry.get('article'):
                cursor.execute("""
                    INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                    VALUES (?, ?, ?, ?)
                """, (lemma_id, entry['article'], 'article', 'article'))
            
            # Insert plural (for nouns)
            if pos == 'noun' and entry.get('plural'):
                cursor.execute("""
                    INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                    VALUES (?, ?, ?, ?)
                """, (lemma_id, entry['plural'], 'plural', 'plural'))
            
            # Insert examples
            for example in entry.get('examples', [])[:2]:
                if example.get('de') and example.get('en'):
                    cursor.execute("""
                        INSERT INTO examples (lemma_id, de_text, en_text, level)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, example['de'], example['en'], 'A1'))
            
            conn.commit()
            conn.close()
            
            # Show what was added
            article_str = f" ({entry.get('article', '')})" if entry.get('article') else ""
            plural_str = f", pl: {entry.get('plural', '')}" if entry.get('plural') else ""
            examples_count = len(entry.get('examples', []))
            
            print(f"  Added {lemma}{article_str} ({pos}){plural_str} - {examples_count} examples")
            return True
            
        except Exception as e:
            print(f"  Error inserting {lemma}: {e}")
            conn.rollback()
            conn.close()
            return False

    async def enhance_existing_collins_entries(self):
        """Enhance existing Collins entries with missing information"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get Collins entries that need enhancement
        cursor.execute("""
            SELECT wl.id, wl.lemma, wl.pos,
                   COUNT(DISTINCT wf.id) as forms_count,
                   COUNT(DISTINCT e.id) as examples_count
            FROM word_lemmas wl
            LEFT JOIN word_forms wf ON wl.id = wf.lemma_id
            LEFT JOIN examples e ON wl.id = e.lemma_id
            WHERE wl.notes LIKE '%Collins%'
            GROUP BY wl.id, wl.lemma, wl.pos
            HAVING forms_count < 2 OR examples_count = 0
        """)
        
        entries_to_enhance = cursor.fetchall()
        conn.close()
        
        print(f"Found {len(entries_to_enhance)} Collins entries needing enhancement:")
        
        for lemma_id, lemma, pos, forms_count, examples_count in entries_to_enhance:
            print(f"  Enhancing {lemma} ({pos}) - {forms_count} forms, {examples_count} examples")
            success = await self.enhance_existing_word(lemma, lemma_id, pos)
            if success:
                print(f"    Enhanced {lemma} successfully")
            else:
                print(f"    Failed to enhance {lemma}")
            
            await asyncio.sleep(1)  # Rate limiting


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Collins dictionary import')
    parser.add_argument('--enhance-existing', action='store_true', 
                       help='Enhance existing Collins entries with missing info')
    parser.add_argument('--extract-new', action='store_true',
                       help='Extract new entries from PDF')
    parser.add_argument('pdf_file', nargs='?', help='Collins PDF file (if extracting new)')
    
    args = parser.parse_args()
    
    importer = EnhancedCollinsImporter()
    
    if args.enhance_existing:
        print("Enhancing Existing Collins Entries")
        print("=" * 40)
        await importer.enhance_existing_collins_entries()
    
    if args.extract_new and args.pdf_file:
        print("\nExtracting New Collins Entries")
        print("=" * 40)
        
        # Use existing extracted text
        text_file = "full_dictionary.txt"
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            print(f"Please first extract PDF text to {text_file}")
            return
        
        # Process first chunk as example
        chunk = text[:3000]
        print("Extracting complete entries with OpenAI...")
        entries = await importer.extract_complete_entries(chunk)
        
        print(f"Found {len(entries)} complete entries")
        
        # Insert entries
        inserted = 0
        for entry in entries:
            if importer.insert_complete_entry(entry):
                inserted += 1
            await asyncio.sleep(0.5)
        
        print(f"Successfully inserted {inserted} complete entries")


if __name__ == "__main__":
    asyncio.run(main())