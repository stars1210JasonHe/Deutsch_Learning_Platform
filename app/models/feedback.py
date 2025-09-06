from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class WordFeedback(Base):
    __tablename__ = "word_feedback"

    id = Column(Integer, primary_key=True, index=True)
    lemma_id = Column(Integer, ForeignKey("word_lemmas.id", ondelete="CASCADE"), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    # Feedback details
    feedback_type = Column(String, nullable=False)  # "incorrect_meaning", "incorrect_example", "incorrect_grammar", "other"
    description = Column(Text, nullable=False)  # User's description of the issue
    suggested_correction = Column(Text)  # Optional: user's suggested fix
    
    # Current word data snapshot (for reference)
    current_meaning = Column(Text)  # Current translation when feedback was submitted
    current_example = Column(Text)  # Current example when feedback was submitted
    
    # Status tracking
    status = Column(String, default="pending")  # "pending", "reviewed", "fixed", "dismissed"
    developer_notes = Column(Text)  # Notes from developer when reviewing
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lemma = relationship("WordLemma")
    user = relationship("User")