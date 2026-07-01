"""
Product Sentiment Analyzer - Models Module

This module defines database models, data validation, and helper functions
for creating and transforming review objects.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict, field
import re

logger = logging.getLogger(__name__)


# ============================================================================
# REVIEW MODEL
# ============================================================================

@dataclass
class Review:
    """
    Data model for a product review.
    
    Attributes:
        product_name (str): Name of the product
        review_text (str): The review content
        rating (int): Review rating (1-5)
        reviewer_name (str): Name of the reviewer
        review_date (str): Date when review was posted
        sentiment (str): Sentiment classification ('Positive', 'Neutral', 'Negative')
        polarity (float): Polarity score (-1 to 1)
        subjectivity (float): Subjectivity score (0 to 1)
        verified_purchase (bool): Whether purchase is verified
        platform (str): Platform source ('amazon' or 'flipkart')
        helpful_count (int): Number of helpful votes
        unhelpful_count (int): Number of unhelpful votes
        scraped_time (datetime): When the review was scraped
        review_url (str): URL of the review (if available)
    """
    
    product_name: str
    review_text: str
    rating: int
    reviewer_name: str
    review_date: str
    sentiment: str = 'Neutral'
    polarity: float = 0.0
    subjectivity: float = 0.5
    verified_purchase: bool = False
    platform: str = 'amazon'
    helpful_count: int = 0
    unhelpful_count: int = 0
    scraped_time: datetime = field(default_factory=datetime.utcnow)
    review_url: str = ''
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert review to dictionary for MongoDB insertion.
        
        Returns:
            dict: Review data
        """
        data = asdict(self)
        # Keep datetime objects as is (MongoDB will handle them)
        return data
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate review data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        from config import Config
        
        # Validate product name
        if not self.product_name or len(self.product_name.strip()) == 0:
            return False, "Product name is required"
        
        if len(self.product_name) > Config.MAX_PRODUCT_NAME_LENGTH:
            return False, f"Product name too long (max {Config.MAX_PRODUCT_NAME_LENGTH} chars)"
        
        # Validate review text
        if not self.review_text or len(self.review_text.strip()) == 0:
            return False, "Review text is required"
        
        if len(self.review_text) < Config.MIN_REVIEW_LENGTH:
            return False, f"Review too short (min {Config.MIN_REVIEW_LENGTH} chars)"
        
        if len(self.review_text) > Config.MAX_REVIEW_LENGTH:
            return False, f"Review too long (max {Config.MAX_REVIEW_LENGTH} chars)"
        
        # Validate rating
        if not isinstance(self.rating, int) or self.rating < 1 or self.rating > 5:
            return False, "Rating must be between 1 and 5"
        
        # Validate reviewer name
        if not self.reviewer_name or len(self.reviewer_name.strip()) == 0:
            return False, "Reviewer name is required"
        
        # Validate sentiment
        valid_sentiments = ['Positive', 'Neutral', 'Negative']
        if self.sentiment not in valid_sentiments:
            return False, f"Sentiment must be one of: {', '.join(valid_sentiments)}"
        
        # Validate polarity
        if not (-1 <= self.polarity <= 1):
            return False, "Polarity must be between -1 and 1"
        
        # Validate subjectivity
        if not (0 <= self.subjectivity <= 1):
            return False, "Subjectivity must be between 0 and 1"
        
        # Validate platform
        valid_platforms = ['amazon', 'flipkart']
        if self.platform not in valid_platforms:
            return False, f"Platform must be one of: {', '.join(valid_platforms)}"
        
        return True, ""
    
    def __str__(self) -> str:
        """String representation of review."""
        return f"Review({self.product_name}, {self.sentiment}, {self.rating}★)"


# ============================================================================
# PRODUCT MODEL
# ============================================================================

@dataclass
class Product:
    """
    Data model for a product.
    
    Attributes:
        name (str): Product name
        url (str): Product URL
        platform (str): Platform ('amazon' or 'flipkart')
        total_reviews (int): Total number of reviews
        average_rating (float): Average rating
        last_scraped (datetime): Last scraping timestamp
    """
    
    name: str
    url: str
    platform: str
    total_reviews: int = 0
    average_rating: float = 0.0
    last_scraped: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary."""
        return asdict(self)
    
    def validate(self) -> tuple[bool, str]:
        """Validate product data."""
        if not self.name or len(self.name.strip()) == 0:
            return False, "Product name is required"
        
        if self.platform not in ['amazon', 'flipkart']:
            return False, "Invalid platform"
        
        if not (0 <= self.average_rating <= 5):
            return False, "Average rating must be between 0 and 5"
        
        return True, ""


# ============================================================================
# SEARCH HISTORY MODEL
# ============================================================================

@dataclass
class SearchHistory:
    """
    Data model for search history tracking.
    
    Attributes:
        query (str): Search query
        platform (str): Platform searched
        results_count (int): Number of results
        timestamp (datetime): Search timestamp
    """
    
    query: str
    platform: str
    results_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_review(
    product_name: str,
    review_text: str,
    rating: int,
    reviewer_name: str,
    review_date: str,
    platform: str = 'amazon',
    verified_purchase: bool = False,
    helpful_count: int = 0,
    unhelpful_count: int = 0,
    review_url: str = ''
) -> Review:
    """
    Factory function to create a Review object.
    
    Args:
        product_name (str): Product name
        review_text (str): Review content
        rating (int): Rating (1-5)
        reviewer_name (str): Reviewer name
        review_date (str): Review date
        platform (str): Platform source
        verified_purchase (bool): Verified purchase flag
        helpful_count (int): Helpful votes
        unhelpful_count (int): Unhelpful votes
        review_url (str): Review URL
    
    Returns:
        Review: Review object
    """
    review = Review(
        product_name=product_name.strip(),
        review_text=review_text.strip(),
        rating=int(rating),
        reviewer_name=reviewer_name.strip(),
        review_date=review_date.strip(),
        platform=platform.lower(),
        verified_purchase=verified_purchase,
        helpful_count=helpful_count,
        unhelpful_count=unhelpful_count,
        review_url=review_url.strip()
    )
    
    return review


def create_product(
    name: str,
    url: str,
    platform: str,
    total_reviews: int = 0,
    average_rating: float = 0.0
) -> Product:
    """
    Factory function to create a Product object.
    
    Args:
        name (str): Product name
        url (str): Product URL
        platform (str): Platform
        total_reviews (int): Total reviews
        average_rating (float): Average rating
    
    Returns:
        Product: Product object
    """
    product = Product(
        name=name.strip(),
        url=url.strip(),
        platform=platform.lower(),
        total_reviews=total_reviews,
        average_rating=average_rating
    )
    
    return product


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_product_name(name: str) -> tuple[bool, str]:
    """
    Validate product name.
    
    Args:
        name (str): Product name to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    from config import Config
    
    if not name or len(name.strip()) == 0:
        return False, "Product name cannot be empty"
    
    if len(name) < Config.MIN_PRODUCT_NAME_LENGTH:
        return False, f"Product name too short (min {Config.MIN_PRODUCT_NAME_LENGTH} chars)"
    
    if len(name) > Config.MAX_PRODUCT_NAME_LENGTH:
        return False, f"Product name too long (max {Config.MAX_PRODUCT_NAME_LENGTH} chars)"
    
    return True, ""


def validate_review_text(text: str) -> tuple[bool, str]:
    """
    Validate review text.
    
    Args:
        text (str): Review text to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    from config import Config
    
    if not text or len(text.strip()) == 0:
        return False, "Review text cannot be empty"
    
    if len(text) < Config.MIN_REVIEW_LENGTH:
        return False, f"Review too short (min {Config.MIN_REVIEW_LENGTH} chars)"
    
    if len(text) > Config.MAX_REVIEW_LENGTH:
        return False, f"Review too long (max {Config.MAX_REVIEW_LENGTH} chars)"
    
    return True, ""


def validate_rating(rating: Any) -> tuple[bool, str]:
    """
    Validate rating value.
    
    Args:
        rating: Rating value to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        rating_int = int(rating)
        if 1 <= rating_int <= 5:
            return True, ""
        else:
            return False, "Rating must be between 1 and 5"
    except (ValueError, TypeError):
        return False, "Rating must be a valid integer"


def validate_sentiment(sentiment: str) -> tuple[bool, str]:
    """
    Validate sentiment value.
    
    Args:
        sentiment (str): Sentiment to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    valid_sentiments = ['Positive', 'Neutral', 'Negative']
    if sentiment in valid_sentiments:
        return True, ""
    return False, f"Sentiment must be one of: {', '.join(valid_sentiments)}"


def validate_polarity(polarity: Any) -> tuple[bool, str]:
    """
    Validate polarity score.
    
    Args:
        polarity: Polarity value to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        polarity_float = float(polarity)
        if -1 <= polarity_float <= 1:
            return True, ""
        else:
            return False, "Polarity must be between -1 and 1"
    except (ValueError, TypeError):
        return False, "Polarity must be a valid number"


# ============================================================================
# DATA TRANSFORMATION FUNCTIONS
# ============================================================================

def clean_text(text: str) -> str:
    """
    Clean review text by removing extra whitespace and special characters.
    
    Args:
        text (str): Text to clean
    
    Returns:
        str: Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove multiple punctuation marks
    text = re.sub(r'[!?]{2,}', '!', text)
    
    return text


def extract_rating_from_text(text: str) -> Optional[int]:
    """
    Extract numeric rating from text if present.
    
    Args:
        text (str): Text to extract from
    
    Returns:
        int: Rating (1-5) or None
    """
    # Look for patterns like "5 star", "4 stars", "★★★★★"
    star_pattern = r'★+'
    match = re.search(star_pattern, text)
    if match:
        return min(len(match.group()), 5)
    
    # Look for patterns like "5 star", "4 stars"
    number_pattern = r'(\d)\s*star'
    match = re.search(number_pattern, text, re.IGNORECASE)
    if match:
        rating = int(match.group(1))
        return rating if 1 <= rating <= 5 else None
    
    return None


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to maximum length, preserving word boundaries.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
    
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated.strip() + '...'


def classify_sentiment(polarity: float) -> str:
    """
    Classify sentiment based on polarity score.
    
    Args:
        polarity (float): Polarity score (-1 to 1)
    
    Returns:
        str: Sentiment classification
    """
    from config import Config
    
    if polarity > Config.POSITIVE_THRESHOLD:
        return 'Positive'
    elif polarity < Config.NEGATIVE_THRESHOLD:
        return 'Negative'
    else:
        return 'Neutral'


def review_to_csv_row(review: Review) -> Dict[str, Any]:
    """
    Convert review to CSV-compatible dictionary.
    
    Args:
        review (Review): Review object
    
    Returns:
        dict: CSV row data
    """
    return {
        'Product Name': review.product_name,
        'Rating': review.rating,
        'Reviewer': review.reviewer_name,
        'Review Date': review.review_date,
        'Review Text': review.review_text,
        'Sentiment': review.sentiment,
        'Polarity': round(review.polarity, 3),
        'Subjectivity': round(review.subjectivity, 3),
        'Verified Purchase': 'Yes' if review.verified_purchase else 'No',
        'Platform': review.platform,
        'Helpful': review.helpful_count,
        'Unhelpful': review.unhelpful_count,
        'Scraped Time': review.scraped_time.strftime('%Y-%m-%d %H:%M:%S')
    }


def reviews_to_csv_rows(reviews: List[Review]) -> List[Dict[str, Any]]:
    """
    Convert multiple reviews to CSV rows.
    
    Args:
        reviews (list): List of Review objects
    
    Returns:
        list: List of CSV row dictionaries
    """
    return [review_to_csv_row(review) for review in reviews]


def review_from_dict(data: Dict[str, Any]) -> Review:
    """
    Create Review object from dictionary (e.g., from database).
    
    Args:
        data (dict): Review data
    
    Returns:
        Review: Review object
    """
    # Handle datetime conversion if needed
    scraped_time = data.get('scraped_time')
    if isinstance(scraped_time, str):
        scraped_time = datetime.fromisoformat(scraped_time)
    
    created_at = data.get('created_at')
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return Review(
        product_name=data.get('product_name', ''),
        review_text=data.get('review_text', ''),
        rating=data.get('rating', 0),
        reviewer_name=data.get('reviewer_name', ''),
        review_date=data.get('review_date', ''),
        sentiment=data.get('sentiment', 'Neutral'),
        polarity=data.get('polarity', 0.0),
        subjectivity=data.get('subjectivity', 0.5),
        verified_purchase=data.get('verified_purchase', False),
        platform=data.get('platform', 'amazon'),
        helpful_count=data.get('helpful_count', 0),
        unhelpful_count=data.get('unhelpful_count', 0),
        scraped_time=scraped_time,
        review_url=data.get('review_url', ''),
        created_at=created_at
    )


# ============================================================================
# AGGREGATION FUNCTIONS
# ============================================================================

def calculate_sentiment_distribution(reviews: List[Review]) -> Dict[str, int]:
    """
    Calculate sentiment distribution from reviews.
    
    Args:
        reviews (list): List of Review objects
    
    Returns:
        dict: Sentiment counts
    """
    distribution = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
    
    for review in reviews:
        sentiment = review.sentiment
        if sentiment in distribution:
            distribution[sentiment] += 1
    
    return distribution


def calculate_average_polarity(reviews: List[Review]) -> float:
    """
    Calculate average polarity from reviews.
    
    Args:
        reviews (list): List of Review objects
    
    Returns:
        float: Average polarity
    """
    if not reviews:
        return 0.0
    
    total_polarity = sum(review.polarity for review in reviews)
    return round(total_polarity / len(reviews), 3)


def calculate_average_rating(reviews: List[Review]) -> float:
    """
    Calculate average rating from reviews.
    
    Args:
        reviews (list): List of Review objects
    
    Returns:
        float: Average rating
    """
    if not reviews:
        return 0.0
    
    total_rating = sum(review.rating for review in reviews)
    return round(total_rating / len(reviews), 2)


def get_most_common_words(reviews: List[Review], n: int = 20) -> Dict[str, int]:
    """
    Extract most common words from reviews.
    
    Args:
        reviews (list): List of Review objects
        n (int): Number of top words to return
    
    Returns:
        dict: Word frequency map
    """
    from collections import Counter
    
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'is', 'was', 'are', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
    }
    
    words = []
    for review in reviews:
        # Split and clean words
        review_words = review.review_text.lower().split()
        review_words = [
            word.strip('.,!?;:"\'-') 
            for word in review_words 
            if len(word) > 2 and word.lower() not in stop_words
        ]
        words.extend(review_words)
    
    # Get most common words
    word_freq = Counter(words)
    return dict(word_freq.most_common(n))
