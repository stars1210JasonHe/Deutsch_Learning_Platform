#!/usr/bin/env python3
"""
Fix missing/incorrect plural forms for Collins nouns
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


class CollinsPluralFixer:
    """Fix plural forms for Collins nouns"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_path = 'data/app.db'
    
    def get_nouns_needing_plural_fix(self):
        """Get Collins nouns that need plural fixes"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                wl.id,
                wl.lemma,
                GROUP_CONCAT(CASE WHEN wf.feature_key = 'article' THEN wf.form END) as article,
                GROUP_CONCAT(CASE WHEN wf.feature_key = 'plural' THEN wf.form END) as plural
            FROM word_lemmas wl
            LEFT JOIN word_forms wf ON wl.id = wf.lemma_id
            WHERE wl.notes LIKE '%Collins%' AND wl.pos = 'noun'
            GROUP BY wl.id, wl.lemma
            HAVING plural IS NULL OR plural = 'die Unsinn'
            ORDER BY wl.lemma
        ''')
        
        results = []
        for row in cursor.fetchall():
            lemma_id, lemma, article, plural = row
            results.append({
                'lemma_id': lemma_id,
                'lemma': lemma,
                'article': article,
                'current_plural': plural
            })
        
        conn.close()
        return results
    
    async def generate_correct_plural(self, lemma: str, article: str) -> str:
        """Generate correct plural form using OpenAI"""
        
        system_prompt = f"""You are a German grammar expert. For the German noun "{lemma}" with article "{article}", provide the correct plural form.

Rules:
1. If the noun is uncountable (like "Rudern", "Mondschein"), return "no plural"
2. If the noun is already plural (like "Ferien"), return the same form
3. Otherwise, provide the standard German plural form

Examples:
- der Hund -> Hunde
- das Haus -> Häuser  
- die Katze -> Katzen
- der Mondschein -> no plural (uncountable)
- das Rudern -> no plural (gerund/activity)

Return only the plural form or "no plural"."""

        user_prompt = f'What is the correct plural form of "{article} {lemma}"?'

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
            print(f"    Error generating plural for {lemma}: {e}")
            return None
    
    def update_noun_plural(self, lemma_id: int, lemma: str, new_plural: str) -> bool:
        """Update the plural form in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Remove existing incorrect plural
            cursor.execute(
                "DELETE FROM word_forms WHERE lemma_id = ? AND feature_key = 'plural'",
                (lemma_id,)
            )
            
            # Add correct plural if not "no plural"
            if new_plural and new_plural != "no plural":
                cursor.execute("""
                    INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                    VALUES (?, ?, ?, ?)
                """, (lemma_id, new_plural, 'plural', 'plural'))
                
                print(f"  ✓ {lemma}: plural = {new_plural}")
            else:
                print(f"  ✓ {lemma}: no plural (uncountable)")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"  ✗ Error updating {lemma}: {e}")
            conn.rollback()
            conn.close()
            return False
    
    async def fix_all_collins_plurals(self):
        """Fix all Collins nouns with missing/incorrect plurals"""
        
        nouns_to_fix = self.get_nouns_needing_plural_fix()
        
        if not nouns_to_fix:
            print("All Collins nouns have correct plurals!")
            return
        
        print(f"Found {len(nouns_to_fix)} nouns needing plural fixes:")
        
        for noun in nouns_to_fix:
            lemma = noun['lemma']
            article = noun['article'] or ''
            current = noun['current_plural'] or 'MISSING'
            
            print(f"\nFixing: {article} {lemma} (current plural: {current})")
            
            try:
                # Generate correct plural
                correct_plural = await self.generate_correct_plural(lemma, article)
                
                if correct_plural:
                    # Update in database
                    success = self.update_noun_plural(
                        noun['lemma_id'], 
                        lemma, 
                        correct_plural
                    )
                    
                    if not success:
                        print(f"  Failed to update {lemma}")
                else:
                    print(f"  Could not generate plural for {lemma}")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"  Error processing {lemma}: {e}")


async def main():
    """Main function"""
    
    print("=== Collins Plural Forms Fixer ===")
    print()
    
    fixer = CollinsPluralFixer()
    await fixer.fix_all_collins_plurals()
    
    print("\n=== Verification ===")
    
    # Verify results
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            wl.lemma,
            GROUP_CONCAT(CASE WHEN wf.feature_key = 'article' THEN wf.form END) as article,
            GROUP_CONCAT(CASE WHEN wf.feature_key = 'plural' THEN wf.form END) as plural
        FROM word_lemmas wl
        LEFT JOIN word_forms wf ON wl.id = wf.lemma_id
        WHERE wl.notes LIKE '%Collins%' AND wl.pos = 'noun'
        GROUP BY wl.id, wl.lemma
        ORDER BY wl.lemma
    ''')
    
    print("Final Collins noun data:")
    for row in cursor.fetchall():
        lemma, article, plural = row
        try:
            plural_display = plural if plural else 'no plural'
            print(f"  {article or '?'} {lemma} -> {plural_display}")
        except UnicodeEncodeError:
            plural_display = 'present' if plural else 'no plural'
            print(f"  [noun] -> {plural_display}")
    
    conn.close()


if __name__ == "__main__":
    asyncio.run(main())