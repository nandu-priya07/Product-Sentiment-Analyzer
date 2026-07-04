import os
from dotenv import load_dotenv

load_dotenv()


def _csv_env(name: str, default: str) -> list[str]:
    return [
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    ]


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/sentiment_db")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "sentiment_db")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    CORS_ORIGINS = _csv_env("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    USE_MOCK_DATA = _bool_env("USE_MOCK_DATA", True)
    DEBUG = _bool_env("FLASK_DEBUG", os.getenv("FLASK_ENV", "development") == "development")
    PORT = int(os.getenv("PORT", "5000"))
