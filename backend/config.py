from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "DriveLegal"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SHORT: int = 900       # 15 mins (for dynamic RAG results)
    CACHE_TTL_MEDIUM: int = 3600     # 1 hour (for fines lookup)
    CACHE_TTL_LONG: int = 86400      # 24 hours (for static jurisdiction/violations)
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # LLM Configuration
    LLM_PROVIDER: str = "mock"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # App Configuration
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    @model_validator(mode='after')
    def validate_llm_keys(self) -> 'Settings':
        if self.LLM_PROVIDER != 'mock' and not self.GEMINI_API_KEY and not self.OPENAI_API_KEY:
            raise ValueError(f"An API key (GEMINI_API_KEY or OPENAI_API_KEY) must be provided when LLM_PROVIDER is '{self.LLM_PROVIDER}'")
        return self

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
