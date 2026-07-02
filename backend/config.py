import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/sentiment_db")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"
