"""
Configuration settings for User Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "User Service"
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/user_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/1"
    cache_ttl_seconds: int = 300  # 5 minutes
    
    # JWT (for validation)
    jwt_secret_key: str = "your-secret-key-change-in-production-min-32-characters"
    jwt_algorithm: str = "HS256"
    
    # Service URLs
    auth_service_url: str = "http://localhost:8001"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
