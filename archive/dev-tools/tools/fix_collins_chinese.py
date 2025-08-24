#!/usr/bin/env python3
"""
Fix missing Chinese translations and example translations for Collins words
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


class CollinsChineseFixer:
    """Add missing Chinese translations for Collins words"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_path = 'data/app.db'
    
    def get_words_needing_chinese(self):
        """Get Collins words missing Chinese translations"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get words with English but missing Chinese translations
        cursor.execute('''
            SELECT 
                wl.id,
                wl.lemma,
                wl.pos,
                GROUP_CONCAT(CASE WHEN t.lang_code = "en" THEN t.text END, "; ") as en_translations
            FROM word_lemmas wl
            LEFT JOIN translations t ON wl.id = t.lemma_id
            WHERE wl.notes LIKE "%Collins%" 
            AND wl.id NOT IN (
                SELECT DISTINCT lemma_id 
                FROM translations 
                WHERE lang_code = "zh"
            )
            GROUP BY wl.id, wl.lemma, wl.pos
            HAVING en_translations IS NOT NULL
            ORDER BY wl.lemma
        ''')
        
        results = []
        for row in cursor.fetchall():
            lemma_id, lemma, pos, en_translations = row
            results.append({
                'lemma_id': lemma_id,
                'lemma': lemma,
                'pos': pos,
                'en_translations': en_translations or ''
            })
        
        conn.close()
        return results
    
    def get_examples_needing_chinese(self):
        """Get examples missing Chinese translations"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                e.id,
                wl.lemma,
                e.de_text,
                e.en_text
            FROM examples e
            JOIN word_lemmas wl ON e.lemma_id = wl.id
            WHERE wl.notes LIKE "%Collins%"
            AND (e.zh_text IS NULL OR e.zh_text = "")
            AND e.de_text IS NOT NULL
            AND e.en_text IS NOT NULL
            ORDER BY wl.lemma
        ''')
        
        results = []
        for row in cursor.fetchall():
            example_id, lemma, de_text, en_text = row
            results.append({
                'example_id': example_id,
                'lemma': lemma,
                'de_text': de_text,
                'en_text': en_text
            })
        
        conn.close()
        return results
    
    async def generate_chinese_translations(self, lemma: str, pos: str, en_translations: str) -> list:
        """Generate Chinese translations using OpenAI"""
        
        system_prompt = f"""You are a German-Chinese translation expert. Translate German words to Chinese.

For the German {pos} "{lemma}" with English meanings: {en_translations}

Provide 2-3 accurate Chinese translations that match the English meanings.

Return only a JSON array of Chinese translations:
["中文翻译1", "中文翻译2", "中文翻译3"]

Keep translations concise and accurate."""

        user_prompt = f'Translate German {pos} "{lemma}" to Chinese. English meanings: {en_translations}'

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
            
            # Handle different response formats
            if isinstance(result, list):
                return result[:3]
            elif isinstance(result, dict):
                if 'translations' in result:
                    return result['translations'][:3]
                elif 'chinese' in result:
                    return result['chinese'][:3]
                else:
                    # Try to get first array value
                    for value in result.values():
                        if isinstance(value, list):
                            return value[:3]
            
            return []
            
        except Exception as e:
            print(f"    Error generating Chinese for {lemma}: {e}")
            return []
    
    async def generate_chinese_example_translation(self, de_text: str, en_text: str) -> str:
        """Generate Chinese translation for German example"""
        
        system_prompt = """You are a German-Chinese translation expert. 

Translate the German sentence to Chinese. Use the English translation as reference for meaning.

Return only the Chinese translation, nothing else."""

        user_prompt = f'Translate to Chinese:\nGerman: {de_text}\nEnglish reference: {en_text}'

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
            print(f"    Error translating example: {e}")
            return None
    
    def save_chinese_translations(self, lemma_id: int, lemma: str, zh_translations: list) -> bool:
        """Save Chinese translations to database"""
        
        if not zh_translations:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for zh_trans in zh_translations:
                if zh_trans and zh_trans.strip():
                    cursor.execute("""
                        INSERT INTO translations (lemma_id, lang_code, text, source)
                        VALUES (?, ?, ?, ?)
                    """, (lemma_id, 'zh', zh_trans.strip(), 'collins_chinese'))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"    Database error saving Chinese for {lemma}: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def save_chinese_example(self, example_id: int, zh_text: str) -> bool:
        """Save Chinese example translation"""
        
        if not zh_text:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE examples SET zh_text = ? WHERE id = ?
            """, (zh_text.strip(), example_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"    Database error saving example: {e}")
            conn.rollback()
            conn.close()
            return False
    
    async def fix_all_chinese_translations(self):
        """Fix all missing Chinese translations"""
        
        # Fix word translations
        words_to_fix = self.get_words_needing_chinese()
        print(f"Found {len(words_to_fix)} words needing Chinese translations")
        
        for word in words_to_fix:
            lemma = word['lemma']
            pos = word['pos']
            en_translations = word['en_translations']
            
            print(f"\nAdding Chinese for: {lemma} ({pos})")
            
            try:
                zh_translations = await self.generate_chinese_translations(
                    lemma, pos, en_translations
                )
                
                if zh_translations:
                    success = self.save_chinese_translations(
                        word['lemma_id'], lemma, zh_translations
                    )
                    
                    if success:
                        print(f"    ✓ Added: {', '.join(zh_translations)}")
                    else:
                        print(f"    ✗ Failed to save Chinese translations")
                else:
                    print(f"    ✗ Could not generate Chinese translations")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"    Error processing {lemma}: {e}")
        
        # Fix example translations  
        examples_to_fix = self.get_examples_needing_chinese()
        print(f"\nFound {len(examples_to_fix)} examples needing Chinese translations")
        
        for example in examples_to_fix:
            lemma = example['lemma']
            de_text = example['de_text']
            en_text = example['en_text']
            
            print(f"\nTranslating example for: {lemma}")
            print(f"    DE: {de_text[:50]}...")
            
            try:
                zh_text = await self.generate_chinese_example_translation(
                    de_text, en_text
                )
                
                if zh_text:
                    success = self.save_chinese_example(
                        example['example_id'], zh_text
                    )
                    
                    if success:
                        print(f"    ✓ ZH: {zh_text[:50]}...")
                    else:
                        print(f"    ✗ Failed to save Chinese example")
                else:
                    print(f"    ✗ Could not translate example")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"    Error translating example: {e}")


async def main():
    """Main function"""
    
    print("=== Collins Chinese Translations Fixer ===")
    print()
    
    fixer = CollinsChineseFixer()
    await fixer.fix_all_chinese_translations()
    
    print("\n=== Final Verification ===")
    
    # Verify results
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            wl.lemma,
            COUNT(CASE WHEN t.lang_code = "en" THEN 1 END) as en_count,
            COUNT(CASE WHEN t.lang_code = "zh" THEN 1 END) as zh_count,
            COUNT(CASE WHEN e.en_text IS NOT NULL THEN 1 END) as en_examples,
            COUNT(CASE WHEN e.zh_text IS NOT NULL THEN 1 END) as zh_examples
        FROM word_lemmas wl
        LEFT JOIN translations t ON wl.id = t.lemma_id
        LEFT JOIN examples e ON wl.id = e.lemma_id
        WHERE wl.notes LIKE "%Collins%"
        GROUP BY wl.id, wl.lemma
        ORDER BY wl.lemma
        LIMIT 10
    ''')
    
    print("Final translation status:")
    for row in cursor.fetchall():
        lemma, en_trans, zh_trans, en_examples, zh_examples = row
        try:
            status = "COMPLETE" if zh_trans > 0 and zh_examples >= en_examples else "INCOMPLETE"
            print(f"  {lemma}: {en_trans}EN/{zh_trans}ZH trans, {en_examples}EN/{zh_examples}ZH examples [{status}]")
        except UnicodeEncodeError:
            status = "COMPLETE" if zh_trans > 0 and zh_examples >= en_examples else "INCOMPLETE" 
            print(f"  [word]: {en_trans}EN/{zh_trans}ZH trans, {en_examples}EN/{zh_examples}ZH examples [{status}]")
    
    conn.close()


if __name__ == "__main__":
    asyncio.run(main())