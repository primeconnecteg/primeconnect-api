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
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
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
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Dynamically constructs the database connection string.
        We use postgresql+asyncpg for asynchronous database operations.
        """
        import urllib.parse
        encoded_password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    

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
