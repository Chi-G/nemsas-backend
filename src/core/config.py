import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEMSAS Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # External Integrations
    FRONTEND_URL: str = "https://nemsas.gov.ng"
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    SMS_GATEWAY_API_KEY: Optional[str] = None
    USSD_GATEWAY_API_KEY: Optional[str] = None
    
    # Mail
    MAIL_SERVER: str = "sandbox.smtp.mailtrap.io"
    MAIL_PORT: int = 2525
    MAIL_USERNAME: Optional[str] = "1728f8f3c42417"
    MAIL_PASSWORD: Optional[str] = "50ac7520cb7c8c"
    MAIL_FROM: str = "noreply@nemsas.gov.ng"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    
    # Rates
    BLS_FIXED_RATE: int = 15000
    ALS_VARIABLE_BASE_RATE: int = 25000

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
