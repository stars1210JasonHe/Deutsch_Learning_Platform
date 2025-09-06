from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.feedback import WordFeedback
from app.models.word import WordLemma, Translation, Example
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse
from app.services.openai_service import OpenAIService

router = APIRouter()
openai_service = OpenAIService()


@router.post("/word/{lemma_id}", response_model=FeedbackResponse)
async def submit_word_feedback(
    lemma_id: int,
    request: FeedbackCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit feedback for a specific word"""
    
    # Verify the word exists
    word = db.query(WordLemma).filter(WordLemma.id == lemma_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    
    # Get current word data for snapshot
    translations = db.query(Translation).filter(Translation.lemma_id == lemma_id).all()
    examples = db.query(Example).filter(Example.lemma_id == lemma_id).all()
    
    current_meaning = "; ".join([t.text for t in translations if t.lang_code == "en"])
    current_example = examples[0].de_text if examples else ""
    
    # Create feedback record
    feedback = WordFeedback(
        lemma_id=lemma_id,
        user_id=current_user.id,
        feedback_type=request.feedback_type,
        description=request.description,
        suggested_correction=request.suggested_correction,
        current_meaning=current_meaning,
        current_example=current_example
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    # Log feedback submission
    print(f"✓ New feedback received for word '{word.lemma}' from user {current_user.email}")
    
    return FeedbackResponse(
        id=feedback.id,
        lemma_id=feedback.lemma_id,
        feedback_type=feedback.feedback_type,
        description=feedback.description,
        status=feedback.status,
        created_at=feedback.created_at,
        word_lemma=word.lemma
    )


@router.get("/word/{lemma_id}", response_model=List[FeedbackResponse])
async def get_word_feedback(
    lemma_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get feedback for a specific word (admin only or user's own feedback)"""
    
    # Check if user is admin or get only their own feedback
    if current_user.email == "admin@example.com":  # Replace with actual admin check
        feedbacks = db.query(WordFeedback).filter(WordFeedback.lemma_id == lemma_id).all()
    else:
        feedbacks = db.query(WordFeedback).filter(
            WordFeedback.lemma_id == lemma_id,
            WordFeedback.user_id == current_user.id
        ).all()
    
    results = []
    for feedback in feedbacks:
        word = db.query(WordLemma).filter(WordLemma.id == feedback.lemma_id).first()
        results.append(FeedbackResponse(
            id=feedback.id,
            lemma_id=feedback.lemma_id,
            feedback_type=feedback.feedback_type,
            description=feedback.description,
            status=feedback.status,
            created_at=feedback.created_at,
            word_lemma=word.lemma if word else "Unknown"
        ))
    
    return results

