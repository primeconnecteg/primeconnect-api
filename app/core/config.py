from typing import Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, field_validator

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables or .env file.
    Pydantic will automatically validate these types when the app starts.
    """
    
    # Application Core
    PROJECT_NAME: str = "PrimeConnect API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "https://primeconnecteg.com",
        "https://www.primeconnecteg.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:4173",
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return [
            "https://primeconnecteg.com",
            "https://www.primeconnecteg.com",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:4173",
        ]
    
    # Security
    SECRET_KEY: str = "default_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    JWT_ALGORITHM: str = "HS256"
    
    # Email / SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_FROM_NAME: str = "PrimeConnect"
    SMTP_FROM_EMAIL: str = "info@primeconnecteg.com"
    CEO_EMAIL: str = "info@primeconnecteg.com"
    
    # Environment Config
    ENVIRONMENT: str = "development"
    
    # Database
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "pass"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "db"
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Dynamically constructs the database connection string.
        Uses Vercel Postgres in production, falls back to SQLite locally.
        """
        import os
        import logging
        
        # Vercel Postgres typically uses POSTGRES_URL, while Render/Railway use DATABASE_URL
        db_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
        
        if db_url:
            # SQLAlchemy asyncpg requires postgresql+asyncpg:// instead of postgres://
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgresql://") and "asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return db_url
            
        is_production = self.ENVIRONMENT == "production" or os.getenv("VERCEL_ENV") == "production"
        if is_production:
            logging.getLogger("uvicorn").warning(
                "POSTGRES_URL environment variable is missing in production. Falling back to SQLite."
            )
            
        return "sqlite+aiosqlite:///./local_test.db"
    

    # Administrator Seed
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    
    # Config object to tell Pydantic to read from the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# We instantiate the settings once here. 
# Other modules will import this singleton `settings` object.
settings = Settings()
