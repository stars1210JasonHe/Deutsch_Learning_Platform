#!/usr/bin/env python3
"""
Word Deduplication Script
Analyzes and fixes duplicate word entries in the vocabulary database.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.models.word import WordLemma, Translation, Example, WordForm
from sqlalchemy import text, func
from typing import List, Dict, Tuple
import argparse
from datetime import datetime

class WordDeduplicator:
    def __init__(self, dry_run: bool = True):
        self.db = SessionLocal()
        self.dry_run = dry_run
        self.stats = {
            'exact_duplicates': 0,
            'similar_pairs': 0,
            'merged_words': 0,
            'deleted_words': 0,
            'preserved_words': 0
        }
    
    def analyze_duplicates(self):
        """Analyze the database for duplicate entries"""
        print("🔍 Analyzing word duplicates...")
        
        # 1. Check for exact lemma duplicates (case-insensitive)
        print("\n1. EXACT DUPLICATES:")
        exact_duplicates = self.find_exact_duplicates()
        
        if exact_duplicates:
            print(f"Found {len(exact_duplicates)} groups of exact duplicates:")
            for lemma, words in exact_duplicates.items():
                print(f"  📝 '{lemma}' - {len(words)} entries:")
                for word in words:
                    created = word.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(word, 'created_at') and word.created_at else 'Unknown'
                    print(f"    ID {word.id}: pos={word.pos}, cefr={word.cefr}, created={created}")
                    if word.notes:
                        print(f"      notes: {word.notes[:50]}...")
        else:
            print("  ✅ No exact duplicates found")
        
        # 2. Check for similar words
        print("\n2. SIMILAR WORDS (potential typos):")
        similar_pairs = self.find_similar_words()
        
        if similar_pairs:
            print(f"Found {len(similar_pairs)} pairs of similar words:")
            for (word1, word2, similarity) in similar_pairs[:10]:  # Show top 10
                print(f"  🔄 '{word1.lemma}' ↔ '{word2.lemma}' (similarity: {similarity:.2f})")
                print(f"    ID {word1.id} vs ID {word2.id}")
        else:
            print("  ✅ No similar words found")
        
        # 3. Statistics
        total_words = self.db.query(WordLemma).count()
        total_translations = self.db.query(Translation).count()
        total_examples = self.db.query(Example).count()
        
        print(f"\n3. DATABASE STATISTICS:")
        print(f"  Total words: {total_words}")
        print(f"  Total translations: {total_translations}")
        print(f"  Total examples: {total_examples}")
        
        self.stats['exact_duplicates'] = len(exact_duplicates)
        self.stats['similar_pairs'] = len(similar_pairs)
        
        return exact_duplicates, similar_pairs
    
    def find_exact_duplicates(self) -> Dict[str, List[WordLemma]]:
        """Find words with identical lemmas (case-insensitive)"""
        duplicates = {}
        
        # Get all words with duplicate lemmas
        duplicate_lemmas = self.db.execute(text('''
            SELECT LOWER(lemma) as lemma_lower, COUNT(*) as count 
            FROM word_lemmas 
            GROUP BY LOWER(lemma) 
            HAVING COUNT(*) > 1 
            ORDER BY count DESC
        ''')).fetchall()
        
        for lemma_lower, count in duplicate_lemmas:
            # Get all words with this lemma
            words = self.db.query(WordLemma).filter(
                func.lower(WordLemma.lemma) == lemma_lower
            ).all()
            
            if len(words) > 1:
                duplicates[lemma_lower] = words
        
        return duplicates
    
    def find_similar_words(self, similarity_threshold: float = 0.85) -> List[Tuple[WordLemma, WordLemma, float]]:
        """Find words that are similar (potential typos, excluding legitimate grammatical variations)"""
        similar_pairs = []
        
        # Get all words with length >= 4 to avoid short word false positives
        words = self.db.query(WordLemma).filter(
            func.length(WordLemma.lemma) >= 4
        ).order_by(WordLemma.lemma).all()
        
        checked = set()
        
        for i, word1 in enumerate(words):
            if word1.id in checked:
                continue
                
            for word2 in words[i+1:]:
                if word2.id in checked:
                    continue
                
                lemma1, lemma2 = word1.lemma.lower(), word2.lemma.lower()
                
                # Only check words of similar length
                if abs(len(lemma1) - len(lemma2)) <= 2:
                    # Skip obvious grammatical variations
                    if self.is_likely_grammatical_variation(lemma1, lemma2):
                        continue
                    
                    similarity = self.calculate_similarity(lemma1, lemma2)
                    
                    if similarity_threshold <= similarity < 1.0:  # Similar but not identical
                        similar_pairs.append((word1, word2, similarity))
        
        return sorted(similar_pairs, key=lambda x: x[2], reverse=True)
    
    def is_likely_grammatical_variation(self, word1: str, word2: str) -> bool:
        """Check if two words are likely grammatical variations rather than typos"""
        
        import re
        
        # Check common German plural patterns
        if word1.endswith('e') and word2 == word1 + 'n':  # Katze -> Katzen
            return True
        if word2.endswith('e') and word1 == word2 + 'n':
            return True
            
        if word1.endswith('el') and word2 == word1 + 'n':  # Kartoffel -> Kartoffeln
            return True
        if word2.endswith('el') and word1 == word2 + 'n':
            return True
        
        # Simple plural with -n ending
        if abs(len(word1) - len(word2)) == 1:
            longer = word1 if len(word1) > len(word2) else word2
            shorter = word2 if len(word1) > len(word2) else word1
            if longer == shorter + 'n':
                return True
        
        # Simple plural with -en ending  
        if abs(len(word1) - len(word2)) == 2:
            longer = word1 if len(word1) > len(word2) else word2
            shorter = word2 if len(word1) > len(word2) else word1
            if longer == shorter + 'en':
                return True
        
        # Roman numeral differences (Sekundarstufe I vs II)
        if re.search(r' I+$', word1) and re.search(r' I+$', word2):
            base1 = re.sub(r' I+$', '', word1)
            base2 = re.sub(r' I+$', '', word2)
            if base1 == base2:
                return True
            
        # Check for adjective endings
        if word1.endswith('e') and word2.endswith('er') and word1[:-1] == word2[:-2]:  # große -> großer
            return True
        if word2.endswith('e') and word1.endswith('er') and word2[:-1] == word1[:-2]:
            return True
            
        # Check for compound vs simple words (different meanings)
        if len(word1) > len(word2) * 1.5 or len(word2) > len(word1) * 1.5:
            # One word is significantly longer - likely compound vs simple
            return True
        
        return False
    
    def calculate_similarity(self, word1: str, word2: str) -> float:
        """Calculate similarity between two words using edit distance"""
        if word1 == word2:
            return 1.0
        
        # Levenshtein distance
        len1, len2 = len(word1), len(word2)
        
        if len1 == 0:
            return 0.0 if len2 > 0 else 1.0
        if len2 == 0:
            return 0.0
        
        # Create distance matrix
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j
        
        # Fill matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if word1[i-1] == word2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(
                        dp[i-1][j] + 1,     # deletion
                        dp[i][j-1] + 1,     # insertion
                        dp[i-1][j-1] + 1    # substitution
                    )
        
        edit_distance = dp[len1][len2]
        max_len = max(len1, len2)
        
        return 1.0 - (edit_distance / max_len) if max_len > 0 else 0.0
    
    def merge_duplicate_group(self, words: List[WordLemma]) -> WordLemma:
        """Merge a group of duplicate words, keeping the best one"""
        if len(words) <= 1:
            return words[0] if words else None
        
        # Choose the best word to keep (priority: newest, most complete data)
        best_word = self.choose_best_word(words)
        words_to_delete = [w for w in words if w.id != best_word.id]
        
        print(f"  🔄 Merging {len(words)} duplicates of '{best_word.lemma}'...")
        print(f"    Keeping: ID {best_word.id} (chosen as best)")
        
        # Merge data from other words
        for word_to_delete in words_to_delete:
            print(f"    Deleting: ID {word_to_delete.id}")
            
            # Move translations
            translations = self.db.query(Translation).filter(
                Translation.lemma_id == word_to_delete.id
            ).all()
            
            for translation in translations:
                # Check if this translation already exists for the best word
                existing = self.db.query(Translation).filter(
                    Translation.lemma_id == best_word.id,
                    Translation.lang_code == translation.lang_code,
                    func.lower(Translation.text) == func.lower(translation.text)
                ).first()
                
                if not existing:
                    translation.lemma_id = best_word.id
                    print(f"      Moved translation: {translation.text}")
                else:
                    print(f"      Skipped duplicate translation: {translation.text}")
            
            # Move examples
            examples = self.db.query(Example).filter(
                Example.lemma_id == word_to_delete.id
            ).all()
            
            for example in examples:
                # Check if similar example exists
                existing = self.db.query(Example).filter(
                    Example.lemma_id == best_word.id,
                    func.lower(Example.de_text) == func.lower(example.de_text)
                ).first()
                
                if not existing:
                    example.lemma_id = best_word.id
                    print(f"      Moved example: {example.de_text[:30]}...")
                else:
                    print(f"      Skipped duplicate example: {example.de_text[:30]}...")
            
            # Move word forms
            word_forms = self.db.query(WordForm).filter(
                WordForm.lemma_id == word_to_delete.id
            ).all()
            
            for form in word_forms:
                # Check if this form already exists
                existing = self.db.query(WordForm).filter(
                    WordForm.lemma_id == best_word.id,
                    func.lower(WordForm.form) == func.lower(form.form),
                    WordForm.feature_key == form.feature_key,
                    WordForm.feature_value == form.feature_value
                ).first()
                
                if not existing:
                    form.lemma_id = best_word.id
                    print(f"      Moved word form: {form.form}")
                else:
                    print(f"      Skipped duplicate form: {form.form}")
            
            # Delete the duplicate word
            if not self.dry_run:
                self.db.delete(word_to_delete)
                self.stats['deleted_words'] += 1
        
        self.stats['merged_words'] += 1
        return best_word
    
    def choose_best_word(self, words: List[WordLemma]) -> WordLemma:
        """Choose the best word from a group of duplicates"""
        if len(words) == 1:
            return words[0]
        
        # Scoring criteria:
        # 1. Has more translations
        # 2. Has more examples
        # 3. More recent (if has created_at)
        # 4. Better notes/cefr level
        
        scored_words = []
        
        for word in words:
            score = 0
            
            # Count translations
            translation_count = self.db.query(Translation).filter(
                Translation.lemma_id == word.id
            ).count()
            score += translation_count * 10
            
            # Count examples
            example_count = self.db.query(Example).filter(
                Example.lemma_id == word.id
            ).count()
            score += example_count * 5
            
            # Count word forms
            form_count = self.db.query(WordForm).filter(
                WordForm.lemma_id == word.id
            ).count()
            score += form_count * 2
            
            # Prefer non-fallback sources
            if word.notes and 'fallback' not in word.notes.lower():
                score += 3
            
            # Prefer better CEFR levels
            if word.cefr and word.cefr in ['A1', 'A2', 'B1', 'B2']:
                score += 2
            
            # Recency (if available)
            if hasattr(word, 'created_at') and word.created_at:
                # More recent = higher score (simple approximation)
                score += word.created_at.year - 2020  # Adjust base year as needed
            
            scored_words.append((word, score))
        
        # Sort by score (highest first)
        scored_words.sort(key=lambda x: x[1], reverse=True)
        
        best_word = scored_words[0][0]
        print(f"    Best word chosen: ID {best_word.id} (score: {scored_words[0][1]})")
        for word, score in scored_words[1:]:
            print(f"    Alternative: ID {word.id} (score: {score})")
        
        return best_word
    
    def fix_duplicates(self, exact_duplicates: Dict[str, List[WordLemma]], 
                      similar_pairs: List[Tuple[WordLemma, WordLemma, float]],
                      auto_merge_exact: bool = True,
                      auto_merge_similar: bool = False):
        """Fix duplicate entries"""
        
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
        else:
            print("\n✏️ FIXING MODE - Changes will be committed")
        
        # Fix exact duplicates
        if exact_duplicates and auto_merge_exact:
            print(f"\n📝 Fixing {len(exact_duplicates)} groups of exact duplicates:")
            
            for lemma, words in exact_duplicates.items():
                merged_word = self.merge_duplicate_group(words)
                self.stats['preserved_words'] += 1
        
        # Fix similar words (optional, more risky)
        if similar_pairs and auto_merge_similar:
            print(f"\n🔄 Fixing {len(similar_pairs)} pairs of similar words:")
            
            processed_ids = set()
            
            for word1, word2, similarity in similar_pairs:
                if word1.id in processed_ids or word2.id in processed_ids:
                    continue
                
                print(f"\n  Merging similar words: '{word1.lemma}' + '{word2.lemma}' (similarity: {similarity:.2f})")
                
                # Choose better word and merge
                merged_word = self.merge_duplicate_group([word1, word2])
                processed_ids.update([word1.id, word2.id])
        
        # Commit changes
        if not self.dry_run:
            try:
                self.db.commit()
                print("\n✅ Changes committed successfully!")
            except Exception as e:
                self.db.rollback()
                print(f"\n❌ Error committing changes: {e}")
                raise
        else:
            print("\n🔍 Dry run completed - no changes made")
    
    def print_summary(self):
        """Print summary of operations"""
        print("\n" + "="*50)
        print("📊 DEDUPLICATION SUMMARY")
        print("="*50)
        print(f"Exact duplicate groups found: {self.stats['exact_duplicates']}")
        print(f"Similar word pairs found: {self.stats['similar_pairs']}")
        print(f"Words merged: {self.stats['merged_words']}")
        print(f"Words deleted: {self.stats['deleted_words']}")
        print(f"Words preserved: {self.stats['preserved_words']}")
        
        if self.dry_run:
            print("\n🔍 This was a DRY RUN - no actual changes were made")
        else:
            print("\n✅ Changes have been applied to the database")
    
    def close(self):
        """Close database connection"""
        self.db.close()

def main():
    parser = argparse.ArgumentParser(description='Deduplicate words in the vocabulary database')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Analyze only, do not make changes (default: True)')
    parser.add_argument('--fix', action='store_true',
                       help='Actually fix duplicates (disables dry-run)')
    parser.add_argument('--auto-merge-exact', action='store_true', default=True,
                       help='Automatically merge exact duplicates')
    parser.add_argument('--auto-merge-similar', action='store_true',
                       help='Automatically merge similar words (risky!)')
    parser.add_argument('--similarity-threshold', type=float, default=0.95,
                       help='Similarity threshold for merging (0.0-1.0)')
    parser.add_argument('--show-all-similar', action='store_true',
                       help='Show all similar pairs including grammatical variations')
    
    args = parser.parse_args()
    
    # Override dry_run if --fix is specified
    dry_run = not args.fix
    
    print("🗂️ Word Deduplication Script")
    print("="*40)
    print(f"Mode: {'DRY RUN' if dry_run else 'FIXING'}")
    print(f"Auto-merge exact duplicates: {args.auto_merge_exact}")
    print(f"Auto-merge similar words: {args.auto_merge_similar}")
    print(f"Similarity threshold: {args.similarity_threshold}")
    print()
    
    if not dry_run:
        confirm = input("⚠️ This will modify the database. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return
    
    deduplicator = WordDeduplicator(dry_run=dry_run)
    
    try:
        # Analyze
        exact_duplicates, similar_pairs = deduplicator.analyze_duplicates()
        
        # Fix if requested
        if exact_duplicates or similar_pairs:
            deduplicator.fix_duplicates(
                exact_duplicates, 
                similar_pairs,
                auto_merge_exact=args.auto_merge_exact,
                auto_merge_similar=args.auto_merge_similar
            )
        else:
            print("\n✅ No duplicates found - database is clean!")
        
        # Summary
        deduplicator.print_summary()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        deduplicator.close()

if __name__ == "__main__":
    main()