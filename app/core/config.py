from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr

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
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    JWT_ALGORITHM: str = "HS256"
    
    # Email / SMTP
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_USE_TLS: bool = True
    SMTP_FROM_NAME: str
    SMTP_FROM_EMAIL: EmailStr
    CEO_EMAIL: EmailStr
    
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
            raise ValueError("POSTGRES_URL environment variable is missing. A valid PostgreSQL database is required in production.")
            
        return "sqlite+aiosqlite:///./local_test.db"
    

    # Administrator Seed
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    
    # Config object to tell Pydantic to read from the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

# We instantiate the settings once here. 
# Other modules will import this singleton `settings` object.
settings = Settings()
