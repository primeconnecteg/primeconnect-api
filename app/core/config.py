import os
import logging
import urllib.parse
from typing import Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, field_validator

logger = logging.getLogger(__name__)

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
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
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
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://localhost:5173",
            "http://localhost:4173",
        ]
    
    # Security
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    JWT_ALGORITHM: str = "HS256"
    
    # Email / SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "testprimeconnect@gmail.com"
    SMTP_PASSWORD: str = "fjbk zewz bain szjl"
    SMTP_USE_TLS: bool = True
    SMTP_FROM_NAME: str = "PrimeConnect"
    SMTP_FROM_EMAIL: str = "testprimeconnect@gmail.com"
    CEO_EMAIL: str = "testprimeconnect@gmail.com"
    
    # Environment Config
    ENVIRONMENT: str = "development"
    
    # Database
    POSTGRES_USER: str = "postgres.roojvxjqxdiulycpqzrt"
    POSTGRES_PASSWORD: str = "Admin#@2@26#"
    POSTGRES_SERVER: str = "aws-0-eu-north-1.pooler.supabase.com"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "postgres"
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Dynamically constructs the database connection string.
        Supports full POSTGRES_URL/DATABASE_URL or individual POSTGRES_* environment variables.
        URL-encodes the password to support special characters safely.
        """
        # 1. Direct connection string check
        db_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
        
        # 2. Individual POSTGRES_* environment variables check
        if not db_url:
            user = os.getenv("POSTGRES_USER") or self.POSTGRES_USER
            password = os.getenv("POSTGRES_PASSWORD") or self.POSTGRES_PASSWORD
            server = os.getenv("POSTGRES_SERVER") or self.POSTGRES_SERVER
            port = os.getenv("POSTGRES_PORT") or self.POSTGRES_PORT
            db = os.getenv("POSTGRES_DB") or self.POSTGRES_DB
            
            # If explicit POSTGRES_SERVER or user/db env vars are set
            has_pg_env = bool(
                os.getenv("POSTGRES_SERVER") or 
                os.getenv("POSTGRES_USER") or 
                os.getenv("POSTGRES_DB") or 
                os.getenv("POSTGRES_PASSWORD")
            )
            
            if has_pg_env or (server and server != "localhost"):
                encoded_password = urllib.parse.quote_plus(password) if password else ""
                db_url = f"postgresql+asyncpg://{user}:{encoded_password}@{server}:{port}/{db}"

        if db_url:
            # SQLAlchemy asyncpg requires postgresql+asyncpg:// instead of postgres://
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgresql://") and "asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return db_url
            
        is_production = self.ENVIRONMENT == "production" or os.getenv("VERCEL_ENV") in ("production", "preview")
        if is_production:
            logger.warning(
                "Neither POSTGRES_URL nor POSTGRES_* environment variables were set in production. Falling back to SQLite."
            )
            
        return "sqlite+aiosqlite:///./local_test.db"
    

    # Administrator Seed
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin#@2@26#"
    
    # Config object to tell Pydantic to read from the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# Instantiate settings singleton with logging
logger.info("Loading application settings...")
settings = Settings()
logger.info(f"Settings loaded successfully for project '{settings.PROJECT_NAME}' in '{settings.ENVIRONMENT}' environment.")
