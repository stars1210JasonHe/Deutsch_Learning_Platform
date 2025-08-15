from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.search import WordList, WordListItem
from app.models.word import WordLemma
from app.services.vocabulary_service import VocabularyService

router = APIRouter()
vocabulary_service = VocabularyService()

@router.get("/", response_model=List[dict])
async def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's favorites list"""
    
    # Get or create the favorites list
    favorites_list = db.query(WordList).filter(
        WordList.user_id == current_user.id,
        WordList.name == "Favorites"
    ).first()
    
    if not favorites_list:
        favorites_list = WordList(
            user_id=current_user.id,
            name="Favorites",
            description="My favorite words"
        )
        db.add(favorites_list)
        db.commit()
        db.refresh(favorites_list)
    
    # Get all items in favorites list
    items = db.query(WordListItem).filter(
        WordListItem.list_id == favorites_list.id
    ).join(WordLemma).all()
    
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "lemma": item.lemma.lemma,
            "pos": item.lemma.pos,
            "cefr": item.lemma.cefr,
            "added_at": item.added_at
        })
    
    return result


@router.post("/add/{lemma}")
async def add_to_favorites(
    lemma: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a word to favorites"""
    
    # Get or create the favorites list
    favorites_list = db.query(WordList).filter(
        WordList.user_id == current_user.id,
        WordList.name == "Favorites"
    ).first()
    
    if not favorites_list:
        favorites_list = WordList(
            user_id=current_user.id,
            name="Favorites",
            description="My favorite words"
        )
        db.add(favorites_list)
        db.commit()
        db.refresh(favorites_list)
    
    # Get or create the word lemma
    word_lemma = db.query(WordLemma).filter(WordLemma.lemma == lemma).first()
    if not word_lemma:
        # Create basic word entry - this will be enhanced when the user searches for it
        word_lemma = WordLemma(lemma=lemma)
        db.add(word_lemma)
        db.commit()
        db.refresh(word_lemma)
    
    # Check if already in favorites
    existing_item = db.query(WordListItem).filter(
        WordListItem.list_id == favorites_list.id,
        WordListItem.lemma_id == word_lemma.id
    ).first()
    
    if existing_item:
        raise HTTPException(status_code=400, detail="Word already in favorites")
    
    # Add to favorites
    new_item = WordListItem(
        list_id=favorites_list.id,
        lemma_id=word_lemma.id
    )
    db.add(new_item)
    db.commit()
    
    return {"success": True, "message": f"'{lemma}' added to favorites"}


@router.delete("/remove/{lemma}")
async def remove_from_favorites(
    lemma: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a word from favorites"""
    
    # Get the favorites list
    favorites_list = db.query(WordList).filter(
        WordList.user_id == current_user.id,
        WordList.name == "Favorites"
    ).first()
    
    if not favorites_list:
        raise HTTPException(status_code=404, detail="Favorites list not found")
    
    # Get the word lemma
    word_lemma = db.query(WordLemma).filter(WordLemma.lemma == lemma).first()
    if not word_lemma:
        raise HTTPException(status_code=404, detail="Word not found")
    
    # Find and remove the item
    item = db.query(WordListItem).filter(
        WordListItem.list_id == favorites_list.id,
        WordListItem.lemma_id == word_lemma.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Word not in favorites")
    
    db.delete(item)
    db.commit()
    
    return {"success": True, "message": f"'{lemma}' removed from favorites"}


@router.get("/check/{lemma}")
async def check_if_favorite(
    lemma: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check if a word is in favorites"""
    
    # Get the favorites list
    favorites_list = db.query(WordList).filter(
        WordList.user_id == current_user.id,
        WordList.name == "Favorites"
    ).first()
    
    if not favorites_list:
        return {"is_favorite": False}
    
    # Get the word lemma
    word_lemma = db.query(WordLemma).filter(WordLemma.lemma == lemma).first()
    if not word_lemma:
        return {"is_favorite": False}
    
    # Check if in favorites
    item = db.query(WordListItem).filter(
        WordListItem.list_id == favorites_list.id,
        WordListItem.lemma_id == word_lemma.id
    ).first()
    
    return {"is_favorite": bool(item)}