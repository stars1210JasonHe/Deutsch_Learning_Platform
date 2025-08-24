#!/usr/bin/env python3
"""
German Dictionary Entry Extractor
Uses OpenAI to parse Collins German Dictionary entries from PDF text
and prepare data for database insertion
"""
import asyncio
import sys
import os
import json
import re
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
sys.path.append(os.getcwd())

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not found. Install with: uv add pypdf2")
    sys.exit(1)

from app.services.openai_service import OpenAIService


class GermanDictionaryExtractor:
    """Extract German dictionary entries using OpenAI"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_path = 'data/app.db'
        
    async def extract_dictionary_entries(self, text_chunk: str) -> List[Dict[str, Any]]:
        """Extract German dictionary entries from text using OpenAI"""
        
        system_prompt = """You are a German dictionary parsing expert. Extract German dictionary entries from the given text.

For each German word entry you find, extract:
1. lemma - the base German word (e.g., "gehen", "Haus", "schön")
2. pos - part of speech ("verb", "noun", "adjective", "adverb", "preposition", etc.)
3. ipa - IPA pronunciation if available (e.g., "[ˈgeːən]")
4. gender - for nouns only ("m", "f", "n" for der/die/das)
5. translations - list of English translations
6. examples - any German example sentences with English translations if available

Dictionary entry patterns to look for:
- German word followed by IPA pronunciation in brackets: word [IPA]
- Part of speech indicators: n (noun), vt (transitive verb), vi (intransitive verb), adj (adjective)
- Gender indicators: m, f, n or der, die, das
- Translations separated by commas or semicolons
- Example sentences in German with English equivalents

Return only a JSON array of dictionary entries. Each entry should have this structure:
{
  "lemma": "German word",
  "pos": "part of speech",
  "ipa": "IPA pronunciation or null",
  "gender": "m/f/n or null",
  "translations": ["English translation 1", "English translation 2"],
  "examples": [
    {
      "de": "German example sentence",
      "en": "English translation"
    }
  ]
}

If no clear dictionary entries are found, return an empty array []."""

        user_prompt = f"""Extract all German dictionary entries from this text:

{text_chunk}

Return only the JSON array of extracted entries."""

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
            
            # Handle both array and object responses
            if isinstance(result, dict) and 'entries' in result:
                return result['entries']
            elif isinstance(result, list):
                return result
            elif isinstance(result, dict) and len(result) == 0:
                return []
            else:
                print(f"Unexpected response format: {type(result)}")
                return []
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response content: {response_content[:200]}...")
            return []
        except Exception as e:
            print(f"OpenAI extraction error: {e}")
            return []
    
    def normalize_pos(self, pos: str) -> str:
        """Normalize part of speech to standard format"""
        if not pos:
            return "other"
            
        pos = pos.lower().strip()
        
        # Map common abbreviations to standard forms
        pos_mapping = {
            "n": "noun",
            "v": "verb", 
            "vt": "verb",
            "vi": "verb",
            "vr": "verb",
            "adj": "adjective",
            "adv": "adverb",
            "prep": "preposition",
            "conj": "conjunction",
            "art": "article",
            "pron": "pronoun",
            "num": "numeral",
            "interj": "interjection"
        }
        
        return pos_mapping.get(pos, pos)
    
    async def process_pdf_in_chunks(self, pdf_path: str, chunk_size: int = 3000) -> List[Dict[str, Any]]:
        """Process entire PDF by extracting text and parsing in chunks"""
        
        # First extract text from PDF
        print(f"Extracting text from PDF: {pdf_path}")
        text = self.extract_pdf_text(pdf_path)
        
        if not text:
            print("Failed to extract text from PDF")
            return []
        
        print(f"Extracted {len(text)} characters from PDF")
        
        # Split text into chunks
        chunks = self.split_text_into_chunks(text, chunk_size)
        print(f"Split text into {len(chunks)} chunks for processing")
        
        all_entries = []
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            
            try:
                entries = await self.extract_dictionary_entries(chunk)
                all_entries.extend(entries)
                print(f"  Found {len(entries)} entries in chunk {i+1}")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"  Error processing chunk {i+1}: {e}")
                continue
        
        print(f"Total entries extracted: {len(all_entries)}")
        return all_entries
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += page_text + "\n"
                    except Exception as e:
                        print(f"Error reading page {page_num + 1}: {e}")
                        continue
                
                return text
                
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def split_text_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks suitable for OpenAI processing"""
        # Try to split at sentence boundaries or line breaks
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def save_entries_to_json(self, entries: List[Dict[str, Any]], output_path: str):
        """Save extracted entries to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(entries)} entries to {output_path}")
        except Exception as e:
            print(f"Error saving JSON: {e}")
    
    async def insert_entries_to_database(self, entries: List[Dict[str, Any]]) -> int:
        """Insert/update entries in the database using existing schema"""
        
        if not entries:
            print("No entries to insert")
            return 0
        
        # Connect to database with proper encoding
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Set text factory to handle UTF-8 properly on Windows
        conn.text_factory = str
        inserted_count = 0
        updated_count = 0
        
        try:
            for entry in entries:
                lemma = entry.get('lemma', '').strip()
                if not lemma:
                    continue
                
                # Check if word already exists
                cursor.execute(
                    "SELECT id, pos, ipa FROM word_lemmas WHERE LOWER(lemma) = LOWER(?)", 
                    (lemma,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    lemma_id = existing[0]
                    existing_pos = existing[1]
                    existing_ipa = existing[2]
                    
                    # Update existing entry with better information
                    pos = self.normalize_pos(entry.get('pos', ''))
                    ipa = entry.get('ipa')
                    
                    update_needed = False
                    
                    # Update POS if current is generic or missing
                    if not existing_pos or existing_pos in ['other', ''] or pos != existing_pos:
                        cursor.execute(
                            "UPDATE word_lemmas SET pos = ? WHERE id = ?",
                            (pos, lemma_id)
                        )
                        update_needed = True
                        print(f"  Updated POS for {lemma}: {existing_pos} -> {pos}")
                    
                    # Update IPA if missing
                    if not existing_ipa and ipa:
                        try:
                            cursor.execute(
                                "UPDATE word_lemmas SET ipa = ? WHERE id = ?",
                                (ipa, lemma_id)
                            )
                            update_needed = True
                            print(f"  Added IPA for {lemma}: {ipa}")
                        except Exception as ipa_error:
                            print(f"  Warning: Could not add IPA for {lemma}: {ipa_error}")
                            # Continue without IPA
                    
                    # Check existing translations
                    cursor.execute(
                        "SELECT text FROM translations WHERE lemma_id = ? AND lang_code = 'en'",
                        (lemma_id,)
                    )
                    existing_translations = [row[0] for row in cursor.fetchall()]
                    
                    # Add new translations that don't exist
                    new_translations = entry.get('translations', [])
                    for translation in new_translations:
                        if translation and translation.strip() and translation.strip() not in existing_translations:
                            cursor.execute("""
                                INSERT INTO translations (lemma_id, lang_code, text, source)
                                VALUES (?, ?, ?, ?)
                            """, (lemma_id, 'en', translation.strip(), 'collins_dictionary'))
                            update_needed = True
                            print(f"  Added translation for {lemma}: {translation}")
                    
                    # Update gender information for nouns if missing
                    if pos == 'noun' and entry.get('gender'):
                        cursor.execute(
                            "SELECT COUNT(*) FROM word_forms WHERE lemma_id = ? AND feature_key = 'article'",
                            (lemma_id,)
                        )
                        if cursor.fetchone()[0] == 0:  # No article info exists
                            gender = entry['gender'].lower()
                            if gender in ['m', 'f', 'n']:
                                article = {'m': 'der', 'f': 'die', 'n': 'das'}[gender]
                                cursor.execute("""
                                    INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                                    VALUES (?, ?, ?, ?)
                                """, (lemma_id, article, 'article', 'article'))
                                update_needed = True
                                print(f"  Added article for {lemma}: {article}")
                    
                    if update_needed:
                        updated_count += 1
                    else:
                        print(f"  No updates needed for: {lemma}")
                    
                    continue
                
                # Insert WordLemma
                pos = self.normalize_pos(entry.get('pos', ''))
                ipa = entry.get('ipa')
                
                # Handle IPA encoding issues
                try:
                    cursor.execute("""
                        INSERT INTO word_lemmas (lemma, pos, ipa, cefr, notes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        lemma,
                        pos,
                        ipa,
                        'A1',  # Default CEFR level
                        'Imported from Collins Dictionary',
                        datetime.now().isoformat()
                    ))
                except Exception as insert_error:
                    # Try without IPA if encoding fails
                    print(f"  Warning: IPA encoding issue for {lemma}, inserting without IPA")
                    cursor.execute("""
                        INSERT INTO word_lemmas (lemma, pos, cefr, notes, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        lemma,
                        pos,
                        'A1',
                        'Imported from Collins Dictionary',
                        datetime.now().isoformat()
                    ))
                
                lemma_id = cursor.lastrowid
                
                # Insert translations
                translations = entry.get('translations', [])
                for translation in translations:
                    if translation and translation.strip():
                        cursor.execute("""
                            INSERT INTO translations (lemma_id, lang_code, text, source)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, 'en', translation.strip(), 'collins_dictionary'))
                
                # Insert examples if available
                examples = entry.get('examples', [])
                for example in examples:
                    if isinstance(example, dict) and example.get('de') and example.get('en'):
                        cursor.execute("""
                            INSERT INTO examples (lemma_id, de_text, en_text, level)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, example['de'], example['en'], 'A1'))
                
                # Insert gender information for nouns as WordForm
                if pos == 'noun' and entry.get('gender'):
                    gender = entry['gender'].lower()
                    if gender in ['m', 'f', 'n']:
                        article = {'m': 'der', 'f': 'die', 'n': 'das'}[gender]
                        cursor.execute("""
                            INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, article, 'article', 'article'))
                
                inserted_count += 1
                print(f"  Inserted: {lemma} ({pos})")
            
            conn.commit()
            print(f"Database operation complete:")
            print(f"  - New entries inserted: {inserted_count}")
            print(f"  - Existing entries updated: {updated_count}")
            
        except Exception as e:
            print(f"Database error: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return inserted_count + updated_count


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract German dictionary entries from Collins PDF')
    parser.add_argument('pdf_file', help='Path to Collins German Dictionary PDF')
    parser.add_argument('--output-json', help='Save extracted entries to JSON file')
    parser.add_argument('--no-database', action='store_true', help='Skip database insertion')
    parser.add_argument('--chunk-size', type=int, default=3000, help='Text chunk size for processing')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_file):
        print(f"File not found: {args.pdf_file}")
        return
    
    print("Collins German Dictionary Extractor")
    print("=" * 50)
    
    extractor = GermanDictionaryExtractor()
    
    # Extract entries from PDF
    entries = await extractor.process_pdf_in_chunks(args.pdf_file, args.chunk_size)
    
    if not entries:
        print("No dictionary entries found")
        return
    
    # Save to JSON if requested
    if args.output_json:
        extractor.save_entries_to_json(entries, args.output_json)
    
    # Insert to database unless disabled
    if not args.no_database:
        print("\nProcessing entries in database...")
        processed = await extractor.insert_entries_to_database(entries)
        print(f"Database processing complete: {processed} entries processed")
    
    print(f"\nExtraction summary:")
    print(f"Total entries found: {len(entries)}")
    
    # Show sample entries
    if entries:
        print(f"\nSample entries:")
        for entry in entries[:3]:
            print(f"  {entry.get('lemma', 'N/A')} ({entry.get('pos', 'N/A')}): {', '.join(entry.get('translations', [])[:3])}")


if __name__ == "__main__":
    asyncio.run(main())