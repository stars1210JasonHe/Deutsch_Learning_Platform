"""
Exam API Endpoints - Phase 2
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.exam import Exam, ExamAttempt, ExamResponse, ExamQuestion
from app.services.exam_service import ExamService
from app.services.grading_service import GradingService
from datetime import datetime

router = APIRouter(prefix="/exam", tags=["exam"])


# Pydantic models
class ExamGenerateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None  # New field for description-based generation
    level: str = "A1"
    topics: Optional[List[str]] = None
    question_types: Optional[List[str]] = None
    question_count: int = 10


class ExamStartRequest(BaseModel):
    exam_id: int


class ExamSubmitAnswerRequest(BaseModel):
    attempt_id: int
    question_id: int
    answer: Any
    time_taken_seconds: Optional[int] = None


class ExamCompleteRequest(BaseModel):
    attempt_id: int


# Exam generation endpoints
@router.post("/generate")
async def generate_exam(
    request: ExamGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a new exam using AI"""
    
    exam_service = ExamService()
    
    try:
        result = await exam_service.generate_exam(
            db=db,
            user=current_user,
            level=request.level,
            topics=request.topics,
            question_types=request.question_types,
            question_count=request.question_count,
            title=request.title,
            description=request.description
        )
        
        return {
            "success": True,
            "exam": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate exam: {str(e)}"
        )


@router.get("/list")
async def list_exams(
    skip: int = 0,
    limit: int = 20,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available exams"""
    
    query = db.query(Exam).filter(Exam.is_active == True)
    
    if level:
        query = query.filter(Exam.cefr_level == level)
    
    total = query.count()
    exams = query.offset(skip).limit(limit).all()
    
    exam_list = []
    for exam in exams:
        exam_data = {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "level": exam.cefr_level,
            "topics": exam.topics,
            "total_questions": exam.total_questions,
            "time_limit_minutes": exam.time_limit_minutes,
            "created_at": exam.created_at.isoformat(),
            "creator_email": exam.creator.email if exam.creator else None
        }
        exam_list.append(exam_data)
    
    return {
        "exams": exam_list,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{exam_id}")
async def get_exam_details(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed exam information"""
    
    exam = db.query(Exam).filter(
        Exam.id == exam_id,
        Exam.is_active == True
    ).first()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    # Format exam for frontend (without answers)
    sections = []
    for section in exam.sections:
        section_data = {
            "id": section.id,
            "title": section.title,
            "description": section.description,
            "questions": []
        }
        
        for question in section.questions:
            question_data = {
                "id": question.id,
                "type": question.question_type,
                "prompt": question.prompt,
                "content": question.content,
                "points": question.points,
                "difficulty": question.difficulty
            }
            section_data["questions"].append(question_data)
        
        sections.append(section_data)
    
    return {
        "id": exam.id,
        "title": exam.title,
        "description": exam.description,
        "level": exam.cefr_level,
        "topics": exam.topics,
        "total_questions": exam.total_questions,
        "time_limit_minutes": exam.time_limit_minutes,
        "sections": sections
    }


# Exam taking endpoints
@router.post("/start")
async def start_exam(
    request: ExamStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start taking an exam"""
    
    exam = db.query(Exam).filter(
        Exam.id == request.exam_id,
        Exam.is_active == True
    ).first()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    # Check if user already has an in-progress attempt
    existing_attempt = db.query(ExamAttempt).filter(
        ExamAttempt.exam_id == request.exam_id,
        ExamAttempt.user_id == current_user.id,
        ExamAttempt.status == "in_progress"
    ).first()
    
    if existing_attempt:
        return {
            "attempt_id": existing_attempt.id,
            "started_at": existing_attempt.started_at.isoformat(),
            "message": "Resuming existing attempt"
        }
    
    # Create new attempt
    attempt = ExamAttempt(
        exam_id=request.exam_id,
        user_id=current_user.id,
        status="in_progress",
        max_points=sum(q.points for s in exam.sections for q in s.questions)
    )
    
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    return {
        "attempt_id": attempt.id,
        "started_at": attempt.started_at.isoformat(),
        "max_points": attempt.max_points,
        "time_limit_minutes": exam.time_limit_minutes
    }


@router.post("/submit-answer")
async def submit_answer(
    request: ExamSubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an answer to a question"""
    
    # Verify attempt belongs to user
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == request.attempt_id,
        ExamAttempt.user_id == current_user.id,
        ExamAttempt.status == "in_progress"
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found or completed"
        )
    
    # Get question
    question = db.query(ExamQuestion).filter(
        ExamQuestion.id == request.question_id
    ).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check if answer already exists
    existing_response = db.query(ExamResponse).filter(
        ExamResponse.attempt_id == request.attempt_id,
        ExamResponse.question_id == request.question_id
    ).first()
    
    # Grade the answer
    grading_service = GradingService()
    grading_result = await grading_service.grade_response(
        db=db,
        question=question,
        user_answer=request.answer,
        time_taken=request.time_taken_seconds
    )
    
    if existing_response:
        # Update existing response
        existing_response.user_answer = request.answer
        existing_response.is_correct = grading_result["is_correct"]
        existing_response.partial_credit = grading_result["partial_credit"]
        existing_response.points_earned = grading_result["points_earned"]
        existing_response.feedback = grading_result["feedback"]
        existing_response.auto_feedback = grading_result["auto_feedback"]
        existing_response.time_taken_seconds = request.time_taken_seconds
        existing_response.answered_at = datetime.utcnow()
    else:
        # Create new response
        response = ExamResponse(
            attempt_id=request.attempt_id,
            question_id=request.question_id,
            user_answer=request.answer,
            is_correct=grading_result["is_correct"],
            partial_credit=grading_result["partial_credit"],
            points_earned=grading_result["points_earned"],
            feedback=grading_result["feedback"],
            auto_feedback=grading_result["auto_feedback"],
            time_taken_seconds=request.time_taken_seconds
        )
        db.add(response)
    
    db.commit()
    
    return {
        "success": True,
        "is_correct": grading_result["is_correct"],
        "points_earned": grading_result["points_earned"],
        "feedback": grading_result["feedback"],
        "partial_credit": grading_result["partial_credit"]
    }


@router.post("/complete")
async def complete_exam(
    request: ExamCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete an exam and calculate final score"""
    
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == request.attempt_id,
        ExamAttempt.user_id == current_user.id,
        ExamAttempt.status == "in_progress"
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found or already completed"
        )
    
    # Calculate final score
    responses = db.query(ExamResponse).filter(
        ExamResponse.attempt_id == request.attempt_id
    ).all()
    
    total_points = sum(response.points_earned for response in responses)
    
    # Update attempt
    attempt.completed_at = datetime.utcnow()
    attempt.status = "completed"
    attempt.total_points = total_points
    attempt.percentage_score = (total_points / attempt.max_points * 100) if attempt.max_points > 0 else 0
    attempt.time_taken_seconds = int((attempt.completed_at - attempt.started_at).total_seconds())
    
    db.commit()
    
    return {
        "success": True,
        "attempt_id": attempt.id,
        "total_points": total_points,
        "max_points": attempt.max_points,
        "percentage_score": round(attempt.percentage_score, 1),
        "time_taken_seconds": attempt.time_taken_seconds,
        "completed_at": attempt.completed_at.isoformat()
    }


@router.get("/attempt/{attempt_id}/results")
async def get_exam_results(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed results for an exam attempt"""
    
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id,
        ExamAttempt.user_id == current_user.id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found"
        )
    
    # Get all responses
    responses = db.query(ExamResponse).filter(
        ExamResponse.attempt_id == attempt_id
    ).all()
    
    # Format results
    results = []
    for response in responses:
        question = response.question
        result_data = {
            "question_id": question.id,
            "question_type": question.question_type,
            "prompt": question.prompt,
            "user_answer": response.user_answer,
            "correct_answer": question.correct_answer,
            "is_correct": response.is_correct,
            "points_earned": response.points_earned,
            "max_points": question.points,
            "feedback": response.feedback,
            "explanation": question.explanation,
            "time_taken_seconds": response.time_taken_seconds,
            "auto_feedback": response.auto_feedback
        }
        results.append(result_data)
    
    return {
        "attempt_id": attempt.id,
        "exam_title": attempt.exam.title,
        "level": attempt.exam.cefr_level,
        "total_points": attempt.total_points,
        "max_points": attempt.max_points,
        "percentage_score": attempt.percentage_score,
        "time_taken_seconds": attempt.time_taken_seconds,
        "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
        "status": attempt.status,
        "results": results
    }


@router.get("/user/history")
async def get_user_exam_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's exam attempt history"""
    
    query = db.query(ExamAttempt).filter(
        ExamAttempt.user_id == current_user.id
    ).order_by(ExamAttempt.started_at.desc())
    
    total = query.count()
    attempts = query.offset(skip).limit(limit).all()
    
    history = []
    for attempt in attempts:
        attempt_data = {
            "attempt_id": attempt.id,
            "exam_id": attempt.exam.id,
            "exam_title": attempt.exam.title,
            "level": attempt.exam.cefr_level,
            "started_at": attempt.started_at.isoformat(),
            "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
            "status": attempt.status,
            "total_points": attempt.total_points,
            "max_points": attempt.max_points,
            "percentage_score": attempt.percentage_score,
            "time_taken_seconds": attempt.time_taken_seconds
        }
        history.append(attempt_data)
    
    return {
        "attempts": history,
        "total": total,
        "skip": skip,
        "limit": limit
    }