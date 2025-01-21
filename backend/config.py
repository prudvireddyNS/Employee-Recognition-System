from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///attendance.db"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        SECRET_KEY = os.urandom(32).hex()
        
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Reduced to 30 minutes for security
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MINIMUM_PASSWORD_LENGTH: int = 8
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_ATTEMPTS_WINDOW: int = 15  # minutes
    
    # JWT Settings
    JWT_AUDIENCE: str = "employee-recognition-api"
    JWT_ISSUER: str = "employee-recognition-system"
    
    API_V1_PREFIX: str = "/api/v1"
    TOKEN_URL: str = f"{API_V1_PREFIX}/admin/login"
    
    # Face Recognition
    FACE_DETECTION_THRESHOLD: float = 0.6
    FACE_RECOGNITION_THRESHOLD: float = 0.7
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Cors
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173/"]
    
    # Redis (for caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
