"""
Product Sentiment Analyzer - Database Module

This module handles all MongoDB operations including connection management,
CRUD operations, queries, filtering, and aggregation functions.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    OperationFailure,
    DuplicateKeyError
)
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

# Global database connection instance
_db_connection = None
_client = None


def init_db():
    """
    Initialize MongoDB database connection.
    Creates connection pool and collections.
    
    Returns:
        pymongo.database.Database: MongoDB database object
        
    Raises:
        ConnectionFailure: If connection to MongoDB fails
    """
    global _db_connection, _client
    
    try:
        from config import Config
        
        logger.info("Attempting to connect to MongoDB Atlas...")
        
        # Create MongoDB client with connection pool settings
        _client = MongoClient(
            Config.MONGO_URI,
            serverSelectionTimeoutMS=Config.MONGO_SERVER_SELECTION_TIMEOUT,
            connectTimeoutMS=Config.MONGO_CONNECT_TIMEOUT,
            socketTimeoutMS=Config.MONGO_SOCKET_TIMEOUT,
            maxPoolSize=50,
            minPoolSize=10
        )
        
        # Verify connection by pinging the server
        _client.admin.command('ping')
        logger.info("✓ MongoDB connection successful")
        
        # Get database instance
        _db_connection = _client[Config.MONGO_DB_NAME]
        
        # Create collections and indexes
        _create_collections_and_indexes()
        
        logger.info(f"✓ Connected to database: {Config.MONGO_DB_NAME}")
        
        return _db_connection
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"✗ Failed to connect to MongoDB: {e}")
        raise ConnectionFailure(f"Cannot connect to MongoDB: {e}") from e
    except Exception as e:
        logger.error(f"✗ Unexpected error during database initialization: {e}")
        raise


def _create_collections_and_indexes():
    """
    Create collections and indexes if they don't exist.
    Improves query performance.
    """
    try:
        from config import Config
        
        # Create reviews collection with indexes
        if Config.REVIEWS_COLLECTION not in _db_connection.list_collection_names():
            _db_connection.create_collection(Config.REVIEWS_COLLECTION)
            logger.info(f"✓ Created collection: {Config.REVIEWS_COLLECTION}")
        
        reviews_col = _db_connection[Config.REVIEWS_COLLECTION]
        
        # Create indexes for better query performance
        reviews_col.create_index([('product_name', ASCENDING)])
        reviews_col.create_index([('sentiment', ASCENDING)])
        reviews_col.create_index([('rating', DESCENDING)])
        reviews_col.create_index([('scraped_time', DESCENDING)])
        reviews_col.create_index([('reviewer_name', ASCENDING)])
        reviews_col.create_index([('polarity', DESCENDING)])
        
        # Create text index for full-text search
        reviews_col.create_index([('review_text', 'text'), ('product_name', 'text')])
        
        logger.info("✓ Indexes created successfully")
        
        # Create search history collection
        if Config.SEARCH_HISTORY_COLLECTION not in _db_connection.list_collection_names():
            _db_connection.create_collection(Config.SEARCH_HISTORY_COLLECTION)
            logger.info(f"✓ Created collection: {Config.SEARCH_HISTORY_COLLECTION}")
        
    except Exception as e:
        logger.warning(f"Error creating collections/indexes: {e}")


def get_db_connection():
    """
    Get the database connection instance.
    
    Returns:
        pymongo.database.Database: MongoDB database object
        
    Raises:
        ConnectionFailure: If no connection exists
    """
    if _db_connection is None:
        raise ConnectionFailure("Database not initialized. Call init_db() first.")
    return _db_connection


def close_db_connection():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        logger.info("✓ Database connection closed")


# ============================================================================
# REVIEWS CRUD OPERATIONS
# ============================================================================

def insert_review(review_data: Dict[str, Any]) -> str:
    """
    Insert a single review into the database.
    
    Args:
        review_data (dict): Review document with fields:
            - product_name (str)
            - review_text (str)
            - rating (int)
            - reviewer_name (str)
            - review_date (str)
            - sentiment (str): 'Positive', 'Neutral', 'Negative'
            - polarity (float)
            - subjectivity (float)
            - verified_purchase (bool)
    
    Returns:
        str: Inserted document ID
        
    Raises:
        OperationFailure: If insertion fails
    """
    try:
        from config import Config
        
        # Add metadata
        review_data['scraped_time'] = datetime.utcnow()
        review_data['created_at'] = datetime.utcnow()
        
        db = get_db_connection()
        result = db[Config.REVIEWS_COLLECTION].insert_one(review_data)
        
        logger.info(f"✓ Review inserted: {result.inserted_id}")
        return str(result.inserted_id)
        
    except OperationFailure as e:
        logger.error(f"✗ Failed to insert review: {e}")
        raise


def insert_many_reviews(reviews_data: List[Dict[str, Any]]) -> List[str]:
    """
    Insert multiple reviews into the database in bulk.
    
    Args:
        reviews_data (list): List of review documents
    
    Returns:
        list: List of inserted document IDs
        
    Raises:
        OperationFailure: If insertion fails
    """
    try:
        from config import Config
        
        if not reviews_data:
            logger.warning("No reviews to insert")
            return []
        
        # Add metadata to all reviews
        for review in reviews_data:
            review['scraped_time'] = datetime.utcnow()
            review['created_at'] = datetime.utcnow()
        
        db = get_db_connection()
        result = db[Config.REVIEWS_COLLECTION].insert_many(reviews_data)
        
        logger.info(f"✓ {len(result.inserted_ids)} reviews inserted successfully")
        return [str(id) for id in result.inserted_ids]
        
    except OperationFailure as e:
        logger.error(f"✗ Failed to insert reviews: {e}")
        raise


def get_reviews_by_product(
    product_name: str,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = 'scraped_time',
    sentiment_filter: Optional[str] = None
) -> Tuple[List[Dict], int]:
    """
    Fetch reviews for a specific product with pagination.
    
    Args:
        product_name (str): Product name to search
        page (int): Page number (1-indexed)
        per_page (int): Reviews per page
        sort_by (str): Field to sort by
        sentiment_filter (str): Filter by sentiment ('Positive', 'Neutral', 'Negative')
    
    Returns:
        tuple: (list of reviews, total count)
    """
    try:
        from config import Config
        
        db = get_db_connection()
        reviews_col = db[Config.REVIEWS_COLLECTION]
        
        # Build query filter
        query = {'product_name': {'$regex': product_name, '$options': 'i'}}
        if sentiment_filter:
            query['sentiment'] = sentiment_filter
        
        # Calculate pagination
        skip = (page - 1) * per_page
        
        # Get total count
        total_count = reviews_col.count_documents(query)
        
        # Fetch reviews
        reviews = list(
            reviews_col.find(query)
            .sort(sort_by, DESCENDING)
            .skip(skip)
            .limit(per_page)
        )
        
        # Convert ObjectId to string
        for review in reviews:
            review['_id'] = str(review['_id'])
        
        logger.info(f"✓ Retrieved {len(reviews)} reviews for product: {product_name}")
        return reviews, total_count
        
    except Exception as e:
        logger.error(f"✗ Error fetching reviews: {e}")
        return [], 0


def get_review_by_id(review_id: str) -> Optional[Dict]:
    """
    Fetch a specific review by ID.
    
    Args:
        review_id (str): Review ObjectId
    
    Returns:
        dict: Review document or None
    """
    try:
        from config import Config
        
        db = get_db_connection()
        review = db[Config.REVIEWS_COLLECTION].find_one({'_id': ObjectId(review_id)})
        
        if review:
            review['_id'] = str(review['_id'])
        
        return review
        
    except Exception as e:
        logger.error(f"✗ Error fetching review: {e}")
        return None


def get_all_reviews(page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int]:
    """
    Fetch all reviews with pagination.
    
    Args:
        page (int): Page number
        per_page (int): Reviews per page
    
    Returns:
        tuple: (list of reviews, total count)
    """
    try:
        from config import Config
        
        db = get_db_connection()
        reviews_col = db[Config.REVIEWS_COLLECTION]
        
        skip = (page - 1) * per_page
        total_count = reviews_col.count_documents({})
        
        reviews = list(
            reviews_col.find({})
            .sort('scraped_time', DESCENDING)
            .skip(skip)
            .limit(per_page)
        )
        
        for review in reviews:
            review['_id'] = str(review['_id'])
        
        return reviews, total_count
        
    except Exception as e:
        logger.error(f"✗ Error fetching all reviews: {e}")
        return [], 0


def delete_reviews_by_product(product_name: str) -> int:
    """
    Delete all reviews for a specific product.
    
    Args:
        product_name (str): Product name
    
    Returns:
        int: Number of deleted reviews
    """
    try:
        from config import Config
        
        db = get_db_connection()
        result = db[Config.REVIEWS_COLLECTION].delete_many(
            {'product_name': {'$regex': product_name, '$options': 'i'}}
        )
        
        logger.info(f"✓ Deleted {result.deleted_count} reviews for product: {product_name}")
        return result.deleted_count
        
    except Exception as e:
        logger.error(f"✗ Error deleting reviews: {e}")
        return 0


def delete_review_by_id(review_id: str) -> bool:
    """
    Delete a specific review by ID.
    
    Args:
        review_id (str): Review ObjectId
    
    Returns:
        bool: True if deleted, False otherwise
    """
    try:
        from config import Config
        
        db = get_db_connection()
        result = db[Config.REVIEWS_COLLECTION].delete_one({'_id': ObjectId(review_id)})
        
        deleted = result.deleted_count > 0
        if deleted:
            logger.info(f"✓ Review deleted: {review_id}")
        
        return deleted
        
    except Exception as e:
        logger.error(f"✗ Error deleting review: {e}")
        return False


# ============================================================================
# SEARCH & FILTER OPERATIONS
# ============================================================================

def search_reviews(
    search_query: str,
    product_name: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> Tuple[List[Dict], int]:
    """
    Full-text search across reviews.
    
    Args:
        search_query (str): Text to search for
        product_name (str): Optional product filter
        page (int): Page number
        per_page (int): Results per page
    
    Returns:
        tuple: (list of reviews, total count)
    """
    try:
        from config import Config
        
        db = get_db_connection()
        reviews_col = db[Config.REVIEWS_COLLECTION]
        
        query = {'$text': {'$search': search_query}}
        if product_name:
            query['product_name'] = {'$regex': product_name, '$options': 'i'}
        
        skip = (page - 1) * per_page
        total_count = reviews_col.count_documents(query)
        
        reviews = list(
            reviews_col.find(query)
            .skip(skip)
            .limit(per_page)
        )
        
        for review in reviews:
            review['_id'] = str(review['_id'])
        
        logger.info(f"✓ Found {total_count} reviews matching: {search_query}")
        return reviews, total_count
        
    except Exception as e:
        logger.error(f"✗ Error searching reviews: {e}")
        return [], 0


def filter_reviews(
    product_name: Optional[str] = None,
    sentiment: Optional[str] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> Tuple[List[Dict], int]:
    """
    Filter reviews by multiple criteria.
    
    Args:
        product_name (str): Product name filter
        sentiment (str): Sentiment filter
        min_rating (int): Minimum rating
        max_rating (int): Maximum rating
        start_date (str): Start date (ISO format)
        end_date (str): End date (ISO format)
        page (int): Page number
        per_page (int): Results per page
    
    Returns:
        tuple: (list of reviews, total count)
    """
    try:
        from config import Config
        
        db = get_db_connection()
        reviews_col = db[Config.REVIEWS_COLLECTION]
        
        # Build filter query
        query = {}
        
        if product_name:
            query['product_name'] = {'$regex': product_name, '$options': 'i'}
        
        if sentiment:
            query['sentiment'] = sentiment
        
        if min_rating or max_rating:
            query['rating'] = {}
            if min_rating:
                query['rating']['$gte'] = min_rating
            if max_rating:
                query['rating']['$lte'] = max_rating
        
        if start_date or end_date:
            query['scraped_time'] = {}
            if start_date:
                query['scraped_time']['$gte'] = datetime.fromisoformat(start_date)
            if end_date:
                query['scraped_time']['$lte'] = datetime.fromisoformat(end_date)
        
        skip = (page - 1) * per_page
        total_count = reviews_col.count_documents(query)
        
        reviews = list(
            reviews_col.find(query)
            .sort('scraped_time', DESCENDING)
            .skip(skip)
            .limit(per_page)
        )
        
        for review in reviews:
            review['_id'] = str(review['_id'])
        
        return reviews, total_count
        
    except Exception as e:
        logger.error(f"✗ Error filtering reviews: {e}")
        return [], 0


# ============================================================================
# ANALYTICS & AGGREGATION OPERATIONS
# ============================================================================

def get_sentiment_stats(product_name: str) -> Dict[str, Any]:
    """
    Get sentiment statistics for a product.
    
    Args:
        product_name (str): Product name
    
    Returns:
        dict: Statistics with positive, negative, neutral counts
    """
    try:
        from config import Config
        
        db = get_db_connection()
        reviews_col = db[Config.REVIEWS_COLLECTION]
        
        query = {'product_name': {'$regex': product_name, '$options': 'i'}}
        
        # Get total reviews
        total_reviews = reviews_col.count_documents(query)
        
        # Get sentiment counts
        positive_count = reviews_col.count_documents({**query, 'sentiment': 'Positive'})
        negative_count = reviews_col.count_documents({**query, 'sentiment': 'Negative'})
        neutral_count = reviews_col.count_documents({**query, 'sentiment': 'Neutral'})
        
        # Calculate percentages
        positive_pct = (positive_count / total_reviews * 100) if total_reviews > 0 else 0
        negative_pct = (negative_count / total_reviews * 100) if total_reviews > 0 else 0
        neutral_pct = (neutral_count / total_reviews * 100) if total_reviews > 0 else 0
        
        stats = {
            'total_reviews': total_reviews,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_percentage': round(positive_pct, 2),
            'negative_percentage': round(negative_pct, 2),
            'neutral_percentage': round(neutral_pct, 2)
        }
        
        logger.info(f"✓ Sentiment stats retrieved for: {product_name}")
        return stats
        
    except Exception as e:
        logger.error(f"✗ Error getting sentiment stats: {e}")
        return {}


def get_rating_distribution(product_name: str) -> Dict[int, int]:
    """
    Get distribution of ratings for a product.
    
    Args:
        product_name (str): Product name
    
    Returns:
        dict: Rating distribution (rating -> count)
    """
    try:
        from config import Config
        
        db = get_db_connection()
        reviews_col = db[Config.REVIEWS_COLLECTION]
        
        query = {'product_name': {'$regex': product_name, '$options': 'i'}}
        
        distribution = {}
        for rating in range(1, 6):
            count = reviews_col.count_documents({**query, 'rating': rating})
            distribution[rating] = count
        
        return distribution
        
    except Exception as e:
        logger.error(f"✗ Error getting rating distribution: {e}")
        return {}


def get_average_rating(product_name: str) -> float:
    """
    Calculate average rating for a product.
    
    Args:
        product_name (str): Product name
    
    Returns:
        float: Average rating
    """
    try:
        from config import Config
        
        db = get_db_connection()
        reviews_col = db[Config.REVIEWS_COLLECTION]
        
        query = {'product_name': {'$regex': product_name, '$options': 'i'}}
        
        result = list(reviews_col.aggregate([
            {'$match': query},
            {'$group': {'_id': None, 'avg_rating': {'$avg': '$rating'}}}
        ]))
        
        average = result[0]['avg_rating'] if result else 0
        return round(average, 2)
        
    except Exception as e:
        logger.error(f"✗ Error calculating average rating: {e}")
        return 0.0


def get_top_reviews(product_name: str, limit: int = 5, sentiment: Optional[str] = None) -> List[Dict]:
    """
    Get top reviews (by polarity score) for a product.
    
    Args:
        product_name (str): Product name
        limit (int): Number of reviews to return
        sentiment (str): Optional sentiment filter
    
    Returns:
        list: Top reviews
    """
    try:
        from config import Config
        
        db = get_db_connection()
        reviews_col = db[Config.REVIEWS_COLLECTION]
        
        query = {'product_name': {'$regex': product_name, '$options': 'i'}}
        if sentiment:
            query['sentiment'] = sentiment
        
        reviews = list(
            reviews_col.find(query)
            .sort('polarity', DESCENDING)
            .limit(limit)
        )
        
        for review in reviews:
            review['_id'] = str(review['_id'])
        
        return reviews
        
    except Exception as e:
        logger.error(f"✗ Error getting top reviews: {e}")
        return []


def get_recent_reviews(limit: int = 10) -> List[Dict]:
    """
    Get most recent reviews across all products.
    
    Args:
        limit (int): Number of reviews to return
    
    Returns:
        list: Recent reviews
    """
    try:
        from config import Config
        
        db = get_db_connection()
        reviews_col = db[Config.REVIEWS_COLLECTION]
        
        reviews = list(
            reviews_col.find({})
            .sort('scraped_time', DESCENDING)
            .limit(limit)
        )
        
        for review in reviews:
            review['_id'] = str(review['_id'])
        
        return reviews
        
    except Exception as e:
        logger.error(f"✗ Error getting recent reviews: {e}")
        return []


def get_dashboard_stats(product_name: str) -> Dict[str, Any]:
    """
    Get comprehensive dashboard statistics for a product.
    
    Args:
        product_name (str): Product name
    
    Returns:
        dict: Dashboard statistics
    """
    try:
        sentiment_stats = get_sentiment_stats(product_name)
        avg_rating = get_average_rating(product_name)
        rating_dist = get_rating_distribution(product_name)
        top_positive = get_top_reviews(product_name, limit=5, sentiment='Positive')
        top_negative = get_top_reviews(product_name, limit=5, sentiment='Negative')
        
        stats = {
            **sentiment_stats,
            'average_rating': avg_rating,
            'rating_distribution': rating_dist,
            'top_positive_reviews': top_positive,
            'top_negative_reviews': top_negative
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"✗ Error getting dashboard stats: {e}")
        return {}


def get_unique_products() -> List[str]:
    """
    Get list of all unique product names in database.
    
    Returns:
        list: Unique product names
    """
    try:
        from config import Config
        
        db = get_db_connection()
        products = db[Config.REVIEWS_COLLECTION].distinct('product_name')
        
        return sorted(products)
        
    except Exception as e:
        logger.error(f"✗ Error getting unique products: {e}")
        return []


def clear_old_reviews(days: int = 30) -> int:
    """
    Delete reviews older than specified days.
    
    Args:
        days (int): Delete reviews older than this many days
    
    Returns:
        int: Number of deleted reviews
    """
    try:
        from config import Config
        
        db = get_db_connection()
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = db[Config.REVIEWS_COLLECTION].delete_many(
            {'scraped_time': {'$lt': cutoff_date}}
        )
        
        logger.info(f"✓ Deleted {result.deleted_count} reviews older than {days} days")
        return result.deleted_count
        
    except Exception as e:
        logger.error(f"✗ Error clearing old reviews: {e}")
        return 0
