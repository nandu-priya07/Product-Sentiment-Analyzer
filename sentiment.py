"""
Product Sentiment Analyzer - Sentiment Analysis Module

This module handles sentiment analysis using TextBlob and NLTK.
Classifies reviews into Positive, Neutral, and Negative sentiments.
"""

import logging
import string
from typing import Tuple, Dict
from textblob import TextBlob
import nltk

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/averaged_perceptron_tagger')
except LookupError:
    logger.info("Downloading NLTK averaged_perceptron_tagger...")
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    logger.info("Downloading NLTK wordnet...")
    nltk.download('wordnet', quiet=True)


# ============================================================================
# SENTIMENT ANALYSIS
# ============================================================================

def analyze_sentiment(text: str) -> Tuple[float, float]:
    """
    Analyze sentiment of given text using TextBlob.
    
    Args:
        text (str): Text to analyze
    
    Returns:
        tuple: (polarity, subjectivity)
            - polarity: float between -1 (negative) and 1 (positive)
            - subjectivity: float between 0 (objective) and 1 (subjective)
    """
    try:
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for sentiment analysis")
            return 0.0, 0.5
        
        # Clean text
        text = clean_text(text)
        
        # Create TextBlob object
        blob = TextBlob(text)
        
        # Get polarity and subjectivity
        polarity = float(blob.sentiment.polarity)
        subjectivity = float(blob.sentiment.subjectivity)
        
        # Ensure values are in valid range
        polarity = max(-1.0, min(1.0, polarity))
        subjectivity = max(0.0, min(1.0, subjectivity))
        
        logger.debug(f"Sentiment - Polarity: {polarity:.3f}, Subjectivity: {subjectivity:.3f}")
        
        return polarity, subjectivity
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return 0.0, 0.5


def classify_sentiment(polarity: float) -> str:
    """
    Classify sentiment based on polarity score.
    
    Args:
        polarity (float): Polarity score (-1 to 1)
    
    Returns:
        str: 'Positive', 'Neutral', or 'Negative'
    """
    from config import Config
    
    if polarity > Config.POSITIVE_THRESHOLD:
        return 'Positive'
    elif polarity < Config.NEGATIVE_THRESHOLD:
        return 'Negative'
    else:
        return 'Neutral'


def analyze_and_classify(text: str) -> Tuple[float, float, str]:
    """
    Analyze sentiment and return polarity, subjectivity, and classification.
    
    Args:
        text (str): Text to analyze
    
    Returns:
        tuple: (polarity, subjectivity, sentiment)
    """
    polarity, subjectivity = analyze_sentiment(text)
    sentiment = classify_sentiment(polarity)
    return polarity, subjectivity, sentiment


# ============================================================================
# TEXT PREPROCESSING
# ============================================================================

def clean_text(text: str) -> str:
    """
    Clean and normalize text for sentiment analysis.
    
    Args:
        text (str): Raw text
    
    Returns:
        str: Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove URLs
    text = remove_urls(text)
    
    # Remove extra punctuation
    text = normalize_punctuation(text)
    
    # Convert to lowercase for analysis
    # (TextBlob handles this internally)
    
    return text


def remove_urls(text: str) -> str:
    """Remove URLs from text."""
    import re
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.sub(url_pattern, '', text)


def normalize_punctuation(text: str) -> str:
    """Normalize excessive punctuation."""
    import re
    # Replace multiple exclamation marks
    text = re.sub(r'!{2,}', '!', text)
    # Replace multiple question marks
    text = re.sub(r'\?{2,}', '?', text)
    # Replace multiple periods
    text = re.sub(r'\.{2,}', '.', text)
    return text


def remove_special_characters(text: str) -> str:
    """Remove special characters but keep spaces and basic punctuation."""
    # Keep alphanumeric, spaces, and basic punctuation
    return ''.join(c if c.isalnum() or c in ' .!?,;:\'"' else '' for c in text)


def remove_stopwords(text: str) -> str:
    """Remove common English stopwords."""
    try:
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english'))
        words = text.lower().split()
        filtered = [w for w in words if w not in stop_words]
        return ' '.join(filtered)
    except Exception as e:
        logger.debug(f"Error removing stopwords: {e}")
        return text


# ============================================================================
# SENTIMENT STATISTICS
# ============================================================================

def get_sentiment_score(text: str) -> Dict[str, float]:
    """
    Get detailed sentiment score breakdown.
    
    Args:
        text (str): Text to analyze
    
    Returns:
        dict: Detailed sentiment metrics
    """
    polarity, subjectivity = analyze_sentiment(text)
    sentiment = classify_sentiment(polarity)
    
    return {
        'polarity': round(polarity, 3),
        'subjectivity': round(subjectivity, 3),
        'sentiment': sentiment,
        'positive_score': round((polarity + 1) / 2, 3),  # Normalize to 0-1
        'negative_score': round((1 - polarity) / 2, 3),  # Normalize to 0-1
        'confidence': round(abs(polarity), 3)  # Confidence is absolute polarity
    }


def compare_sentiments(text1: str, text2: str) -> Dict[str, any]:
    """
    Compare sentiment between two texts.
    
    Args:
        text1 (str): First text
        text2 (str): Second text
    
    Returns:
        dict: Comparison result
    """
    pol1, sub1 = analyze_sentiment(text1)
    pol2, sub2 = analyze_sentiment(text2)
    
    return {
        'text1_polarity': round(pol1, 3),
        'text1_subjectivity': round(sub1, 3),
        'text1_sentiment': classify_sentiment(pol1),
        'text2_polarity': round(pol2, 3),
        'text2_subjectivity': round(sub2, 3),
        'text2_sentiment': classify_sentiment(pol2),
        'polarity_difference': round(abs(pol1 - pol2), 3),
        'more_positive': 'text1' if pol1 > pol2 else 'text2',
        'more_subjective': 'text1' if sub1 > sub2 else 'text2'
    }


def batch_analyze_sentiments(texts: list) -> list:
    """
    Analyze sentiment for multiple texts.
    
    Args:
        texts (list): List of texts to analyze
    
    Returns:
        list: List of sentiment analysis results
    """
    results = []
    for text in texts:
        try:
            polarity, subjectivity = analyze_sentiment(text)
            sentiment = classify_sentiment(polarity)
            results.append({
                'text': text[:100] + '...' if len(text) > 100 else text,
                'polarity': round(polarity, 3),
                'subjectivity': round(subjectivity, 3),
                'sentiment': sentiment
            })
        except Exception as e:
            logger.debug(f"Error analyzing text: {e}")
            results.append({
                'text': text[:100] + '...' if len(text) > 100 else text,
                'error': str(e)
            })
    
    return results


# ============================================================================
# SENTIMENT INTERPRETATION
# ============================================================================

def interpret_polarity(polarity: float) -> str:
    """
    Get human-readable interpretation of polarity score.
    
    Args:
        polarity (float): Polarity score (-1 to 1)
    
    Returns:
        str: Interpretation
    """
    if polarity >= 0.8:
        return "Extremely Positive"
    elif polarity >= 0.5:
        return "Very Positive"
    elif polarity >= 0.2:
        return "Positive"
    elif polarity > -0.2:
        return "Neutral"
    elif polarity >= -0.5:
        return "Negative"
    elif polarity >= -0.8:
        return "Very Negative"
    else:
        return "Extremely Negative"


def interpret_subjectivity(subjectivity: float) -> str:
    """
    Get human-readable interpretation of subjectivity score.
    
    Args:
        subjectivity (float): Subjectivity score (0 to 1)
    
    Returns:
        str: Interpretation
    """
    if subjectivity >= 0.8:
        return "Highly Subjective (Opinion-based)"
    elif subjectivity >= 0.6:
        return "Mostly Subjective"
    elif subjectivity >= 0.4:
        return "Mixed (Subjective & Objective)"
    elif subjectivity >= 0.2:
        return "Mostly Objective"
    else:
        return "Highly Objective (Fact-based)"


def get_sentiment_intensity(polarity: float) -> Dict[str, float]:
    """
    Get sentiment intensity metrics.
    
    Args:
        polarity (float): Polarity score
    
    Returns:
        dict: Intensity metrics
    """
    abs_polarity = abs(polarity)
    
    return {
        'intensity': round(abs_polarity, 3),
        'intensity_percentage': round(abs_polarity * 100, 1),
        'direction': 'Positive' if polarity > 0 else 'Negative' if polarity < 0 else 'Neutral',
        'strength': 'Strong' if abs_polarity > 0.7 else 'Moderate' if abs_polarity > 0.3 else 'Weak'
    }


# ============================================================================
# REVIEW QUALITY METRICS
# ============================================================================

def calculate_review_quality_score(text: str, rating: int) -> float:
    """
    Calculate quality score for a review based on text and rating.
    
    Args:
        text (str): Review text
        rating (int): Review rating (1-5)
    
    Returns:
        float: Quality score (0-1)
    """
    try:
        # Text length score
        text_length = len(text.split())
        length_score = min(text_length / 100, 1.0)  # 100+ words = full score
        
        # Sentiment consistency score
        polarity, subjectivity = analyze_sentiment(text)
        rating_polarity = (rating - 3) / 2  # Convert 1-5 rating to -1 to 1
        
        consistency = 1.0 - abs(polarity - rating_polarity) / 2
        consistency = max(0, consistency)
        
        # Subjectivity score (reviews with moderate subjectivity are better)
        subjectivity_score = 1.0 - abs(subjectivity - 0.5) * 0.5
        
        # Combine scores
        quality_score = (length_score * 0.3 + consistency * 0.4 + subjectivity_score * 0.3)
        
        return round(quality_score, 3)
    
    except Exception as e:
        logger.debug(f"Error calculating quality score: {e}")
        return 0.5


# ============================================================================
# SENTIMENT TREND ANALYSIS
# ============================================================================

def calculate_sentiment_trend(review_list: list) -> Dict[str, any]:
    """
    Analyze sentiment trend across multiple reviews.
    
    Args:
        review_list (list): List of reviews (dicts with 'text' and optional 'date')
    
    Returns:
        dict: Sentiment trend analysis
    """
    if not review_list:
        return {}
    
    sentiments = []
    polarities = []
    
    for review in review_list:
        text = review.get('text') or review.get('review_text', '')
        polarity, subjectivity = analyze_sentiment(text)
        sentiments.append(classify_sentiment(polarity))
        polarities.append(polarity)
    
    # Count sentiments
    positive_count = sentiments.count('Positive')
    negative_count = sentiments.count('Negative')
    neutral_count = sentiments.count('Neutral')
    
    # Calculate averages
    avg_polarity = sum(polarities) / len(polarities) if polarities else 0
    
    return {
        'total_reviews': len(review_list),
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'positive_percentage': round(positive_count / len(review_list) * 100, 1) if review_list else 0,
        'negative_percentage': round(negative_count / len(review_list) * 100, 1) if review_list else 0,
        'neutral_percentage': round(neutral_count / len(review_list) * 100, 1) if review_list else 0,
        'average_polarity': round(avg_polarity, 3),
        'overall_sentiment': classify_sentiment(avg_polarity)
    }


# Type hint import