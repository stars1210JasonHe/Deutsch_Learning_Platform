#!/usr/bin/env python3
"""
Database migration script for Phase 2 features
Adds exam, SRS, and progress tracking tables
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.db.session import engine
from app.db.base import Base

# Import all models to ensure they're registered
from app.models import user, word, search
from app.models.exam import (
    Exam, ExamSection, ExamQuestion, ExamAttempt, ExamResponse,
    SRSCard, LearningSession, UserProgress
)

def migrate_database():
    """Create Phase 2 database tables"""
    
    print("🔄 Starting Phase 2 database migration...")
    
    try:
        # Create all tables (existing ones will be skipped)
        Base.metadata.create_all(bind=engine)
        
        print("✅ Phase 2 database migration completed successfully!")
        
        # Print created tables
        inspector = engine.inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Current database tables:")
        for table in sorted(tables):
            print(f"   - {table}")
        
        # Check for Phase 2 specific tables
        phase2_tables = [
            "exams", "exam_sections", "exam_questions", "exam_attempts", "exam_responses",
            "srs_cards", "learning_sessions", "user_progress"
        ]
        
        missing_tables = [table for table in phase2_tables if table not in tables]
        
        if missing_tables:
            print(f"\n⚠️ Missing Phase 2 tables: {missing_tables}")
        else:
            print(f"\n✅ All Phase 2 tables created successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_database()
    if not success:
        sys.exit(1)
    
    print(f"\n🎉 Phase 2 migration complete! You can now use:")
    print(f"   - Exam generation and taking")
    print(f"   - Spaced repetition system (SRS)")
    print(f"   - Learning progress tracking")
    print(f"   - Auto-grading with fuzzy matching")