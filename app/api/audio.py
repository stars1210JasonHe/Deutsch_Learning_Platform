"""
Audio API Endpoints - Serve German learning audio files
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services.audio_service import AudioService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio", tags=["audio"])


# Pydantic models
class AudioFileInfo(BaseModel):
    file_id: str
    filename: str
    course: str
    relative_path: str
    size: int
    chapter: Optional[int] = None
    lesson: Optional[int] = None
    lesson_code: Optional[str] = None


class AudioStats(BaseModel):
    total_files: int
    total_courses: int
    total_size_mb: float
    cached_files: int
    courses: Dict[str, int]
    last_indexed: str


class AudioSearchRequest(BaseModel):
    query: str


# Audio management endpoints
@router.post("/rebuild-index")
async def rebuild_audio_index(
    current_user: User = Depends(get_current_user)
):
    """Rebuild audio file index from NAS"""
    
    audio_service = AudioService()
    
    try:
        index_data = audio_service.build_audio_index()
        
        return {
            "success": True,
            "message": "Audio index rebuilt successfully",
            "stats": {
                "total_files": index_data["total_files"],
                "total_courses": index_data["total_courses"],
                "generated_at": index_data["generated_at"]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to rebuild audio index: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebuild audio index: {str(e)}"
        )


@router.get("/stats")
async def get_audio_stats(
    current_user: User = Depends(get_current_user)
) -> AudioStats:
    """Get audio library statistics"""
    
    audio_service = AudioService()
    stats = audio_service.get_audio_stats()
    
    if "error" in stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=stats["error"]
        )
        
    return AudioStats(**stats)


@router.get("/courses")
async def list_courses(
    current_user: User = Depends(get_current_user)
):
    """List all available audio courses"""
    
    audio_service = AudioService()
    index = audio_service.get_audio_index()
    
    if not index:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audio index found. Please rebuild the index first."
        )
    
    courses = []
    for course_name, course_data in index["courses"].items():
        courses.append({
            "name": course_name,
            "audio_count": course_data["audio_count"],
            "chapters": list(course_data["chapters"].keys()) if course_data["chapters"] else []
        })
    
    return {
        "courses": courses,
        "total": len(courses)
    }


@router.get("/courses/{course_name}")
async def get_course_audio_files(
    course_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get all audio files for a specific course"""
    
    audio_service = AudioService()
    files = audio_service.get_course_audio_files(course_name)
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audio files found for course: {course_name}"
        )
    
    return {
        "course": course_name,
        "files": files,
        "count": len(files)
    }


@router.get("/courses/{course_name}/chapters/{chapter}")
async def get_chapter_audio_files(
    course_name: str,
    chapter: int,
    current_user: User = Depends(get_current_user)
):
    """Get audio files for a specific chapter"""
    
    audio_service = AudioService()
    files = audio_service.get_chapter_audio_files(course_name, chapter)
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audio files found for {course_name} chapter {chapter}"
        )
    
    # Sort by lesson number if available
    files.sort(key=lambda x: x.get('lesson', 0))
    
    return {
        "course": course_name,
        "chapter": chapter,
        "files": files,
        "count": len(files)
    }


@router.post("/search")
async def search_audio_files(
    request: AudioSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Search audio files by filename or course name"""
    
    audio_service = AudioService()
    results = audio_service.search_audio_files(request.query)
    
    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }


# Audio serving endpoints
@router.get("/play/{file_id}")
async def serve_audio_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Serve audio file for playback directly from NAS"""
    
    audio_service = AudioService()
    index = audio_service.get_audio_index()
    
    if not index:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio index not found. Please rebuild the index first."
        )
    
    # Find the file by ID
    target_file = None
    for course in index["courses"].values():
        for audio_file in course["files"]:
            if audio_file["file_id"] == file_id:
                target_file = audio_file
                break
        if target_file:
            break
    
    if not target_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file not found: {file_id}"
        )
    
    # Get direct path to file
    file_path = target_file["nas_path"]
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file not accessible: {file_path}"
        )
    
    # Determine media type based on file extension
    media_types = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4',
        '.flac': 'audio/flac'
    }
    
    file_ext = '.' + target_file["filename"].split('.')[-1].lower()
    media_type = media_types.get(file_ext, 'application/octet-stream')
    
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
    )


@router.get("/download/{file_id}")
async def download_audio_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download audio file"""
    
    audio_service = AudioService()
    
    # Get file info for original filename
    index = audio_service.get_audio_index()
    if not index:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio index not found"
        )
    
    # Find original filename
    original_filename = None
    for course in index["courses"].values():
        for audio_file in course["files"]:
            if audio_file["file_id"] == file_id:
                original_filename = audio_file["filename"]
                break
        if original_filename:
            break
    
    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file not found: {file_id}"
        )
    
    # Get cached file
    cached_path = audio_service.get_cached_audio_path(file_id)
    if not cached_path:
        cached_path = audio_service.cache_audio_file(file_id)
        
    if not cached_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file not available: {file_id}"
        )
    
    return FileResponse(
        cached_path,
        filename=original_filename,
        headers={"Content-Disposition": f"attachment; filename={original_filename}"}
    )


@router.get("/info/{file_id}")
async def get_audio_file_info(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about an audio file"""
    
    audio_service = AudioService()
    index = audio_service.get_audio_index()
    
    if not index:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio index not found"
        )
    
    # Find file info
    for course in index["courses"].values():
        for audio_file in course["files"]:
            if audio_file["file_id"] == file_id:
                # Check if file is cached
                cached_path = audio_service.get_cached_audio_path(file_id)
                
                return {
                    **audio_file,
                    "is_cached": cached_path is not None,
                    "play_url": f"/audio/play/{file_id}",
                    "download_url": f"/audio/download/{file_id}"
                }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Audio file not found: {file_id}"
    )


# Utility endpoints
@router.delete("/cache/{file_id}")
async def clear_audio_cache(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Clear cached audio file"""
    
    audio_service = AudioService()
    cached_path = audio_service.get_cached_audio_path(file_id)
    
    if cached_path:
        try:
            import os
            os.remove(cached_path)
            return {"success": True, "message": "Cache cleared"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear cache: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not in cache"
        )