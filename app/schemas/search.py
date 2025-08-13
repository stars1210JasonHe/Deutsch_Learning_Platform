from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SearchHistoryItem(BaseModel):
    id: int
    query_text: str
    query_type: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SearchHistoryResponse(BaseModel):
    items: List[SearchHistoryItem]
    total: int


class SearchStatsResponse(BaseModel):
    total_searches: int
    cache_hit_rate: float
    popular_searches: List[dict]
    recent_searches: List[dict]