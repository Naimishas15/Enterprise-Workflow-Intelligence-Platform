from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    SENTRY_DSN: str = ""
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = str(BASE_DIR/".env")

settings = Settings()