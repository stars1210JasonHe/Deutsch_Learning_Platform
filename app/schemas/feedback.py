from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FeedbackCreateRequest(BaseModel):
    feedback_type: str  # "incorrect_meaning", "incorrect_example", "incorrect_grammar", "other"
    description: str
    suggested_correction: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    lemma_id: int
    feedback_type: str
    description: str
    status: str
    created_at: datetime
    word_lemma: str

    class Config:
        from_attributes = True