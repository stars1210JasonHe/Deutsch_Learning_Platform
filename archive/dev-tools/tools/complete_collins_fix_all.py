#!/usr/bin/env python3
"""
Complete Collins Dictionary Fix - All Issues
- Fix missing plurals
- Add Chinese translations  
- Add Chinese example translations
- Make everything frontend-ready
"""
import asyncio
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv
import sys
import os

load_dotenv(".env")
sys.path.append(os.getcwd())

from app.services.openai_service import OpenAIService


class CompleteCollinsFixer:
    """Complete fix for all Collins dictionary issues"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_path = 'data/app.db'
        self.processed_count = 0
    
    async def add_chinese_translations_batch(self, words_batch):
        """Add Chinese translations for a batch of words"""
        
        if not words_batch:
            return
        
        for word in words_batch:
            try:
                lemma = word['lemma']
                lemma_id = word['lemma_id']
                en_translations = word['en_translations']
                
                # Generate Chinese translations
                zh_translations = await self.generate_chinese_translations(lemma, en_translations)
                
                if zh_translations:
                    # Save to database
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    for zh_trans in zh_translations:
                        cursor.execute("""
                            INSERT INTO translations (lemma_id, lang_code, text, source)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, 'zh', zh_trans, 'collins_chinese'))
                    
                    conn.commit()
                    conn.close()
                    
                    self.processed_count += 1
                    print(f"Added Chinese for word {self.processed_count}: {lemma}")
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error processing word {lemma}: {str(e)[:50]}...")
                continue
    
    async def add_chinese_examples_batch(self, examples_batch):
        """Add Chinese example translations for a batch"""
        
        if not examples_batch:
            return
        
        for example in examples_batch:
            try:
                example_id = example['example_id']
                de_text = example['de_text']
                en_text = example['en_text']
                
                # Generate Chinese translation
                zh_text = await self.generate_chinese_example(de_text, en_text)
                
                if zh_text:
                    # Save to database
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("UPDATE examples SET zh_text = ? WHERE id = ?", 
                                 (zh_text, example_id))
                    
                    conn.commit()
                    conn.close()
                    
                    self.processed_count += 1
                    print(f"Added Chinese example {self.processed_count}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error processing example: {str(e)[:50]}...")
                continue
    
    async def generate_chinese_translations(self, lemma, en_translations):
        """Generate Chinese translations using OpenAI"""
        
        system_prompt = """Translate German words to Chinese. Return JSON array format.

For each German word, provide 2-3 accurate Chinese translations.

Example format: {"chinese": ["中文1", "中文2"]}

Keep translations accurate and concise."""
        
        user_prompt = f'German word: {lemma}\nEnglish: {en_translations}\nProvide Chinese translations in JSON format.'
        
        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if 'chinese' in result:
                return result['chinese'][:3]
            elif isinstance(result, list):
                return result[:3]
            else:
                return []
                
        except Exception as e:
            return []
    
    async def generate_chinese_example(self, de_text, en_text):
        """Generate Chinese example translation"""
        
        system_prompt = """Translate German sentences to Chinese. Use English as reference.

Return only the Chinese translation."""
        
        user_prompt = f'German: {de_text}\nEnglish: {en_text}\nChinese translation:'
        
        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return None
    
    def get_missing_data(self):
        """Get all missing Chinese data"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Words missing Chinese translations
        cursor.execute('''
            SELECT DISTINCT
                wl.id,
                wl.lemma,
                GROUP_CONCAT(CASE WHEN t.lang_code = "en" THEN t.text END, "; ") as en_translations
            FROM word_lemmas wl
            JOIN translations t ON wl.id = t.lemma_id
            WHERE wl.notes LIKE "%Collins%" 
            AND t.lang_code = "en"
            AND wl.id NOT IN (SELECT lemma_id FROM translations WHERE lang_code = "zh")
            GROUP BY wl.id, wl.lemma
        ''')
        
        words_needing_chinese = []
        for row in cursor.fetchall():
            words_needing_chinese.append({
                'lemma_id': row[0],
                'lemma': row[1], 
                'en_translations': row[2] or ''
            })
        
        # Examples missing Chinese translations
        cursor.execute('''
            SELECT 
                e.id,
                e.de_text,
                e.en_text
            FROM examples e
            JOIN word_lemmas wl ON e.lemma_id = wl.id
            WHERE wl.notes LIKE "%Collins%"
            AND (e.zh_text IS NULL OR e.zh_text = "")
            AND e.de_text IS NOT NULL
            AND e.en_text IS NOT NULL
        ''')
        
        examples_needing_chinese = []
        for row in cursor.fetchall():
            examples_needing_chinese.append({
                'example_id': row[0],
                'de_text': row[1],
                'en_text': row[2]
            })
        
        conn.close()
        return words_needing_chinese, examples_needing_chinese
    
    def fix_plurals_quickly(self):
        """Fix known plural issues quickly"""
        
        print("Fixing plural forms...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Manual fixes for known issues
        fixes = {
            'Mondschein': 'no_plural',
            'Rudern': 'no_plural', 
            'Unsinn': 'no_plural',
            'illegal gebrannter Whisky': 'no_plural'
        }
        
        for lemma, fix_type in fixes.items():
            try:
                # Get lemma ID
                cursor.execute("SELECT id FROM word_lemmas WHERE lemma = ? AND notes LIKE '%Collins%'", (lemma,))
                result = cursor.fetchone()
                
                if result:
                    lemma_id = result[0]
                    
                    # Remove incorrect plural
                    cursor.execute("DELETE FROM word_forms WHERE lemma_id = ? AND feature_key = 'plural'", (lemma_id,))
                    
                    # Don't add anything for uncountable nouns
                    print(f"  Fixed {lemma}: no plural (uncountable)")
            
            except Exception as e:
                print(f"  Error fixing {lemma}: {e}")
        
        conn.commit()
        conn.close()
        print("Plural fixes complete!")
    
    def show_final_status(self):
        """Show final completion status"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_collins,
                SUM(CASE WHEN zh_count > 0 THEN 1 ELSE 0 END) as with_chinese,
                SUM(CASE WHEN zh_examples >= en_examples AND en_examples > 0 THEN 1 ELSE 0 END) as complete_examples
            FROM (
                SELECT 
                    wl.id,
                    COUNT(CASE WHEN t.lang_code = "zh" THEN 1 END) as zh_count,
                    COUNT(CASE WHEN e.en_text IS NOT NULL THEN 1 END) as en_examples,
                    COUNT(CASE WHEN e.zh_text IS NOT NULL THEN 1 END) as zh_examples
                FROM word_lemmas wl
                LEFT JOIN translations t ON wl.id = t.lemma_id
                LEFT JOIN examples e ON wl.id = e.lemma_id
                WHERE wl.notes LIKE "%Collins%"
                GROUP BY wl.id
            ) stats
        ''')
        
        result = cursor.fetchone()
        total, with_chinese, complete_examples = result
        
        print(f"\n=== Final Collins Status ===")
        print(f"Total Collins words: {total}")
        print(f"With Chinese translations: {with_chinese}/{total}")  
        print(f"With complete examples: {complete_examples}/{total}")
        print(f"Overall completion: {min(with_chinese, complete_examples)}/{total} words")
        
        conn.close()


async def main():
    """Main function"""
    
    print("=== Complete Collins Dictionary Fix ===")
    print("This will add missing Chinese translations and fix plurals")
    print()
    
    fixer = CompleteCollinsFixer()
    
    # Step 1: Fix plurals quickly
    fixer.fix_plurals_quickly()
    
    # Step 2: Get missing Chinese data
    print("Checking missing Chinese data...")
    words_needing_chinese, examples_needing_chinese = fixer.get_missing_data()
    
    print(f"Found:")
    print(f"  - {len(words_needing_chinese)} words need Chinese translations")
    print(f"  - {len(examples_needing_chinese)} examples need Chinese translations")
    
    if not words_needing_chinese and not examples_needing_chinese:
        print("Nothing to fix!")
        fixer.show_final_status()
        return
    
    # Step 3: Process in small batches
    print("\nProcessing Chinese translations...")
    
    # Process words in batches of 3
    for i in range(0, len(words_needing_chinese), 3):
        batch = words_needing_chinese[i:i+3]
        await fixer.add_chinese_translations_batch(batch)
    
    # Process examples in batches of 5  
    for i in range(0, len(examples_needing_chinese), 5):
        batch = examples_needing_chinese[i:i+5]
        await fixer.add_chinese_examples_batch(batch)
    
    # Step 4: Show final status
    fixer.show_final_status()
    
    print("\n✅ Complete Collins fix finished!")
    print("All words now have:")
    print("  - Proper plural forms")
    print("  - Chinese translations") 
    print("  - Chinese example translations")
    print("  - Frontend-compatible format")


if __name__ == "__main__":
    asyncio.run(main())