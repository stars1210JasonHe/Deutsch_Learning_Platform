#!/usr/bin/env python3
"""
Simplified Collins Dictionary Importer
Focuses on basic word information without IPA to avoid encoding issues
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


class SimpleCollinsImporter:
    """Simplified Collins dictionary importer"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_path = 'data/app.db'
    
    async def extract_basic_entries(self, text_chunk: str) -> List[Dict[str, Any]]:
        """Extract basic German dictionary entries without IPA"""
        
        system_prompt = """Extract German dictionary entries from Collins dictionary text.

For each German word, extract:
1. lemma - the German word (base form)
2. pos - part of speech ("noun", "verb", "adjective", etc.)
3. gender - for nouns only ("m", "f", "n")
4. translations - English translations (array)

Focus on clear, unambiguous entries. Skip complex compound phrases.
Return JSON array format:
[
  {
    "lemma": "German_word",
    "pos": "noun/verb/adjective/etc",
    "gender": "m/f/n or null",
    "translations": ["English translation"]
  }
]

If no entries found, return empty array []."""

        user_prompt = f"Extract German dictionary entries from: {text_chunk[:1500]}"

        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            response_content = response.choices[0].message.content
            result = json.loads(response_content.strip())
            
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and 'entries' in result:
                return result['entries']
            else:
                return []
                
        except Exception as e:
            print(f"Extraction error: {e}")
            return []
    
    def insert_simple_entries(self, entries: List[Dict[str, Any]]) -> int:
        """Insert entries with basic error handling"""
        
        if not entries:
            return 0
        
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        cursor = conn.cursor()
        inserted = 0
        
        try:
            for entry in entries:
                lemma = entry.get('lemma', '').strip()
                if not lemma or len(lemma) > 50:  # Skip very long entries
                    continue
                
                # Check if exists
                cursor.execute(
                    "SELECT COUNT(*) FROM word_lemmas WHERE LOWER(lemma) = LOWER(?)", 
                    (lemma,)
                )
                if cursor.fetchone()[0] > 0:
                    continue
                
                # Normalize POS
                pos = entry.get('pos', 'other').lower()
                pos_map = {'n': 'noun', 'v': 'verb', 'adj': 'adjective', 'adv': 'adverb'}
                pos = pos_map.get(pos, pos)
                
                try:
                    # Insert word lemma (no IPA)
                    cursor.execute("""
                        INSERT INTO word_lemmas (lemma, pos, cefr, notes, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        lemma,
                        pos,
                        'A1',
                        'Collins Dictionary import',
                        datetime.now().isoformat()
                    ))
                    
                    lemma_id = cursor.lastrowid
                    
                    # Insert translations
                    translations = entry.get('translations', [])
                    for trans in translations[:3]:  # Limit to 3 translations
                        if trans and len(trans) < 200:
                            cursor.execute("""
                                INSERT INTO translations (lemma_id, lang_code, text, source)
                                VALUES (?, ?, ?, ?)
                            """, (lemma_id, 'en', trans, 'collins_dict'))
                    
                    # Insert gender article for nouns
                    if pos == 'noun' and entry.get('gender') in ['m', 'f', 'n']:
                        articles = {'m': 'der', 'f': 'die', 'n': 'das'}
                        article = articles[entry['gender']]
                        cursor.execute("""
                            INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, article, 'article', 'article'))
                    
                    inserted += 1
                    print(f"  Added: {lemma} ({pos})")
                    
                except Exception as word_error:
                    print(f"  Error with {lemma}: {word_error}")
                    continue
            
            print(f"Successfully inserted {inserted} entries")
            
        except Exception as e:
            print(f"Database error: {e}")
        finally:
            conn.close()
        
        return inserted


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Collins dictionary import')
    parser.add_argument('pdf_file', help='Collins PDF file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_file):
        print(f"File not found: {args.pdf_file}")
        return
    
    print("Simple Collins Dictionary Importer")
    print("=" * 40)
    
    # Read the extracted text file (reuse previous extraction)
    text_file = "full_dictionary.txt"
    if os.path.exists(text_file):
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        print(f"Please first extract PDF text to {text_file}")
        return
    
    importer = SimpleCollinsImporter()
    
    # Process in smaller chunks
    chunk_size = 2000
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    
    print(f"Processing {len(chunks)} text chunks...")
    
    all_entries = []
    for i, chunk in enumerate(chunks[:3]):  # Limit to first 3 chunks for testing
        print(f"Processing chunk {i+1}/{len(chunks[:3])}...")
        entries = await importer.extract_basic_entries(chunk)
        all_entries.extend(entries)
        print(f"  Found {len(entries)} entries")
        await asyncio.sleep(1)  # Rate limiting
    
    print(f"\nTotal entries found: {len(all_entries)}")
    
    # Insert to database
    if all_entries:
        print("Inserting to database...")
        inserted = importer.insert_simple_entries(all_entries)
        print(f"Import complete: {inserted} new entries")


if __name__ == "__main__":
    asyncio.run(main())