from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"  # Default model
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Separate OpenAI configuration for image generation
    openai_image_api_key: Optional[str] = None  # Direct OpenAI API key for images
    openai_image_base_url: Optional[str] = None  # For image generation (defaults to direct OpenAI)
    
    # Feature-specific models (optional, falls back to openai_model if not set)
    openai_chat_model: Optional[str] = None  # For chat conversations
    openai_analysis_model: Optional[str] = None  # For word analysis
    openai_translation_model: Optional[str] = None  # For translations
    openai_exam_model: Optional[str] = None  # For exam generation
    openai_image_model: Optional[str] = None  # For image generation (DALL-E)
    
    # Database
    database_url: str = "sqlite:///./data/app.db"
    
    # Security
    secret_key: str = "default-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 24 * 60  # 24 hours
    refresh_token_expire_days: int = 30  # 30 days
    remember_me_expire_days: int = 90  # 90 days for "remember me"
    
    # CORS
    allowed_hosts: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]
    
    # Development
    debug: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env file


settings = Settings()