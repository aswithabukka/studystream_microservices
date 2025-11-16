"""
Configuration settings for Notification Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Notification Service"
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/notification_db"
    
    # JWT (for validation)
    jwt_secret_key: str = "your-secret-key-change-in-production-min-32-characters"
    jwt_algorithm: str = "HS256"
    
    # Service URLs
    auth_service_url: str = "http://localhost:8001"
    
    # Email (optional)
    email_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@studystream.com"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
