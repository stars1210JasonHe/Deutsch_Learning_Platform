"""
Audio Service - Manage German learning audio files from NAS
"""
import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import hashlib
import json
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioService:
    def __init__(self):
        # For NAS deployment, audio files will be mounted as volume
        self.audio_base_path = os.environ.get("AUDIO_PATH", "/app/audio")
        self.fallback_nas_path = "//DS420plus/homes/德语学习"  # Fallback for development
        
        # Use data directory for index file only
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audio_index_file = self.data_dir / "audio_index.json"
        
        # Determine actual audio path
        self.nas_audio_path = (
            self.audio_base_path if os.path.exists(self.audio_base_path) 
            else self.fallback_nas_path
        )
        
        # Supported audio formats
        self.supported_formats = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
        
    def get_nas_audio_files(self) -> List[Dict[str, Any]]:
        """Scan NAS for all audio files and return structured information"""
        audio_files = []
        
        try:
            for root, dirs, files in os.walk(self.nas_audio_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in self.supported_formats):
                        full_path = os.path.join(root, file)
                        relative_path = os.path.relpath(full_path, self.nas_audio_path)
                        
                        # Parse course and lesson info from path
                        path_parts = relative_path.split(os.sep)
                        course = path_parts[0] if len(path_parts) > 0 else "Unknown"
                        
                        audio_info = {
                            "filename": file,
                            "nas_path": full_path,
                            "relative_path": relative_path,
                            "course": course,
                            "size": self._get_file_size_safe(full_path),
                            "file_id": self._generate_file_id(relative_path),
                            "last_modified": self._get_modification_time(full_path)
                        }
                        
                        # Try to extract lesson/chapter info from filename
                        lesson_info = self._parse_lesson_info(file)
                        if lesson_info:
                            audio_info.update(lesson_info)
                            
                        audio_files.append(audio_info)
                        
        except Exception as e:
            logger.error(f"Error scanning NAS audio files: {e}")
            
        return audio_files
    
    def _generate_file_id(self, relative_path: str) -> str:
        """Generate unique ID for audio file"""
        return hashlib.md5(relative_path.encode()).hexdigest()[:16]
    
    def _get_file_size_safe(self, file_path: str) -> int:
        """Get file size safely"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    def _get_modification_time(self, file_path: str) -> str:
        """Get file modification time"""
        try:
            mtime = os.path.getmtime(file_path)
            return datetime.fromtimestamp(mtime).isoformat()
        except:
            return datetime.now().isoformat()
    
    def _parse_lesson_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Parse lesson information from filename"""
        # Examples: 1-01.mp3, 2-05.mp3, etc.
        name_without_ext = os.path.splitext(filename)[0]
        
        # Pattern: chapter-lesson (e.g., "1-01")
        if '-' in name_without_ext and len(name_without_ext.split('-')) == 2:
            try:
                chapter, lesson = name_without_ext.split('-')
                return {
                    "chapter": int(chapter),
                    "lesson": int(lesson),
                    "lesson_code": name_without_ext
                }
            except ValueError:
                pass
                
        return None
    
    def build_audio_index(self) -> Dict[str, Any]:
        """Build comprehensive audio index"""
        logger.info("Building audio index from NAS...")
        
        audio_files = self.get_nas_audio_files()
        
        # Group by course
        courses = {}
        for audio in audio_files:
            course_name = audio['course']
            if course_name not in courses:
                courses[course_name] = {
                    "name": course_name,
                    "audio_count": 0,
                    "chapters": {},
                    "files": []
                }
            
            courses[course_name]["audio_count"] += 1
            courses[course_name]["files"].append(audio)
            
            # Group by chapter if available
            if "chapter" in audio:
                chapter = audio["chapter"]
                if chapter not in courses[course_name]["chapters"]:
                    courses[course_name]["chapters"][chapter] = []
                courses[course_name]["chapters"][chapter].append(audio)
        
        index_data = {
            "generated_at": datetime.now().isoformat(),
            "total_files": len(audio_files),
            "total_courses": len(courses),
            "courses": courses
        }
        
        # Save index to local file
        try:
            with open(self.audio_index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Audio index saved: {len(audio_files)} files from {len(courses)} courses")
        except Exception as e:
            logger.error(f"Failed to save audio index: {e}")
            
        return index_data
    
    def get_audio_index(self) -> Optional[Dict[str, Any]]:
        """Get cached audio index"""
        try:
            if self.audio_index_file.exists():
                with open(self.audio_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load audio index: {e}")
        return None
    
    def cache_audio_file(self, file_id: str) -> Optional[str]:
        """Cache an audio file locally for serving"""
        index = self.get_audio_index()
        if not index:
            logger.error("No audio index available")
            return None
            
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
            logger.error(f"Audio file not found: {file_id}")
            return None
            
        # Create local cache path
        cache_filename = f"{file_id}_{target_file['filename']}"
        local_cache_path = self.local_audio_dir / cache_filename
        
        # Copy file if not already cached
        if not local_cache_path.exists():
            try:
                shutil.copy2(target_file["nas_path"], local_cache_path)
                logger.info(f"Cached audio file: {cache_filename}")
            except Exception as e:
                logger.error(f"Failed to cache audio file {file_id}: {e}")
                return None
                
        return str(local_cache_path)
    
    def get_cached_audio_path(self, file_id: str) -> Optional[str]:
        """Get path to cached audio file"""
        index = self.get_audio_index()
        if not index:
            return None
            
        # Find filename by ID
        target_filename = None
        for course in index["courses"].values():
            for audio_file in course["files"]:
                if audio_file["file_id"] == file_id:
                    target_filename = audio_file['filename']
                    break
            if target_filename:
                break
                
        if not target_filename:
            return None
            
        cache_filename = f"{file_id}_{target_filename}"
        local_cache_path = self.local_audio_dir / cache_filename
        
        return str(local_cache_path) if local_cache_path.exists() else None
    
    def get_course_audio_files(self, course_name: str) -> List[Dict[str, Any]]:
        """Get all audio files for a specific course"""
        index = self.get_audio_index()
        if not index or course_name not in index["courses"]:
            return []
            
        return index["courses"][course_name]["files"]
    
    def get_chapter_audio_files(self, course_name: str, chapter: int) -> List[Dict[str, Any]]:
        """Get audio files for a specific chapter"""
        index = self.get_audio_index()
        if not index or course_name not in index["courses"]:
            return []
            
        chapters = index["courses"][course_name]["chapters"]
        return chapters.get(str(chapter), [])
    
    def search_audio_files(self, query: str) -> List[Dict[str, Any]]:
        """Search audio files by filename or course"""
        index = self.get_audio_index()
        if not index:
            return []
            
        results = []
        query_lower = query.lower()
        
        for course in index["courses"].values():
            for audio_file in course["files"]:
                if (query_lower in audio_file["filename"].lower() or
                    query_lower in audio_file["course"].lower()):
                    results.append(audio_file)
                    
        return results
    
    def get_audio_stats(self) -> Dict[str, Any]:
        """Get audio library statistics"""
        index = self.get_audio_index()
        if not index:
            return {"error": "No audio index available"}
            
        # Calculate total size
        total_size = 0
        for course in index["courses"].values():
            for audio_file in course["files"]:
                total_size += audio_file.get("size", 0)
                
        # Count cached files
        cached_files = len(list(self.local_audio_dir.glob("*_*.mp3")))
        
        return {
            "total_files": index["total_files"],
            "total_courses": index["total_courses"],
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cached_files": cached_files,
            "courses": {name: data["audio_count"] for name, data in index["courses"].items()},
            "last_indexed": index["generated_at"]
        }