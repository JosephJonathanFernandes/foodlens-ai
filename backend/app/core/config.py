"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "FoodLens AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_BASE_URL: str = "http://localhost:8000"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    CORS_ORIGINS: str = "*"

    DATABASE_URL: str = "sqlite:///./foodlens.db"

    OCR_ENGINE: str = "paddleocr"

    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""
    LLM_BASE_URL: str = ""

    TRANSLATION_PROVIDER: str = "mock"
    TRANSLATION_API_KEY: str = ""
    TRANSLATION_BASE_URL: str = ""

    SECRET_KEY: str = "replace-with-a-strong-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
