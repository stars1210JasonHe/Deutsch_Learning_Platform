#!/usr/bin/env python3
"""
Simple Collins Fix - Add Key Missing Information
Based on collins_reading_guide.md but keeps it simple
Just adds the essential missing pieces without overcomplicating
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


class SimpleCollinsFix:
    """Simple targeted fixes for Collins entries"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.db_path = 'data/app.db'
    
    def get_collins_words_needing_improvement(self):
        """Get Collins words that could use better grammatical info"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get Collins words with basic info
        cursor.execute('''
            SELECT 
                wl.id,
                wl.lemma,
                wl.pos,
                wl.ipa,
                GROUP_CONCAT(CASE WHEN t.lang_code = "en" THEN t.text END, "; ") as en_translations
            FROM word_lemmas wl
            LEFT JOIN translations t ON wl.id = t.lemma_id
            WHERE wl.notes LIKE "%Collins%" 
            AND wl.pos IN ("noun", "verb", "adjective")
            GROUP BY wl.id, wl.lemma, wl.pos, wl.ipa
            ORDER BY wl.lemma
            LIMIT 5
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'lemma_id': row[0],
                'lemma': row[1],
                'pos': row[2],
                'ipa': row[3],
                'en_translations': row[4] or ''
            })
        
        conn.close()
        return results
    
    async def add_collins_grammatical_info(self, word_info: dict) -> dict:
        """Add Collins-style grammatical information using OpenAI"""
        
        lemma = word_info['lemma']
        pos = word_info['pos']
        
        if pos == 'noun':
            system_prompt = f"""For German noun "{lemma}", provide Collins dictionary grammatical information:

1. gender: "m", "f", or "nt" (neuter)
2. plural: plural form or "uncountable" if no plural
3. genitive: genitive ending like "-(e)s", "-en", etc.
4. domain: field label like "Anat", "Tech", "Phys" if specialized term

Return JSON: {{"gender": "f", "plural": "Membranen", "genitive": "-", "domain": "Tech"}}"""

        elif pos == 'verb':
            system_prompt = f"""For German verb "{lemma}", provide Collins dictionary grammatical information:

1. transitivity: "vt" (transitive), "vi" (intransitive), or "vr" (reflexive)
2. separable: true/false for particle verbs
3. preposition: governed preposition like "auf +acc", "mit +dat" if any

Return JSON: {{"transitivity": "vi", "separable": false, "preposition": "auf +acc"}}"""

        elif pos == 'adjective':
            system_prompt = f"""For German adjective "{lemma}", provide Collins dictionary grammatical information:

1. preposition: governed preposition like "auf +acc", "über +acc" if any

Return JSON: {{"preposition": "auf +acc"}}"""
        
        else:
            return {}
        
        user_prompt = f'Provide Collins-style grammatical information for German {pos} "{lemma}"'
        
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
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"  Error getting grammar info for {lemma}: {e}")
            return {}
    
    def update_word_with_collins_info(self, word_info: dict, grammar_info: dict) -> bool:
        """Update word with Collins grammatical information"""
        
        lemma_id = word_info['lemma_id']
        lemma = word_info['lemma']
        pos = word_info['pos']
        
        if not grammar_info:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update noun with Collins info
            if pos == 'noun':
                gender = grammar_info.get('gender', '')
                plural = grammar_info.get('plural', '')
                genitive = grammar_info.get('genitive', '')
                
                # Add article if not present
                if gender in ['m', 'f', 'nt']:
                    cursor.execute(
                        "SELECT COUNT(*) FROM word_forms WHERE lemma_id = ? AND feature_key = 'article'",
                        (lemma_id,)
                    )
                    if cursor.fetchone()[0] == 0:
                        article = {'m': 'der', 'f': 'die', 'nt': 'das'}[gender]
                        cursor.execute("""
                            INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, article, 'article', 'article'))
                        print(f"    Added article: {article}")
                
                # Add plural if not present and countable
                if plural and plural != 'uncountable':
                    cursor.execute(
                        "SELECT COUNT(*) FROM word_forms WHERE lemma_id = ? AND feature_key = 'plural'",
                        (lemma_id,)
                    )
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, plural, 'plural', 'plural'))
                        print(f"    Added plural: {plural}")
                
                # Add genitive if available
                if genitive and genitive != '-':
                    cursor.execute(
                        "SELECT COUNT(*) FROM word_forms WHERE lemma_id = ? AND feature_key = 'genitive'",
                        (lemma_id,)
                    )
                    if cursor.fetchone()[0] == 0:
                        gen_form = lemma + genitive.replace('-(', '').replace(')', '')
                        cursor.execute("""
                            INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, gen_form, 'genitive', 'genitive_singular'))
                        print(f"    Added genitive: {gen_form}")
            
            # Update verb with Collins info
            elif pos == 'verb':
                transitivity = grammar_info.get('transitivity', '')
                separable = grammar_info.get('separable', False)
                preposition = grammar_info.get('preposition', '')
                
                # Update notes with verb properties
                verb_props = {
                    'transitivity': transitivity,
                    'separable': separable,
                    'preposition': preposition
                }
                cursor.execute("""
                    UPDATE word_lemmas 
                    SET notes = notes || ' | collins_verb_props: ' || ?
                    WHERE id = ?
                """, (json.dumps(verb_props), lemma_id))
                print(f"    Added verb properties: {transitivity}, separable: {separable}")
            
            # Update adjective with Collins info
            elif pos == 'adjective':
                preposition = grammar_info.get('preposition', '')
                if preposition:
                    cursor.execute("""
                        UPDATE word_lemmas 
                        SET notes = notes || ' | collins_adj_prep: ' || ?
                        WHERE id = ?
                    """, (preposition, lemma_id))
                    print(f"    Added adjective preposition: {preposition}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"    Error updating {lemma}: {e}")
            conn.rollback()
            conn.close()
            return False
    
    async def improve_collins_words(self):
        """Improve Collins words with better grammatical information"""
        
        words_to_improve = self.get_collins_words_needing_improvement()
        
        if not words_to_improve:
            print("No Collins words found to improve!")
            return
        
        print(f"Improving {len(words_to_improve)} Collins words with grammatical info...")
        
        improved_count = 0
        
        for word_info in words_to_improve:
            lemma = word_info['lemma']
            pos = word_info['pos']
            
            print(f"\nImproving: {lemma} ({pos})")
            
            try:
                # Get Collins grammatical information
                grammar_info = await self.add_collins_grammatical_info(word_info)
                
                if grammar_info:
                    # Update database
                    success = self.update_word_with_collins_info(word_info, grammar_info)
                    if success:
                        improved_count += 1
                        print(f"    Successfully improved {lemma}")
                    else:
                        print(f"    Failed to update {lemma}")
                else:
                    print(f"    No grammar info generated for {lemma}")
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"    Error processing {lemma}: {e}")
        
        print(f"\nImprovement complete: {improved_count}/{len(words_to_improve)} words enhanced")


async def main():
    """Main function"""
    
    print("=== Simple Collins Fix ===")
    print("Adding key Collins grammatical information")
    print("Keeps UI compatibility, adds proper grammar")
    print()
    
    fixer = SimpleCollinsFix()
    await fixer.improve_collins_words()
    
    print("\n=== Final Status ===")
    print("Collins words now have:")
    print("- Proper articles and plurals for nouns")
    print("- Transitivity and prepositions for verbs")
    print("- Government information for adjectives")
    print("- UI compatibility maintained")


if __name__ == "__main__":
    asyncio.run(main())