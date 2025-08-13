"""
Exam system models for Phase 2
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Exam(Base):
    """Generated exam model"""
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    cefr_level = Column(String(10), nullable=False)  # A1, A2, B1, B2, C1, C2
    topics = Column(JSON)  # List of topics covered
    total_questions = Column(Integer, default=0)
    time_limit_minutes = Column(Integer)  # Optional time limit
    
    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    creator = relationship("User", back_populates="created_exams")
    sections = relationship("ExamSection", back_populates="exam", cascade="all, delete-orphan")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")


class ExamSection(Base):
    """Exam section model"""
    __tablename__ = "exam_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)
    
    # Relationships
    exam = relationship("Exam", back_populates="sections")
    questions = relationship("ExamQuestion", back_populates="section", cascade="all, delete-orphan")


class ExamQuestion(Base):
    """Exam question model"""
    __tablename__ = "exam_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("exam_sections.id"), nullable=False)
    
    # Question content
    question_type = Column(String(50), nullable=False)  # mcq, cloze, matching, reorder, writing
    prompt = Column(Text, nullable=False)
    content = Column(JSON)  # Question-specific data (options, blanks, etc.)
    correct_answer = Column(JSON)  # Correct answer(s)
    alternatives = Column(JSON)  # Alternative acceptable answers
    explanation = Column(Text)
    
    # Metadata
    points = Column(Float, default=1.0)
    difficulty = Column(String(20))  # easy, medium, hard
    order_index = Column(Integer, default=0)
    
    # Word associations for SRS
    target_words = Column(JSON)  # List of lemma IDs this question targets
    
    # Relationships
    section = relationship("ExamSection", back_populates="questions")
    responses = relationship("ExamResponse", back_populates="question", cascade="all, delete-orphan")


class ExamAttempt(Base):
    """User exam attempt model"""
    __tablename__ = "exam_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Attempt data
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    time_taken_seconds = Column(Integer)
    
    # Scoring
    total_points = Column(Float, default=0.0)
    max_points = Column(Float, default=0.0)
    percentage_score = Column(Float)
    
    # Status
    status = Column(String(20), default="in_progress")  # in_progress, completed, abandoned
    
    # Relationships
    exam = relationship("Exam", back_populates="attempts")
    user = relationship("User", back_populates="exam_attempts")
    responses = relationship("ExamResponse", back_populates="attempt", cascade="all, delete-orphan")


class ExamResponse(Base):
    """User response to exam question"""
    __tablename__ = "exam_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("exam_questions.id"), nullable=False)
    
    # Response data
    user_answer = Column(JSON)  # User's submitted answer
    is_correct = Column(Boolean)
    partial_credit = Column(Float, default=0.0)  # 0.0 to 1.0
    points_earned = Column(Float, default=0.0)
    
    # Feedback
    feedback = Column(Text)
    auto_feedback = Column(JSON)  # Structured auto-generated feedback
    
    # Timing
    time_taken_seconds = Column(Integer)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    attempt = relationship("ExamAttempt", back_populates="responses")
    question = relationship("ExamQuestion", back_populates="responses")


class SRSCard(Base):
    """Spaced Repetition System card"""
    __tablename__ = "srs_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lemma_id = Column(Integer, ForeignKey("word_lemmas.id"), nullable=False)
    
    # SRS algorithm data (simplified SM-2)
    ease_factor = Column(Float, default=2.5)  # Ease factor
    interval_days = Column(Integer, default=1)  # Current interval
    repetition_count = Column(Integer, default=0)  # Number of successful reviews
    
    # Scheduling
    next_review_date = Column(DateTime(timezone=True))
    last_reviewed_at = Column(DateTime(timezone=True))
    
    # Performance tracking
    correct_count = Column(Integer, default=0)
    incorrect_count = Column(Integer, default=0)
    streak = Column(Integer, default=0)  # Current correct streak
    
    # Question types this card has been tested on
    question_types_seen = Column(JSON, default=list)
    
    # Card status
    is_active = Column(Boolean, default=True)
    is_mature = Column(Boolean, default=False)  # Interval >= 21 days
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="srs_cards")
    lemma = relationship("WordLemma")  # Removed back_populates to avoid circular import


class LearningSession(Base):
    """Learning session tracking"""
    __tablename__ = "learning_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session data
    session_type = Column(String(50), nullable=False)  # exam, srs_review, practice
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Performance metrics
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    accuracy_percentage = Column(Float)
    
    # Content covered
    topics_covered = Column(JSON)  # List of topics/grammar points
    words_practiced = Column(JSON)  # List of lemma IDs
    
    # Reference to specific activity
    exam_attempt_id = Column(Integer, ForeignKey("exam_attempts.id"))
    
    # Relationships
    user = relationship("User", back_populates="learning_sessions")
    exam_attempt = relationship("ExamAttempt")


class UserProgress(Base):
    """User learning progress tracking"""
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # CEFR progress
    current_level = Column(String(10), default="A1")  # A1, A2, B1, B2, C1, C2
    
    # Statistics
    total_words_learned = Column(Integer, default=0)
    vocabulary_size = Column(Integer, default=0)  # Unique words in SRS
    
    # Performance metrics
    average_accuracy = Column(Float, default=0.0)
    study_streak_days = Column(Integer, default=0)
    total_study_time_hours = Column(Float, default=0.0)
    
    # Weekly/monthly goals
    daily_goal_minutes = Column(Integer, default=15)
    weekly_goal_cards = Column(Integer, default=50)
    
    # Achievement tracking
    achievements_unlocked = Column(JSON, default=list)
    level_milestones = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="progress")