"""
Core Configuration
Settings and environment variable management for the Procurement System.
"""

import os
from typing import List, Optional, Union
from pydantic import BaseModel, validator, Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # =====================================================
    # APPLICATION SETTINGS
    # =====================================================
    APP_NAME: str = Field(default="Procurement System", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=True, env="DEBUG")
    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")
    
    # =====================================================
    # SECURITY SETTINGS
    # =====================================================
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    # =====================================================
    # DATABASE SETTINGS
    # =====================================================
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=0, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    # =====================================================
    # SUPABASE SETTINGS
    # =====================================================
    SUPABASE_URL: Optional[str] = Field(default=None, env="SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None, env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_ROLE_KEY")
    
    # =====================================================
    # CORS SETTINGS
    # =====================================================
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # =====================================================
    # MULTI-TENANT SETTINGS
    # =====================================================
    DEFAULT_UNIT_CODE: str = Field(default="HOTEL001", env="DEFAULT_UNIT_CODE")
    MAX_UNITS: int = Field(default=8, env="MAX_UNITS")
    
    # =====================================================
    # LOGGING SETTINGS
    # =====================================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    # =====================================================
    # API DOCUMENTATION SETTINGS
    # =====================================================
    ENABLE_DOCS: bool = Field(default=True, env="ENABLE_DOCS")
    ENABLE_REDOC: bool = Field(default=True, env="ENABLE_REDOC")
    
    # =====================================================
    # EMAIL SETTINGS (for notifications)
    # =====================================================
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    SMTP_PORT: Optional[int] = Field(default=None, env="SMTP_PORT")
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[str] = Field(default=None, env="EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = Field(default=None, env="EMAILS_FROM_NAME")
    
    # =====================================================
    # PAGINATION SETTINGS
    # =====================================================
    DEFAULT_PAGE_SIZE: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    MAX_PAGE_SIZE: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    @validator("DEFAULT_PAGE_SIZE")
    def validate_default_page_size(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("DEFAULT_PAGE_SIZE must be between 1 and 100")
        return v
    
    @validator("MAX_PAGE_SIZE")
    def validate_max_page_size(cls, v):
        if v <= 0 or v > 1000:
            raise ValueError("MAX_PAGE_SIZE must be between 1 and 1000")
        return v
    
    # =====================================================
    # FILE UPLOAD SETTINGS
    # =====================================================
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["pdf", "jpg", "jpeg", "png", "xlsx", "csv"],
        env="ALLOWED_EXTENSIONS"
    )
    UPLOAD_DIRECTORY: str = Field(default="uploads", env="UPLOAD_DIRECTORY")
    
    # =====================================================
    # CACHE SETTINGS
    # =====================================================
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")  # 5 minutes
    
    # =====================================================
    # BUSINESS LOGIC SETTINGS
    # =====================================================
    LOW_STOCK_THRESHOLD_DAYS: int = Field(default=7, env="LOW_STOCK_THRESHOLD_DAYS")
    REORDER_LEAD_TIME_DAYS: int = Field(default=14, env="REORDER_LEAD_TIME_DAYS")
    DEFAULT_SUPPLIER_RATING: float = Field(default=5.0, env="DEFAULT_SUPPLIER_RATING")
    
    # =====================================================
    # COMPUTED PROPERTIES
    # =====================================================
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG
    
    @property
    def postgres_dsn(self) -> str:
        """Get PostgreSQL connection string."""
        return self.DATABASE_URL
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return self.BACKEND_CORS_ORIGINS
    
    @property
    def smtp_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return all([
            self.SMTP_HOST,
            self.SMTP_PORT,
            self.SMTP_USER,
            self.SMTP_PASSWORD
        ])
    
    @property
    def redis_configured(self) -> bool:
        """Check if Redis is configured."""
        return self.REDIS_URL is not None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # Example values for documentation
        json_schema_extra = {
            "example": {
                "APP_NAME": "Procurement System",
                "DEBUG": True,
                "SECRET_KEY": "super-secret-key-min-32-chars-long",
                "DATABASE_URL": "postgresql://postgres:password@localhost/procurement_db",
                "BACKEND_CORS_ORIGINS": ["http://localhost:3000", "http://localhost:8080"],
                "LOG_LEVEL": "INFO"
            }
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    This function uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()


# Development helper function
def print_settings():
    """Print non-sensitive settings for debugging."""
    if settings.DEBUG:
        print("=== Application Settings ===")
        print(f"App Name: {settings.APP_NAME}")
        print(f"Version: {settings.APP_VERSION}")
        print(f"Debug Mode: {settings.DEBUG}")
        print(f"API Prefix: {settings.API_V1_STR}")
        print(f"Log Level: {settings.LOG_LEVEL}")
        print(f"Database URL: {settings.DATABASE_URL[:50]}...")
        print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
        print(f"Default Unit: {settings.DEFAULT_UNIT_CODE}")
        print(f"Max Units: {settings.MAX_UNITS}")
        print(f"Docs Enabled: {settings.ENABLE_DOCS}")
        print(f"SMTP Configured: {settings.smtp_configured}")
        print(f"Redis Configured: {settings.redis_configured}")
        print("===========================")


if __name__ == "__main__":
    # For testing configuration
    print_settings()