#!/usr/bin/env python3
"""
Improved Collins Dictionary Extractor
Based on collins_reading_guide.md - extracts proper grammatical information
Keeps it simple but accurate for UI compatibility
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


class ImprovedCollinsExtractor:
    """Improved Collins extractor following guide principles"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_path = 'data/app.db'

    async def extract_collins_entries_properly(self, text_chunk: str) -> List[Dict[str, Any]]:
        """Extract Collins entries with proper grammatical information"""
        
        system_prompt = """You are a Collins German Dictionary expert. Extract German entries following Collins format rules.

For each German word, extract:

1. **lemma** - base German word
2. **pos** - part of speech (noun, verb, adjective, etc.)
3. **ipa** - pronunciation in [brackets] if present
4. **translations** - English meanings (array)

For NOUNS specifically extract:
5. **gender** - "m", "f", "nt" (neuter)  
6. **genitive** - genitive singular ending (e.g., "-(e)s", "-en")
7. **plural** - plural form or "no pl" for uncountable
8. **countability** - "countable", "uncountable", "pl-only" 

For VERBS specifically extract:
9. **transitivity** - "vt" (transitive), "vi" (intransitive), "vr" (reflexive)
10. **separable** - true/false for particle verbs
11. **preposition** - governed preposition if any (e.g., "auf +acc", "mit +dat")

For ADJECTIVES extract:
12. **government** - preposition + case if any (e.g., "stolz auf +acc")

For ALL words extract:
13. **domain_labels** - field labels like "(Anat)", "(Tech)", "(inf)" etc.
14. **examples** - 1-2 German sentences with English translations

Return JSON:
{
  "entries": [
    {
      "lemma": "Membran",
      "pos": "noun", 
      "ipa": "[mεmˈbraːn]",
      "gender": "f",
      "genitive": "-",
      "plural": "Membranen",
      "countability": "countable",
      "translations": ["membrane", "diaphragm"],
      "domain_labels": ["(Anat)", "(Tech)"],
      "examples": [
        {"de": "Die Membran ist dünn.", "en": "The membrane is thin."}
      ]
    }
  ]
}

Focus on extracting real Collins dictionary entries, not generated content."""

        user_prompt = f"""Extract German dictionary entries from this Collins text:

{text_chunk[:2000]}

Return JSON with proper grammatical information according to Collins format."""

        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('entries', [])
            
        except Exception as e:
            print(f"  Error extracting: {e}")
            return []

    async def enhance_with_chinese(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add Chinese translations to entries"""
        
        for entry in entries:
            try:
                lemma = entry.get('lemma', '')
                translations = entry.get('translations', [])
                
                if lemma and translations:
                    # Generate Chinese translations
                    chinese_translations = await self.generate_chinese_translations(lemma, translations)
                    if chinese_translations:
                        entry['chinese_translations'] = chinese_translations
                    
                    # Add Chinese to examples
                    examples = entry.get('examples', [])
                    for example in examples:
                        if example.get('de') and example.get('en'):
                            zh_text = await self.generate_chinese_example(example['de'], example['en'])
                            if zh_text:
                                example['zh'] = zh_text
                
                await asyncio.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"  Error adding Chinese for {entry.get('lemma', 'unknown')}: {e}")
                continue
        
        return entries

    async def generate_chinese_translations(self, lemma: str, en_translations: List[str]) -> List[str]:
        """Generate Chinese translations"""
        
        system_prompt = f"""Translate German word "{lemma}" to Chinese.

English meanings: {', '.join(en_translations)}

Return JSON: {{"chinese": ["中文1", "中文2"]}}"""

        user_prompt = f'German: {lemma} → Chinese translations (2-3 words)'

        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('chinese', [])[:3]
            
        except Exception as e:
            return []

    async def generate_chinese_example(self, de_text: str, en_text: str) -> str:
        """Generate Chinese example translation"""
        
        system_prompt = """Translate German sentence to Chinese. Use English as reference.

Return only the Chinese translation."""

        user_prompt = f'German: {de_text}\nEnglish: {en_text}\nChinese:'

        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return None

    def save_improved_entry(self, entry: Dict[str, Any]) -> bool:
        """Save entry with improved Collins grammatical information"""
        
        lemma = entry.get('lemma', '').strip()
        pos = entry.get('pos', 'other').lower()
        
        if not lemma:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if exists
            cursor.execute("SELECT id FROM word_lemmas WHERE LOWER(lemma) = LOWER(?)", (lemma,))
            existing = cursor.fetchone()
            
            if existing:
                lemma_id = existing[0]
                print(f"    Updating: {lemma}")
                # Clear existing data
                cursor.execute("DELETE FROM word_forms WHERE lemma_id = ?", (lemma_id,))
                cursor.execute("DELETE FROM examples WHERE lemma_id = ?", (lemma_id,))
                cursor.execute("DELETE FROM translations WHERE lemma_id = ? AND source LIKE '%collins%'", (lemma_id,))
            else:
                print(f"    Inserting: {lemma}")
                # Insert new lemma
                ipa = entry.get('ipa', '').replace('[', '').replace(']', '') if entry.get('ipa') else None
                cursor.execute("""
                    INSERT INTO word_lemmas (lemma, pos, ipa, cefr, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (lemma, pos, ipa, 'A1', 'Collins Dictionary - Improved', datetime.now().isoformat()))
                lemma_id = cursor.lastrowid
            
            # Insert English translations
            for translation in entry.get('translations', [])[:5]:
                if translation:
                    cursor.execute("""
                        INSERT INTO translations (lemma_id, lang_code, text, source)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, 'en', translation, 'collins_improved'))
            
            # Insert Chinese translations
            for zh_translation in entry.get('chinese_translations', [])[:3]:
                if zh_translation:
                    cursor.execute("""
                        INSERT INTO translations (lemma_id, lang_code, text, source)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, 'zh', zh_translation, 'collins_chinese'))
            
            # Insert examples
            for example in entry.get('examples', [])[:2]:
                if example.get('de') and example.get('en'):
                    cursor.execute("""
                        INSERT INTO examples (lemma_id, de_text, en_text, zh_text, level)
                        VALUES (?, ?, ?, ?, ?)
                    """, (lemma_id, example['de'], example['en'], example.get('zh'), 'A1'))
            
            # Handle noun-specific Collins data
            if pos == 'noun':
                gender = entry.get('gender', '')
                if gender in ['m', 'f', 'nt']:
                    article = {'m': 'der', 'f': 'die', 'nt': 'das'}[gender]
                    cursor.execute("""
                        INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, article, 'article', 'article'))
                
                # Plural handling
                plural = entry.get('plural', '')
                countability = entry.get('countability', 'countable')
                
                if plural and plural != 'no pl' and countability != 'uncountable':
                    cursor.execute("""
                        INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, plural, 'plural', 'plural'))
                
                # Genitive if available
                genitive = entry.get('genitive', '')
                if genitive and genitive != '-':
                    genitive_form = lemma + genitive.replace('-(', '').replace(')', '')  # Simplified
                    cursor.execute("""
                        INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, genitive_form, 'genitive', 'genitive_singular'))
            
            # Handle verb-specific Collins data
            elif pos == 'verb':
                transitivity = entry.get('transitivity', '')
                separable = entry.get('separable', False)
                preposition = entry.get('preposition', '')
                
                # Save verb properties in notes
                verb_info = {
                    'transitivity': transitivity,
                    'separable': separable,
                    'preposition': preposition
                }
                cursor.execute("""
                    UPDATE word_lemmas SET notes = notes || ' | verb_info: ' || ?
                    WHERE id = ?
                """, (json.dumps(verb_info), lemma_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"    Error saving {lemma}: {e}")
            conn.rollback()
            conn.close()
            return False


async def main():
    """Main function - simplified interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Improved Collins dictionary extractor')
    parser.add_argument('--test', action='store_true', help='Test with first 2 chunks')
    parser.add_argument('--process-all', action='store_true', help='Process all chunks')
    parser.add_argument('pdf_file', help='Collins PDF file')
    
    args = parser.parse_args()
    
    if not os.path.exists("full_dictionary.txt"):
        print("Please ensure full_dictionary.txt exists (extract PDF first)")
        return
    
    print("=== Improved Collins Dictionary Extractor ===")
    print("Following Collins reading guide principles")
    print()
    
    extractor = ImprovedCollinsExtractor()
    
    # Load text
    with open("full_dictionary.txt", 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Process in chunks
    chunk_size = 8000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    print(f"Total text length: {len(text)} characters")
    print(f"Created {len(chunks)} chunks with size {chunk_size}")
    
    if args.test:
        chunks_to_process = chunks[:2]
        print("TEST MODE: Processing first 2 chunks")
    elif args.process_all:
        chunks_to_process = chunks
        print(f"FULL MODE: Processing all {len(chunks)} chunks")
    else:
        chunks_to_process = chunks[:3]
        print("DEFAULT MODE: Processing first 3 chunks")
    
    all_entries = []
    
    # Extract entries
    for i, chunk in enumerate(chunks_to_process):
        print(f"Extracting from chunk {i+1}/{len(chunks_to_process)}...")
        entries = await extractor.extract_collins_entries_properly(chunk)
        print(f"  Found {len(entries)} entries")
        all_entries.extend(entries)
        await asyncio.sleep(1)
    
    if not all_entries:
        print("No entries found!")
        return
    
    print(f"\nEnhancing {len(all_entries)} entries with Chinese translations...")
    enhanced_entries = await extractor.enhance_with_chinese(all_entries)
    
    print(f"\nSaving to database...")
    saved_count = 0
    
    for entry in enhanced_entries:
        if extractor.save_improved_entry(entry):
            saved_count += 1
        await asyncio.sleep(0.5)
    
    print(f"\n=== COMPLETED ===")
    print(f"Extracted: {len(all_entries)} entries")
    print(f"Saved: {saved_count} entries")
    print("Entries now have proper Collins grammatical information!")
    print("Ready for UI - maintains compatibility with WordResult.vue")


if __name__ == "__main__":
    asyncio.run(main())