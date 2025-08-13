import hashlib
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models.search import SearchCache, SearchHistory
from app.models.user import User


class CacheService:
    @staticmethod
    def generate_cache_key(query_text: str, query_type: str) -> str:
        """Generate MD5 hash for cache lookup"""
        cache_input = f"{query_text.lower().strip()}:{query_type}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    @staticmethod
    async def get_cached_response(
        db: Session, 
        query_text: str, 
        query_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if exists"""
        cache_key = CacheService.generate_cache_key(query_text, query_type)
        
        cached_result = db.query(SearchCache).filter(
            SearchCache.query_hash == cache_key
        ).first()
        
        if cached_result:
            # Update hit count and last accessed
            cached_result.hit_count += 1
            cached_result.last_accessed = func.now()
            db.commit()
            
            return cached_result.response_json
        
        return None

    @staticmethod
    async def cache_response(
        db: Session,
        query_text: str,
        query_type: str,
        response_data: Dict[str, Any]
    ) -> int:
        """Cache OpenAI response"""
        cache_key = CacheService.generate_cache_key(query_text, query_type)
        
        # Check if already exists
        existing = db.query(SearchCache).filter(
            SearchCache.query_hash == cache_key
        ).first()
        
        if existing:
            return existing.id
        
        # Create new cache entry
        cache_entry = SearchCache(
            query_text=query_text.strip(),
            query_type=query_type,
            query_hash=cache_key,
            response_json=response_data,
            hit_count=1
        )
        
        db.add(cache_entry)
        db.commit()
        db.refresh(cache_entry)
        
        return cache_entry.id

    @staticmethod
    async def log_search_history(
        db: Session,
        user: User,
        query_text: str,
        query_type: str,
        cached_result_id: Optional[int] = None
    ):
        """Log user search history"""
        history_entry = SearchHistory(
            user_id=user.id,
            query_text=query_text.strip(),
            query_type=query_type,
            cached_result_id=cached_result_id
        )
        
        db.add(history_entry)
        db.commit()

    @staticmethod
    async def get_user_search_history(
        db: Session, 
        user: User, 
        skip: int = 0, 
        limit: int = 50
    ):
        """Get user's search history"""
        history = db.query(SearchHistory).filter(
            SearchHistory.user_id == user.id
        ).order_by(SearchHistory.timestamp.desc()).offset(skip).limit(limit).all()
        
        total = db.query(SearchHistory).filter(
            SearchHistory.user_id == user.id
        ).count()
        
        return history, total

    @staticmethod
    async def get_cache_stats(db: Session) -> Dict[str, Any]:
        """Get cache statistics"""
        total_searches = db.query(SearchHistory).count()
        total_cached = db.query(SearchCache).count()
        
        # Popular searches (top 10 by hit count)
        popular = db.query(SearchCache).order_by(
            SearchCache.hit_count.desc()
        ).limit(10).all()
        
        # Recent searches (last 10)
        recent = db.query(SearchCache).order_by(
            SearchCache.created_at.desc()
        ).limit(10).all()
        
        cache_hit_rate = (total_cached / total_searches * 100) if total_searches > 0 else 0
        
        return {
            "total_searches": total_searches,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "popular_searches": [
                {"query": item.query_text, "hits": item.hit_count} 
                for item in popular
            ],
            "recent_searches": [
                {"query": item.query_text, "type": item.query_type} 
                for item in recent
            ]
        }