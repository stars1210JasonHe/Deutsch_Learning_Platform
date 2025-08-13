from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.search import SearchHistoryResponse, SearchStatsResponse
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("/history", response_model=SearchHistoryResponse)
async def get_search_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's search history"""
    
    history, total = await CacheService.get_user_search_history(
        db, current_user, skip, limit
    )
    
    return SearchHistoryResponse(
        items=history,
        total=total
    )


@router.delete("/history/{history_id}")
async def delete_search_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a specific search history item"""
    
    from app.models.search import SearchHistory
    
    history_item = db.query(SearchHistory).filter(
        SearchHistory.id == history_id,
        SearchHistory.user_id == current_user.id
    ).first()
    
    if history_item:
        db.delete(history_item)
        db.commit()
        return {"message": "Search history item deleted"}
    
    return {"message": "History item not found"}


@router.get("/cache/stats", response_model=SearchStatsResponse)
async def get_cache_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get cache statistics (admin only in production)"""
    
    # In production, you might want to restrict this to admin users
    stats = await CacheService.get_cache_stats(db)
    
    return SearchStatsResponse(**stats)