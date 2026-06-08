import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEMSAS API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str
    
    # JWT Settings
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30 # 30 days
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Redis Settings
    REDIS_HOST: str = "localhost" 
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_USERNAME: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False 
    
    # Firebase Settings
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = None # Path to service account json
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None # Raw JSON string of service account for production

    # Upload Provider Settings
    UPLOAD_PROVIDER: str = "local"

    # Cloudinary Settings
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    # SMTP / Email Settings
    EMAIL_HOST: str = "mail.privateemail.com"
    EMAIL_HOST_USER: str = "demo@sydanitechnologies.com"
    EMAIL_HOST_PASSWORD: str = "@StechDemo887"
    EMAIL_PORT: int = 587
    EMAIL_USE_TLS: bool = True
    EMAILS_FROM_EMAIL: str = "demo@sydanitechnologies.com"

    # Email Provider Toggle: "default" (SMTP) or "brevo" (Brevo API)
    EMAIL_PROVIDER: str = "default"

    # Brevo (Sendinblue) API Settings
    BREVO_API_KEY: Optional[str] = None
    BREVO_SENDER_EMAIL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
