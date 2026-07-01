"""
Product Sentiment Analyzer - Utility Functions Module

This module contains helper functions for text processing, date formatting,
CSV export, and other common operations.
"""

import logging
import csv
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# TEXT PROCESSING
# ============================================================================

def clean_product_name(name: str) -> str:
    """
    Clean product name by removing extra spaces and special characters.
    
    Args:
        name (str): Raw product name
    
    Returns:
        str: Cleaned product name
    """
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    # Remove special characters but keep spaces and hyphens
    import re
    name = re.sub(r'[^a-zA-Z0-9\s\-]', '', name)
    
    # Remove extra hyphens
    name = re.sub(r'-+', '-', name)
    
    return name.strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to maximum length, preserving word boundaries.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix to add if truncated
    
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length // 2:
        truncated = truncated[:last_space]
    
    return truncated.rstrip() + suffix


def highlight_keywords(text: str, keywords: List[str]) -> str:
    """
    Highlight keywords in text (for HTML display).
    
    Args:
        text (str): Original text
        keywords (list): Keywords to highlight
    
    Returns:
        str: HTML with highlighted keywords
    """
    import re
    
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        text = pattern.sub(f'<mark>{keyword}</mark>', text)
    
    return text


def extract_keywords(text: str, min_length: int = 4) -> List[str]:
    """
    Extract important keywords from text.
    
    Args:
        text (str): Input text
        min_length (int): Minimum keyword length
    
    Returns:
        list: List of keywords
    """
    import re
    from collections import Counter
    
    # Common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'is', 'was', 'are', 'be', 'been', 'being', 'have', 'has', 'had'
    }
    
    # Extract words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter
    words = [w for w in words if len(w) >= min_length and w not in stop_words]
    
    # Get most common
    counter = Counter(words)
    return [word for word, _ in counter.most_common(10)]


# ============================================================================
# DATE & TIME UTILITIES
# ============================================================================

def format_date(date_obj: datetime, format_str: str = '%d %b %Y') -> str:
    """
    Format datetime object to string.
    
    Args:
        date_obj (datetime): Datetime object
        format_str (str): Format string
    
    Returns:
        str: Formatted date string
    """
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.fromisoformat(date_obj)
        return date_obj.strftime(format_str)
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return str(date_obj)


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string to datetime object.
    
    Args:
        date_str (str): Date string
    
    Returns:
        datetime: Parsed datetime or None
    """
    formats = [
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%d %b %Y',
        '%d %B %Y',
        '%Y-%m-%d %H:%M:%S',
        '%d-%m-%Y %H:%M:%S'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


def get_time_ago(date_obj: datetime) -> str:
    """
    Get human-readable time difference (e.g., "2 days ago").
    
    Args:
        date_obj (datetime): Datetime object
    
    Returns:
        str: Human-readable time difference
    """
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.fromisoformat(date_obj)
        
        now = datetime.utcnow()
        diff = now - date_obj
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = int(seconds / 2592000)
            return f"{months} month{'s' if months > 1 else ''} ago"
    
    except Exception as e:
        logger.error(f"Error calculating time ago: {e}")
        return str(date_obj)


# ============================================================================
# CSV EXPORT
# ============================================================================

def export_to_csv(reviews: List, product_name: str = "reviews") -> str:
    """
    Export reviews to CSV file.
    
    Args:
        reviews (list): List of Review objects
        product_name (str): Product name for filename
    
    Returns:
        str: Path to exported CSV file
    """
    try:
        from config import Config
        from models import review_to_csv_row
        
        # Create exports directory if not exists
        os.makedirs(Config.EXPORT_DIR, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"reviews_{product_name}_{timestamp}.csv")
        filepath = os.path.join(Config.EXPORT_DIR, filename)
        
        # Convert to CSV rows
        csv_rows = [review_to_csv_row(review) for review in reviews]
        
        if not csv_rows:
            logger.warning("No reviews to export")
            return ""
        
        # Get headers from first row
        headers = csv_rows[0].keys()
        
        # Write to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(csv_rows)
        
        logger.info(f"✓ CSV exported: {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return ""


def export_to_json(reviews: List[Dict], product_name: str = "reviews") -> str:
    """
    Export reviews to JSON file.
    
    Args:
        reviews (list): List of review dictionaries
        product_name (str): Product name for filename
    
    Returns:
        str: Path to exported JSON file
    """
    try:
        from config import Config
        
        # Create exports directory if not exists
        os.makedirs(Config.EXPORT_DIR, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"reviews_{product_name}_{timestamp}.json")
        filepath = os.path.join(Config.EXPORT_DIR, filename)
        
        # Convert datetime objects to strings
        for review in reviews:
            for key, value in review.items():
                if isinstance(value, datetime):
                    review[key] = value.isoformat()
        
        # Write to JSON
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(reviews, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ JSON exported: {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return ""


def secure_filename(filename: str) -> str:
    """
    Make filename safe for file system.
    
    Args:
        filename (str): Original filename
    
    Returns:
        str: Safe filename
    """
    import re
    
    # Remove non-alphanumeric characters except dash, underscore, and dot
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Replace spaces with underscore
    filename = re.sub(r'\s+', '_', filename)
    
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    return filename


# ============================================================================
# STATISTICS
# ============================================================================

def calculate_statistics(reviews: List[Dict]) -> Dict[str, Any]:
    """
    Calculate statistics from reviews.
    
    Args:
        reviews (list): List of review dictionaries
    
    Returns:
        dict: Statistics
    """
    if not reviews:
        return {}
    
    ratings = [r.get('rating', 0) for r in reviews]
    polarities = [r.get('polarity', 0) for r in reviews]
    sentiments = [r.get('sentiment', 'Neutral') for r in reviews]
    
    return {
        'total_reviews': len(reviews),
        'average_rating': round(sum(ratings) / len(ratings), 2) if ratings else 0,
        'min_rating': min(ratings) if ratings else 0,
        'max_rating': max(ratings) if ratings else 0,
        'average_polarity': round(sum(polarities) / len(polarities), 3) if polarities else 0,
        'positive_reviews': sentiments.count('Positive'),
        'negative_reviews': sentiments.count('Negative'),
        'neutral_reviews': sentiments.count('Neutral'),
        'positive_percentage': round(sentiments.count('Positive') / len(sentiments) * 100, 1) if sentiments else 0,
        'negative_percentage': round(sentiments.count('Negative') / len(sentiments) * 100, 1) if sentiments else 0,
        'neutral_percentage': round(sentiments.count('Neutral') / len(sentiments) * 100, 1) if sentiments else 0
    }


def get_rating_statistics(reviews: List[Dict]) -> Dict[int, int]:
    """
    Get distribution of ratings.
    
    Args:
        reviews (list): List of review dictionaries
    
    Returns:
        dict: Rating distribution
    """
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for review in reviews:
        rating = review.get('rating', 0)
        if rating in distribution:
            distribution[rating] += 1
    
    return distribution


# ============================================================================
# VALIDATION
# ============================================================================

def is_valid_email(email: str) -> bool:
    """Validate email address."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_url(url: str) -> bool:
    """Validate URL."""
    import re
    pattern = r'^https?://[^\s]+'
    return re.match(pattern, url) is not None


def is_empty_string(text: str) -> bool:
    """Check if string is empty or whitespace."""
    return text is None or len(text.strip()) == 0


def validate_rating(rating: Any) -> bool:
    """Validate rating is between 1 and 5."""
    try:
        return 1 <= int(rating) <= 5
    except (ValueError, TypeError):
        return False


# ============================================================================
# CONVERSIONS
# ============================================================================

def sentiment_to_emoji(sentiment: str) -> str:
    """Convert sentiment to emoji."""
    mapping = {
        'Positive': '😊',
        'Negative': '😞',
        'Neutral': '😐'
    }
    return mapping.get(sentiment, '❓')


def rating_to_stars(rating: int) -> str:
    """Convert rating to star string."""
    full_stars = '★' * rating
    empty_stars = '☆' * (5 - rating)
    return full_stars + empty_stars


def rating_to_bar(rating: int, max_width: int = 20) -> str:
    """Convert rating to progress bar."""
    filled = int(rating / 5 * max_width)
    empty = max_width - filled
    return '█' * filled + '░' * empty


# ============================================================================
# PAGINATION
# ============================================================================

def paginate(items: List, page: int, per_page: int) -> tuple:
    """
    Paginate a list of items.
    
    Args:
        items (list): Items to paginate
        page (int): Page number (1-indexed)
        per_page (int): Items per page
    
    Returns:
        tuple: (paginated_items, total_pages)
    """
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    
    # Ensure page is valid
    page = max(1, min(page, total_pages))
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return items[start:end], total_pages


# ============================================================================
# COLORS & FORMATTING
# ============================================================================

def get_sentiment_color(sentiment: str) -> str:
    """Get hex color for sentiment."""
    colors = {
        'Positive': '#28a745',  # Green
        'Negative': '#dc3545',  # Red
        'Neutral': '#6c757d'    # Gray
    }
    return colors.get(sentiment, '#6c757d')


def get_rating_color(rating: int) -> str:
    """Get hex color for rating."""
    if rating >= 4:
        return '#28a745'  # Green
    elif rating >= 3:
        return '#ffc107'  # Yellow
    else:
        return '#dc3545'  # Red


# ============================================================================
# LOGGING HELPERS
# ============================================================================

def log_action(action: str, user: str = "System", details: str = ""):
    """Log an application action."""
    message = f"[{user}] {action}"
    if details:
        message += f" - {details}"
    logger.info(message)


def format_error_message(error: Exception, context: str = "") -> str:
    """Format error message for display."""
    message = str(error)
    if context:
        message = f"{context}: {message}"
    return message
