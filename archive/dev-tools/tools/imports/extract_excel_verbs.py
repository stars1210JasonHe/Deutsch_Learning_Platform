"""
Extract verbs from Excel file and add missing ones to database via OpenAI
"""
import pandas as pd
import sqlite3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all models first to ensure relationships are properly resolved
from app.models.user import User
from app.models.word import WordLemma, WordForm, Translation, Example
from app.models.search import SearchCache, SearchHistory, WordList, WordListItem
from app.models.exam import (
    Exam, ExamSection, ExamQuestion, ExamAttempt, ExamResponse, 
    SRSCard, LearningSession, UserProgress
)

from app.services.vocabulary_service import VocabularyService
from app.db.session import SessionLocal

async def extract_and_add_verbs():
    print("=== EXTRACTING VERBS FROM EXCEL FILE ===")
    
    # Read Excel file - specifically the Datenbank sheet
    excel_file = "德语动词变位练习模板 20250507.xlsm"
    try:
        # Read the Datenbank sheet, column A starting from A2
        df = pd.read_excel(excel_file, sheet_name='Datenbank', engine='openpyxl')
        print(f"Excel file loaded successfully. Shape: {df.shape}")
        
        # Get the first column (verbs) and remove NaN values
        verbs_column = df.iloc[:, 0].dropna().tolist()  # First column, all rows
        
        # Remove header if it exists and clean the data
        verbs = []
        for verb in verbs_column:
            if isinstance(verb, str) and verb.strip():
                verb_clean = verb.strip()
                # Skip obvious headers
                if not verb_clean.lower() in ['verb', 'verbs', 'lemma', 'infinitiv']:
                    verbs.append(verb_clean)
        
        print(f"Found {len(verbs)} potential verbs in Excel file")
        print("First 10 verbs:")
        for i, verb in enumerate(verbs[:10], 1):
            try:
                print(f"  {i}. {verb}")
            except UnicodeEncodeError:
                print(f"  {i}. [German verb with umlauts]")
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # Connect to database
    db = SessionLocal()
    try:
        # Get a user for the service (required for OpenAI calls)
        user = db.query(User).first()
        if not user:
            print("No user found in database - cannot proceed")
            return
            
        # Initialize vocabulary service
        vocab_service = VocabularyService()
        
        # Check existing verbs in database
        existing_verbs = set()
        from sqlalchemy import text
        cursor = db.execute(text('SELECT lemma FROM word_lemmas WHERE pos = "verb"'))
        for row in cursor:
            existing_verbs.add(row[0].lower())
            
        print(f"Found {len(existing_verbs)} existing verbs in database")
        
        # Find missing verbs
        missing_verbs = []
        for verb in verbs:
            if verb.lower() not in existing_verbs:
                missing_verbs.append(verb)
                
        print(f"Found {len(missing_verbs)} missing verbs to add")
        print("First 20 missing verbs:")
        for i, verb in enumerate(missing_verbs[:20], 1):
            try:
                print(f"  {i:2d}. {verb}")
            except UnicodeEncodeError:
                print(f"  {i:2d}. [German verb]")
        
        if not missing_verbs:
            print("All verbs already exist in database!")
            return
            
        # Add missing verbs using OpenAI
        added_count = 0
        failed_count = 0
        
        for i, verb in enumerate(missing_verbs, 1):
            try:
                print(f"\n{i:3d}/{len(missing_verbs):3d}. Processing '{verb}'...")
                
                # Use vocabulary service to get/create word (this will call OpenAI if needed)
                result = await vocab_service.get_or_create_word(db, verb, user)
                
                if result.get('found', False):
                    added_count += 1
                    print(f"     ✅ Added '{verb}' successfully")
                    
                    # Check if it has conjugation tables
                    tables = result.get('tables')
                    if tables:
                        tense_count = len([k for k in tables.keys() if k in ['praesens', 'praeteritum', 'perfekt', 'plusquamperfekt', 'imperativ']])
                        print(f"     📊 {tense_count}/5 essential tenses")
                    else:
                        print(f"     ⚠️  No conjugation tables")
                else:
                    failed_count += 1
                    print(f"     ❌ Failed to add '{verb}' - {result.get('message', 'Unknown error')}")
                    
                # Small delay to avoid overwhelming OpenAI API
                if i % 5 == 0:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                failed_count += 1
                print(f"     ❌ Error processing '{verb}': {str(e)}")
                
        print("\n=== FINAL RESULTS ===")
        print(f"Total verbs in Excel: {len(verbs)}")
        print(f"Already in database: {len(verbs) - len(missing_verbs)}")
        print(f"Missing verbs found: {len(missing_verbs)}")
        print(f"Successfully added: {added_count}")
        print(f"Failed to add: {failed_count}")
        print(f"Success rate: {added_count/(added_count+failed_count)*100:.1f}%" if (added_count+failed_count) > 0 else "N/A")
        
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(extract_and_add_verbs())