from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class WordLemma(Base):
    __tablename__ = "word_lemmas"

    id = Column(Integer, primary_key=True, index=True)
    lemma = Column(String, index=True, unique=True, nullable=False)  # e.g., "gehen"
    pos = Column(String, index=True)   # "verb"|"noun"|"adj"|...
    cefr = Column(String)              # "A1".."C2"
    ipa = Column(String)               # IPA pronunciation
    frequency = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    forms = relationship("WordForm", back_populates="lemma", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="lemma", cascade="all, delete-orphan")
    examples = relationship("Example", back_populates="lemma", cascade="all, delete-orphan")
    
    # Phase 2: SRS relationship (temporarily disabled to avoid circular import)
    # srs_cards = relationship("SRSCard", back_populates="lemma", cascade="all, delete-orphan")


class WordForm(Base):
    __tablename__ = "word_forms"

    id = Column(Integer, primary_key=True, index=True)
    lemma_id = Column(Integer, ForeignKey("word_lemmas.id", ondelete="CASCADE"), index=True)
    form = Column(String, index=True)  # "gegangen", "ich gehe", "die Tische", etc.
    feature_key = Column(String)       # "tense","person","number","case","gender"
    feature_value = Column(String)     # "praesens","ich","plural","akk","masc"

    # Relationships
    lemma = relationship("WordLemma", back_populates="forms")


class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    lemma_id = Column(Integer, ForeignKey("word_lemmas.id", ondelete="CASCADE"), index=True)
    lang_code = Column(String, index=True)  # "en","zh"
    text = Column(Text)
    source = Column(String, default="openai")  # "openai", "human", "imported"

    # Relationships
    lemma = relationship("WordLemma", back_populates="translations")


class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, index=True)
    lemma_id = Column(Integer, ForeignKey("word_lemmas.id", ondelete="CASCADE"), index=True)
    de_text = Column(Text, nullable=False)
    en_text = Column(Text)
    zh_text = Column(Text)
    level = Column(String, default="A1")

    # Relationships
    lemma = relationship("WordLemma", back_populates="examples")