"""
Database initialization script
"""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User, UserRole
from app.models.word import WordLemma, Translation, Example
from app.core.security import get_password_hash

# Import all models to ensure they are registered
from app.models import user, word, search


def init_db():
    """Initialize database with tables and sample data"""
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@vibedeutsch.com").first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                email="admin@vibedeutsch.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            db.commit()
            print("✅ Created admin user: admin@vibedeutsch.com / admin123")
        
        # Add some sample words if database is empty
        if db.query(WordLemma).count() == 0:
            sample_words = [
                {
                    "lemma": "sein",
                    "pos": "verb",
                    "cefr": "A1",
                    "ipa": "zaɪn",
                    "frequency": 9999,
                    "notes": "Most important German verb - 'to be'"
                },
                {
                    "lemma": "haben",
                    "pos": "verb",
                    "cefr": "A1",
                    "ipa": "ˈhaːbn̩",
                    "frequency": 9998,
                    "notes": "Second most important German verb - 'to have'"
                },
                {
                    "lemma": "der Tisch",
                    "lemma": "Tisch",
                    "pos": "noun",
                    "cefr": "A1",
                    "ipa": "tɪʃ",
                    "frequency": 1500,
                    "notes": "Common furniture noun - table"
                }
            ]
            
            for word_data in sample_words:
                word = WordLemma(**word_data)
                db.add(word)
                db.commit()
                db.refresh(word)
                
                # Add translations
                if word.lemma == "sein":
                    translations = [
                        Translation(lemma_id=word.id, lang_code="en", text="to be"),
                        Translation(lemma_id=word.id, lang_code="zh", text="是，存在")
                    ]
                elif word.lemma == "haben":
                    translations = [
                        Translation(lemma_id=word.id, lang_code="en", text="to have"),
                        Translation(lemma_id=word.id, lang_code="zh", text="有，拥有")
                    ]
                elif word.lemma == "Tisch":
                    translations = [
                        Translation(lemma_id=word.id, lang_code="en", text="table"),
                        Translation(lemma_id=word.id, lang_code="zh", text="桌子")
                    ]
                
                for translation in translations:
                    db.add(translation)
                
                # Add example sentences
                if word.lemma == "Tisch":
                    example = Example(
                        lemma_id=word.id,
                        de_text="Der Tisch ist groß.",
                        en_text="The table is big.",
                        zh_text="桌子很大。",
                        level="A1"
                    )
                    db.add(example)
            
            db.commit()
            print("✅ Added sample vocabulary")
        
        print("🚀 Database initialized successfully!")
        
        # 初始化词库数据
        print("\n🌱 Initializing vocabulary database...")
        from app.db.seed_vocabulary import seed_vocabulary_database
        import asyncio
        asyncio.run(seed_vocabulary_database())
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()