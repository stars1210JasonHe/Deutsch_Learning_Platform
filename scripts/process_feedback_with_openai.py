#!/usr/bin/env python3
"""
Automated Feedback Processing with OpenAI

This script:
1. Retrieves pending feedback from the database
2. Uses OpenAI to analyze the feedback and generate corrections
3. Updates word information based on the analysis
4. Marks feedback as processed
"""

import sqlite3
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional
import json

# Add app directory to path to import services
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app'))

try:
    from services.openai_service import OpenAIService
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI service not available")

class FeedbackProcessor:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app.db')
        self.openai_service = OpenAIService() if OPENAI_AVAILABLE else None
        self.processed_count = 0
        self.failed_count = 0
        
    def get_pending_feedback(self, limit: int = 10) -> List[Dict]:
        """Retrieve pending feedback from database"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        query = """
        SELECT 
            f.id as feedback_id,
            f.lemma_id,
            f.user_id,
            f.feedback_type,
            f.description,
            f.suggested_correction,
            f.current_meaning,
            f.current_example,
            f.created_at,
            w.lemma,
            w.pos,
            w.cefr,
            GROUP_CONCAT(DISTINCT t_en.text) as current_translations_en,
            GROUP_CONCAT(DISTINCT t_zh.text) as current_translations_zh,
            GROUP_CONCAT(DISTINCT e.de_text) as current_examples
        FROM word_feedback f
        JOIN word_lemmas w ON f.lemma_id = w.id
        LEFT JOIN translations t_en ON w.id = t_en.lemma_id AND t_en.lang_code = 'en'
        LEFT JOIN translations t_zh ON w.id = t_zh.lemma_id AND t_zh.lang_code = 'zh'
        LEFT JOIN examples e ON w.id = e.lemma_id
        WHERE f.status = 'pending'
        GROUP BY f.id
        ORDER BY f.created_at ASC
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    async def analyze_feedback_with_openai(self, feedback: Dict) -> Optional[Dict]:
        """Use OpenAI to analyze feedback and suggest corrections"""
        
        if not self.openai_service:
            print("OpenAI service not available")
            return None
        
        # Create analysis prompt
        prompt = f"""
You are a German language expert helping to fix word data based on user feedback.

Word Information:
- German Word: {feedback['lemma']}
- Part of Speech: {feedback['pos'] or 'Unknown'}
- Current English Translations: {feedback['current_translations_en'] or 'None'}
- Current Chinese Translations: {feedback['current_translations_zh'] or 'None'}
- Current Examples: {feedback['current_examples'] or 'None'}

User Feedback:
- Issue Type: {feedback['feedback_type']}
- Description: {feedback['description']}
- User's Suggested Fix: {feedback['suggested_correction'] or 'None provided'}

Please analyze this feedback and provide corrections in the following JSON format:
{{
    "analysis": "Your analysis of whether the feedback is valid",
    "is_valid_feedback": true/false,
    "corrections": {{
        "translations_en": ["corrected English translations"],
        "translations_zh": ["corrected Chinese translations"], 
        "examples": [
            {{
                "de": "German example",
                "en": "English translation",
                "zh": "Chinese translation"
            }}
        ],
        "pos": "corrected part of speech if needed",
        "notes": "Any additional notes about the corrections"
    }},
    "confidence": 0.95,
    "recommended_action": "update/reject/needs_review"
}}

Focus on accuracy and provide high-quality corrections. If you're unsure about something, set confidence lower and recommend manual review.
"""

        try:
            # Use OpenAI to analyze the feedback
            response = await self.openai_service.get_completion(prompt)
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract key information
                print(f"Could not parse JSON response for feedback {feedback['feedback_id']}")
                return {
                    "analysis": response[:500],
                    "is_valid_feedback": True,
                    "confidence": 0.5,
                    "recommended_action": "needs_review"
                }
                
        except Exception as e:
            print(f"Error analyzing feedback {feedback['feedback_id']}: {e}")
            return None
    
    def apply_corrections(self, feedback: Dict, analysis: Dict) -> bool:
        """Apply the corrections to the database"""
        
        if not analysis.get('is_valid_feedback', False):
            print(f"Feedback {feedback['feedback_id']} marked as invalid - skipping corrections")
            return False
        
        if analysis.get('confidence', 0) < 0.7:
            print(f"Confidence too low ({analysis.get('confidence')}) for feedback {feedback['feedback_id']} - marking for review")
            self.update_feedback_status(feedback['feedback_id'], 'needs_review', 
                                      f"Low confidence: {analysis.get('analysis', '')}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            corrections = analysis.get('corrections', {})
            
            # Update English translations
            if corrections.get('translations_en'):
                cursor.execute("DELETE FROM translations WHERE lemma_id = ? AND lang_code = 'en'", 
                             (feedback['lemma_id'],))
                for translation in corrections['translations_en']:
                    cursor.execute("""
                        INSERT INTO translations (lemma_id, lang_code, text, source)
                        VALUES (?, 'en', ?, 'feedback_correction')
                    """, (feedback['lemma_id'], translation))
            
            # Update Chinese translations
            if corrections.get('translations_zh'):
                cursor.execute("DELETE FROM translations WHERE lemma_id = ? AND lang_code = 'zh'", 
                             (feedback['lemma_id'],))
                for translation in corrections['translations_zh']:
                    cursor.execute("""
                        INSERT INTO translations (lemma_id, lang_code, text, source)
                        VALUES (?, 'zh', ?, 'feedback_correction')
                    """, (feedback['lemma_id'], translation))
            
            # Update examples
            if corrections.get('examples'):
                cursor.execute("DELETE FROM examples WHERE lemma_id = ?", (feedback['lemma_id'],))
                for example in corrections['examples']:
                    cursor.execute("""
                        INSERT INTO examples (lemma_id, de_text, en_text, zh_text)
                        VALUES (?, ?, ?, ?)
                    """, (feedback['lemma_id'], example.get('de', ''), 
                          example.get('en', ''), example.get('zh', '')))
            
            # Update POS if needed
            if corrections.get('pos') and corrections['pos'] != feedback['pos']:
                cursor.execute("UPDATE word_lemmas SET pos = ? WHERE id = ?", 
                             (corrections['pos'], feedback['lemma_id']))
            
            conn.commit()
            
            # Mark feedback as fixed
            self.update_feedback_status(
                feedback['feedback_id'], 
                'fixed',
                f"Auto-corrected: {analysis.get('analysis', '')}"
            )
            
            print(f"✓ Applied corrections for word '{feedback['lemma']}' (Feedback ID: {feedback['feedback_id']})")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Failed to apply corrections for feedback {feedback['feedback_id']}: {e}")
            return False
        finally:
            conn.close()
    
    def update_feedback_status(self, feedback_id: int, status: str, notes: str = ""):
        """Update feedback status in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE word_feedback 
                SET status = ?, developer_notes = ?, updated_at = ?
                WHERE id = ?
            """, (status, notes, datetime.now(), feedback_id))
            conn.commit()
        except Exception as e:
            print(f"Failed to update feedback status: {e}")
        finally:
            conn.close()
    
    async def process_all_pending_feedback(self, limit: int = 10, auto_apply: bool = False):
        """Process all pending feedback"""
        
        print("AUTOMATED FEEDBACK PROCESSING")
        print("=" * 50)
        print(f"Processing up to {limit} pending feedback entries...")
        
        # Get pending feedback
        feedback_list = self.get_pending_feedback(limit)
        
        if not feedback_list:
            print("No pending feedback found.")
            return
        
        print(f"Found {len(feedback_list)} pending feedback entries")
        print("-" * 50)
        
        for i, feedback in enumerate(feedback_list, 1):
            print(f"\n[{i}/{len(feedback_list)}] Processing feedback for word: {feedback['lemma']}")
            print(f"Issue: {feedback['feedback_type']} - {feedback['description'][:100]}...")
            
            # Analyze with OpenAI
            analysis = await self.analyze_feedback_with_openai(feedback)
            
            if not analysis:
                print("✗ Failed to analyze feedback")
                self.failed_count += 1
                continue
            
            print(f"Analysis: {analysis.get('analysis', 'No analysis')[:100]}...")
            print(f"Valid: {analysis.get('is_valid_feedback', False)}")
            print(f"Confidence: {analysis.get('confidence', 0):.2f}")
            print(f"Recommended Action: {analysis.get('recommended_action', 'unknown')}")
            
            if auto_apply and analysis.get('recommended_action') == 'update':
                if self.apply_corrections(feedback, analysis):
                    self.processed_count += 1
                else:
                    self.failed_count += 1
            else:
                print("Manual review required - updating status only")
                self.update_feedback_status(
                    feedback['feedback_id'],
                    'reviewed',
                    f"AI Analysis: {analysis.get('analysis', '')}"
                )
                self.processed_count += 1
        
        print("\n" + "=" * 50)
        print("PROCESSING SUMMARY")
        print(f"Successfully processed: {self.processed_count}")
        print(f"Failed: {self.failed_count}")
        print(f"Total: {len(feedback_list)}")
    
    def generate_feedback_report(self):
        """Generate a summary report of all feedback"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\nFEEDBACK SUMMARY REPORT")
        print("=" * 50)
        
        # Overall statistics
        cursor.execute("SELECT COUNT(*) FROM word_feedback")
        total_feedback = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM word_feedback GROUP BY status")
        status_counts = cursor.fetchall()
        
        print(f"Total Feedback: {total_feedback}")
        print("\nBy Status:")
        for status, count in status_counts:
            print(f"  {status}: {count}")
        
        # Recent feedback by type
        cursor.execute("""
            SELECT feedback_type, COUNT(*) 
            FROM word_feedback 
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY feedback_type
        """)
        recent_types = cursor.fetchall()
        
        if recent_types:
            print("\nRecent Feedback Types (Last 7 days):")
            for feedback_type, count in recent_types:
                print(f"  {feedback_type}: {count}")
        
        conn.close()

async def main():
    """Main function to run the feedback processor"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Process user feedback with OpenAI')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of feedback to process')
    parser.add_argument('--auto-apply', action='store_true', help='Automatically apply high-confidence corrections')
    parser.add_argument('--report-only', action='store_true', help='Only generate report, do not process')
    
    args = parser.parse_args()
    
    processor = FeedbackProcessor()
    
    if args.report_only:
        processor.generate_feedback_report()
    else:
        await processor.process_all_pending_feedback(args.limit, args.auto_apply)
        processor.generate_feedback_report()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())