from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Application
    APP_NAME: str
    APP_ENV: str
    DEBUG: bool

    # Security
    SECRET_KEY: str

    # API
    API_HOST: str
    API_PORT: int

    # Database
    DATABASE_URL: str

    # Logging
    LOG_LEVEL: str

    # AI Models
    WEEK10_EMERGENCY_MODEL: str = ""
    MODEL_PATH: str

    # CORS
    ALLOWED_ORIGINS: str

    # Project
    PROJECT_NAME: str
    VERSION: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore any unexpected variables
    )


settings = Settings()
