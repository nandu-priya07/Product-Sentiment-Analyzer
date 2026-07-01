"""
Product Sentiment Analyzer - Configuration Module

This module loads environment variables and defines application configuration.
All sensitive data is stored in .env file, never hardcoded.
"""

import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

class Config:
    """
    Base configuration class for the Flask application.
    Loads all settings from environment variables.
    """
    
    # ========================================================================
    # FLASK SETTINGS
    # ========================================================================
    
    # Application name
    APP_NAME = "Product Sentiment Analyzer"
    
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Flask environment (development/production)
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Debug mode
    DEBUG = FLASK_ENV == 'development'
    
    # Testing mode
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'
    
    # Host and port
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # ========================================================================
    # DATABASE SETTINGS (MongoDB Atlas)
    # ========================================================================
    
    # MongoDB Atlas URI - MUST be set in .env file
    MONGO_URI = os.getenv('MONGO_URI', None)
    
    # Validate MongoDB URI is provided
    if not MONGO_URI:
        raise ValueError("MONGO_URI environment variable is not set. Check your .env file.")
    
    # Database name
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'product_sentiment')
    
    # Collection names
    REVIEWS_COLLECTION = 'reviews'
    PRODUCTS_COLLECTION = 'products'
    SEARCH_HISTORY_COLLECTION = 'search_history'
    
    # MongoDB connection settings
    MONGO_CONNECT_TIMEOUT = 5000  # milliseconds
    MONGO_SERVER_SELECTION_TIMEOUT = 5000  # milliseconds
    MONGO_SOCKET_TIMEOUT = 5000  # milliseconds
    
    # ========================================================================
    # SCRAPER SETTINGS (Selenium)
    # ========================================================================
    
    # Browser settings
    BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'False').lower() == 'true'
    BROWSER_WINDOW_SIZE = (1920, 1080)
    BROWSER_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    # Scraping timeout settings (in seconds)
    SCRAPER_PAGE_LOAD_TIMEOUT = int(os.getenv('SCRAPER_PAGE_LOAD_TIMEOUT', 60))
    SCRAPER_IMPLICIT_WAIT = int(os.getenv('SCRAPER_IMPLICIT_WAIT', 10))
    SCRAPER_EXPLICIT_WAIT = int(os.getenv('SCRAPER_EXPLICIT_WAIT', 15))
    
    # Minimum number of reviews to scrape
    MIN_REVIEWS_TO_SCRAPE = int(os.getenv('MIN_REVIEWS_TO_SCRAPE', 50))
    
    # Maximum number of reviews to scrape (for performance)
    MAX_REVIEWS_TO_SCRAPE = int(os.getenv('MAX_REVIEWS_TO_SCRAPE', 200))
    
    # Pagination settings
    REVIEWS_PER_PAGE = int(os.getenv('REVIEWS_PER_PAGE', 20))
    
    # Scraping retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds between retries
    
    # Platform settings
    PLATFORMS = {
        'amazon': {
            'url': 'https://www.amazon.in',
            'search_path': '/s',
            'enabled': True
        },
        'flipkart': {
            'url': 'https://www.flipkart.com',
            'search_path': '/search',
            'enabled': True
        }
    }
    
    # ========================================================================
    # SENTIMENT ANALYSIS SETTINGS (TextBlob)
    # ========================================================================
    
    # Sentiment classification thresholds
    POSITIVE_THRESHOLD = float(os.getenv('POSITIVE_THRESHOLD', 0.1))
    NEGATIVE_THRESHOLD = float(os.getenv('NEGATIVE_THRESHOLD', -0.1))
    
    # Sentiment labels
    SENTIMENT_LABELS = {
        'positive': 'Positive',
        'neutral': 'Neutral',
        'negative': 'Negative'
    }
    
    # ========================================================================
    # FILE UPLOAD & EXPORT SETTINGS
    # ========================================================================
    
    # Maximum file upload size (in MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB
    
    # Allowed extensions for uploads
    ALLOWED_EXTENSIONS = {'csv', 'txt', 'json'}
    
    # Export format settings
    EXPORT_FORMAT_CSV = 'csv'
    EXPORT_FORMAT_JSON = 'json'
    EXPORT_FORMATS = [EXPORT_FORMAT_CSV, EXPORT_FORMAT_JSON]
    
    # Export directory
    EXPORT_DIR = os.path.join(os.path.dirname(__file__), 'exports')
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    
    # ========================================================================
    # API SETTINGS
    # ========================================================================
    
    # API response settings
    API_RESULTS_PER_PAGE = 20
    API_MAX_RESULTS_PER_PAGE = 100
    
    # API timeout (in seconds)
    API_TIMEOUT = 30
    
    # Rate limiting (requests per minute)
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'False').lower() == 'true'
    RATE_LIMIT_REQUESTS = 100  # requests per minute
    
    # ========================================================================
    # LOGGING SETTINGS
    # ========================================================================
    
    # Log level
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Log format
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Log file location
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')
    
    # ========================================================================
    # CACHE SETTINGS
    # ========================================================================
    
    # Cache timeout for reviews (in seconds)
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 3600))  # 1 hour
    
    # Cache reviews in memory
    CACHE_REVIEWS = True
    
    # ========================================================================
    # SECURITY SETTINGS
    # ========================================================================
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    # HTTPS enforcement in production
    PREFERRED_URL_SCHEME = 'https' if FLASK_ENV == 'production' else 'http'
    
    # ========================================================================
    # PAGINATION SETTINGS
    # ========================================================================
    
    # Reviews per page for dashboard
    DASHBOARD_REVIEWS_PER_PAGE = 10
    
    # Top reviews count
    TOP_REVIEWS_COUNT = 5
    
    # Word cloud settings
    WORDCLOUD_MAX_WORDS = 100
    WORDCLOUD_MIN_WORD_FREQ = 2
    
    # ========================================================================
    # VALIDATION SETTINGS
    # ========================================================================
    
    # Minimum product name length
    MIN_PRODUCT_NAME_LENGTH = 2
    
    # Maximum product name length
    MAX_PRODUCT_NAME_LENGTH = 500
    
    # Minimum review length (characters)
    MIN_REVIEW_LENGTH = 10
    
    # Maximum review length (characters)
    MAX_REVIEW_LENGTH = 5000


class DevelopmentConfig(Config):
    """
    Development configuration.
    Used when FLASK_ENV=development
    """
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """
    Production configuration.
    Used when FLASK_ENV=production
    """
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """
    Testing configuration.
    Used when running unit tests.
    """
    TESTING = True
    DEBUG = True
    MONGO_DB_NAME = 'product_sentiment_test'


# Configuration dictionary for easy access
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Get the appropriate configuration based on FLASK_ENV.
    
    Returns:
        Config: Configuration class
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config_dict.get(env, DevelopmentConfig)
