"""
Migration script to fix existing cloze questions by adding missing 'text' field
This script converts prompts like "Füllen Sie die Lücken: 'Mein Bruder ist ___ und ich bin ___.'"
into proper text field with placeholders: "Mein Bruder ist [b1] und ich bin [b2]."
"""
import sys
import os
import re
import json
from typing import Dict, List, Any

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import locale
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from db.session import SessionLocal
from models.exam import ExamQuestion


def extract_sentence_from_prompt(prompt: str) -> str:
    """Extract the actual sentence from German cloze prompt."""
    # Pattern matches: "Füllen Sie die Lücke(n): 'SENTENCE'" or similar
    patterns = [
        r"Füllen Sie die Lücken?: ['\"](.+?)['\"]",
        r"Fill in the blanks?: ['\"](.+?)['\"]",
        r"Complete the sentence: ['\"](.+?)['\"]",
        r"['\"](.+?)['\"]"  # Fallback: just extract quoted text
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # If no pattern matches, try to extract everything after ":"
    if ":" in prompt:
        parts = prompt.split(":", 1)
        if len(parts) > 1:
            sentence = parts[1].strip()
            # Remove quotes if present
            sentence = re.sub(r'^[\'"]|[\'"]$', '', sentence)
            return sentence
    
    # Last resort: return the whole prompt
    return prompt.strip()


def convert_underscores_to_placeholders(sentence: str, blanks: List[Dict]) -> str:
    """Convert underscores ___ to [b1], [b2], etc. based on blank IDs."""
    # Sort blanks by position if available
    sorted_blanks = sorted(blanks, key=lambda x: x.get('position', 0))
    
    # Replace each ___ with corresponding blank ID
    result = sentence
    for i, blank in enumerate(sorted_blanks):
        blank_id = blank.get('id', f'b{i+1}')
        # Replace first occurrence of ___ with [blank_id]
        result = result.replace('___', f'[{blank_id}]', 1)
    
    return result


def migrate_single_cloze_question(question: ExamQuestion) -> bool:
    """Migrate a single cloze question. Returns True if successful."""
    try:
        # Parse existing content
        if isinstance(question.content, str):
            content = json.loads(question.content)
        else:
            content = question.content or {}
        
        # Skip if already has text field
        if 'text' in content:
            print(f"  Question {question.id} already has text field, skipping")
            return True
        
        # Get blanks
        blanks = content.get('blanks', [])
        if not blanks:
            print(f"  Question {question.id} has no blanks, skipping")
            return False
        
        # Extract sentence from prompt
        sentence = extract_sentence_from_prompt(question.prompt)
        if not sentence:
            print(f"  Question {question.id} couldn't extract sentence from prompt")
            return False
        
        # Convert underscores to placeholders
        text_with_placeholders = convert_underscores_to_placeholders(sentence, blanks)
        
        # Add text field to content
        content['text'] = text_with_placeholders
        
        # Update question content - ensure SQLAlchemy tracks the change
        question.content = content
        # Force SQLAlchemy to recognize the change
        from sqlalchemy.orm import attributes
        attributes.flag_modified(question, 'content')
        
        print(f"  SUCCESS Question {question.id}: '{sentence}' -> '{text_with_placeholders}'")
        return True
        
    except Exception as e:
        print(f"  ERROR processing question {question.id}: {e}")
        return False


def migrate_cloze_questions(dry_run: bool = True) -> Dict[str, Any]:
    """
    Migrate all cloze questions to add missing text fields.
    
    Args:
        dry_run: If True, doesn't save changes (default: True for safety)
    
    Returns:
        Dictionary with migration results
    """
    print("Starting Cloze Questions Migration")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    print("=" * 50)
    
    db = SessionLocal()
    results = {
        'total_processed': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'questions': []
    }
    
    try:
        # Get all cloze questions
        cloze_questions = db.query(ExamQuestion).filter(
            ExamQuestion.question_type == 'cloze'
        ).all()
        
        print(f"Found {len(cloze_questions)} cloze questions to process\n")
        
        for question in cloze_questions:
            results['total_processed'] += 1
            try:
                print(f"Processing Question {question.id}:")
                # Safe prompt display with encoding handling
                safe_prompt = (question.prompt[:100] + "...") if len(question.prompt) > 100 else question.prompt
                print(f"  Prompt: {repr(safe_prompt)}")  # Use repr to handle encoding issues
                
                # Migrate the question
                success = migrate_single_cloze_question(question)
            except UnicodeEncodeError as e:
                print(f"  Encoding error with question {question.id}, continuing...")
                success = migrate_single_cloze_question(question)
            
            if success:
                results['successful'] += 1
                results['questions'].append({
                    'id': question.id,
                    'status': 'success',
                    'prompt': question.prompt[:100],
                    'new_text': question.content.get('text', '') if hasattr(question.content, 'get') else ''
                })
            else:
                results['failed'] += 1
                results['questions'].append({
                    'id': question.id,
                    'status': 'failed',
                    'prompt': question.prompt[:100]
                })
            
            print()
        
        # Save changes if not dry run
        if not dry_run and results['successful'] > 0:
            print("Committing changes to database...")
            db.commit()
            print("Changes saved successfully!")
        elif dry_run:
            print("DRY RUN - No changes saved to database")
            db.rollback()
        
    except Exception as e:
        print(f"Fatal error during migration: {e}")
        db.rollback()
        results['fatal_error'] = str(e)
    
    finally:
        db.close()
    
    # Print summary
    print("\n" + "=" * 50)
    print("MIGRATION SUMMARY")
    print(f"Total processed: {results['total_processed']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {(results['successful']/results['total_processed']*100):.1f}%" if results['total_processed'] > 0 else "0%")
    
    return results


def main():
    """Main function to run migration with command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate cloze questions to add text field')
    parser.add_argument('--dry-run', action='store_true', default=True,
                      help='Run in dry-run mode (default: True)')
    parser.add_argument('--live', action='store_true',
                      help='Run live migration (saves changes)')
    parser.add_argument('--force', action='store_true',
                      help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # If --live is specified, turn off dry-run
    dry_run = not args.live
    
    if not dry_run and not args.force:
        print("WARNING: This will modify the database!")
        try:
            response = input("Are you sure you want to proceed? (type 'YES' to continue): ")
            if response != 'YES':
                print("Migration cancelled.")
                return
        except EOFError:
            print("Cannot get user input. Use --force flag to skip confirmation.")
            return
    
    # Run migration
    results = migrate_cloze_questions(dry_run=dry_run)
    
    # Exit with appropriate code
    if 'fatal_error' in results:
        sys.exit(1)
    elif results['failed'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()