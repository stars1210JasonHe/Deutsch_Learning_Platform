#!/usr/bin/env python3
"""
Quick Collins Test - Fast test with minimal OpenAI calls
Just extract a few words to verify the pipeline works
"""
import asyncio
import sys
import os
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env")
sys.path.append(os.getcwd())

try:
    from PyPDF2 import PdfReader
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "PyPDF2"], check=True)
    from PyPDF2 import PdfReader

from app.services.openai_service import OpenAIService


async def quick_test(pdf_file: str):
    """Quick test of Collins processing pipeline"""
    
    print("=== Quick Collins Test ===")
    print(f"PDF: {os.path.basename(pdf_file)}")
    
    # Step 1: Read PDF
    print("\n1. Reading PDF...")
    try:
        reader = PdfReader(pdf_file)
        print(f"✓ Pages: {len(reader.pages)}")
        
        # Get first page text
        text = reader.pages[0].extract_text()[:1000]  # First 1000 chars only
        print(f"✓ Extracted {len(text)} characters from first page")
        
    except Exception as e:
        print(f"✗ PDF reading failed: {e}")
        return
    
    # Step 2: Test OpenAI extraction (minimal)
    print("\n2. Testing OpenAI extraction...")
    try:
        openai_service = OpenAIService()
        
        system_prompt = """Extract 1-2 German words from this Collins dictionary text.
For each word return: lemma, pos, gender (for nouns), and 1-2 English translations.
Return JSON: {"entries": [{"lemma": "word", "pos": "noun", "gender": "f", "translations": ["translation1"]}]}"""
        
        response = await openai_service.client.chat.completions.create(
            model=openai_service.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract words from: {text[:500]}"}
            ],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        entries = result.get('entries', [])
        print(f"✓ Extracted {len(entries)} words:")
        
        for entry in entries:
            lemma = entry.get('lemma', 'unknown')
            pos = entry.get('pos', 'unknown')
            gender = entry.get('gender', '')
            translations = entry.get('translations', [])
            print(f"  - {lemma} ({pos}{' ' + gender if gender else ''}) → {', '.join(translations[:2])}")
        
    except Exception as e:
        print(f"✗ OpenAI extraction failed: {e}")
        return
    
    # Step 3: Test database insertion
    print("\n3. Testing database insertion...")
    try:
        conn = sqlite3.connect('data/app.db')
        cursor = conn.cursor()
        
        saved_count = 0
        for entry in entries:
            lemma = entry.get('lemma', '').strip()
            if not lemma:
                continue
                
            # Simple insertion
            cursor.execute("""
                INSERT OR REPLACE INTO word_lemmas (lemma, pos, notes, created_at)
                VALUES (?, ?, ?, ?)
            """, (lemma, entry.get('pos', 'other'), 'Quick Collins Test', datetime.now().isoformat()))
            
            lemma_id = cursor.lastrowid
            
            # Add article for nouns
            if entry.get('pos') == 'noun' and entry.get('gender'):
                gender = entry.get('gender')
                if gender in ['m', 'f', 'nt']:
                    article = {'m': 'der', 'f': 'die', 'nt': 'das'}[gender]
                    cursor.execute("""
                        INSERT OR REPLACE INTO word_forms (lemma_id, form, feature_key, feature_value)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, article, 'article', 'article'))
            
            # Add translations
            for translation in entry.get('translations', [])[:2]:
                if translation:
                    cursor.execute("""
                        INSERT OR REPLACE INTO translations (lemma_id, lang_code, text, source)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, 'en', translation, 'quick_test'))
            
            saved_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✓ Saved {saved_count} words to database")
        
    except Exception as e:
        print(f"✗ Database insertion failed: {e}")
        return
    
    # Step 4: Test word lookup via API
    print("\n4. Testing word lookup...")
    if entries:
        test_word = entries[0].get('lemma', '')
        if test_word:
            print(f"Testing lookup for '{test_word}'...")
            # This would require the API to be running, so just show the word
            print(f"✓ Word '{test_word}' ready for testing in UI")
    
    print("\n=== Quick Test Complete ===")
    print("✓ PDF reading works")
    print("✓ OpenAI extraction works") 
    print("✓ Database insertion works")
    print("✓ Ready for full processing!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick Collins test')
    parser.add_argument('pdf_file', help='Path to Collins PDF file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_file):
        print(f"Error: PDF file not found: {args.pdf_file}")
        exit(1)
    
    asyncio.run(quick_test(args.pdf_file))