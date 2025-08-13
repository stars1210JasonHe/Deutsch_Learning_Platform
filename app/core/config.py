from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Database
    database_url: str = "sqlite:///./data/app.db"
    
    # Security
    secret_key: str = "default-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_hosts: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Development
    debug: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env file


settings = Settings()