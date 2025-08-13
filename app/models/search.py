from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class SearchCache(Base):
    __tablename__ = "search_cache"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String, index=True, nullable=False)
    query_type = Column(String, index=True, nullable=False)  # "word", "sentence", "translation"
    query_hash = Column(String, unique=True, index=True, nullable=False)  # MD5 hash for fast lookup
    response_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    query_text = Column(String, nullable=False)
    query_type = Column(String, nullable=False)
    cached_result_id = Column(Integer, ForeignKey("search_cache.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="search_history")
    cached_result = relationship("SearchCache")


class WordList(Base):
    __tablename__ = "word_lists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="word_lists")
    items = relationship("WordListItem", back_populates="word_list", cascade="all, delete-orphan")


class WordListItem(Base):
    __tablename__ = "word_list_items"

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("word_lists.id", ondelete="CASCADE"), index=True)
    lemma_id = Column(Integer, ForeignKey("word_lemmas.id", ondelete="CASCADE"), index=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    word_list = relationship("WordList", back_populates="items")
    lemma = relationship("WordLemma")