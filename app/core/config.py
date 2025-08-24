from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets
import sys


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
    
    # Separate OpenAI configuration for exam generation
    openai_exam_api_key: Optional[str] = None  # Direct OpenAI API key for exams
    openai_exam_base_url: Optional[str] = None  # For exam generation (defaults to direct OpenAI)
    
    # Database
    database_url: str = "sqlite:///./data/app.db"
    
    # Security
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 24 * 60  # 24 hours
    refresh_token_expire_days: int = 30  # 30 days
    remember_me_expire_days: int = 90  # 90 days for "remember me"
    
    # CORS - Default development hosts
    allowed_hosts: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3001", "http://127.0.0.1:3001"]
    
    # Additional CORS configuration via environment variable
    additional_allowed_hosts: Optional[str] = None  # Comma-separated list of additional hosts
    
    # Deployment Configuration
    debug: bool = False
    https_only: bool = False  # Set to True for production HTTPS deployments
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env file


# Initialize settings
_settings = Settings()

# Validate and secure secret key
def _get_secure_secret_key() -> str:
    """Get or generate a secure secret key with proper validation."""
    
    # Try to get from environment variable first
    secret_key = _settings.secret_key or os.getenv("SECRET_KEY")
    
    if secret_key:
        # Validate minimum security requirements
        if len(secret_key) < 32:
            print("WARNING: SECRET_KEY is too short (minimum 32 characters required)")
            print("This is a security risk in production!")
        
        # Check if it's still the default value
        if secret_key == "default-secret-key-change-in-production":
            if os.getenv("ENVIRONMENT") == "production":
                print("CRITICAL SECURITY ERROR: Default secret key detected in production!")
                print("Set a secure SECRET_KEY environment variable immediately.")
                sys.exit(1)
            else:
                print("WARNING: Using default secret key in development mode")
                print("Set SECRET_KEY environment variable for production")
        
        return secret_key
    
    # Generate a secure key for development if none provided
    if os.getenv("ENVIRONMENT") != "production":
        print("INFO: No SECRET_KEY found, generating secure key for development")
        return secrets.token_urlsafe(32)
    else:
        print("CRITICAL ERROR: SECRET_KEY environment variable must be set in production!")
        print("Example: export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')")
        sys.exit(1)

# Create final settings object with secure secret key and merged CORS hosts
class SecureSettings(Settings):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.secret_key = _get_secure_secret_key()
        
        # Merge additional allowed hosts from environment
        if self.additional_allowed_hosts:
            additional_hosts = [host.strip() for host in self.additional_allowed_hosts.split(',') if host.strip()]
            self.allowed_hosts.extend(additional_hosts)
            # Remove duplicates while preserving order
            self.allowed_hosts = list(dict.fromkeys(self.allowed_hosts))

settings = SecureSettings()