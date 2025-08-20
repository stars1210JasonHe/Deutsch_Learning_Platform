# Import all models to ensure SQLAlchemy can resolve relationships
from .user import User, UserRole
from .word import WordLemma, Translation, Example, WordForm
from .search import SearchHistory
from .exam import (
    Exam, ExamSection, ExamQuestion, ExamAttempt, ExamResponse,
    SRSCard, LearningSession, UserProgress
)

__all__ = [
    "User", "UserRole",
    "WordLemma", "Translation", "Example", "WordForm", 
    "SearchHistory",
    "Exam", "ExamSection", "ExamQuestion", "ExamAttempt", "ExamResponse",
    "SRSCard", "LearningSession", "UserProgress"
]