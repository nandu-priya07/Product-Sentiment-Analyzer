"""
Product Sentiment Analyzer - Routes Module

This module defines all Flask routes and blueprints for the application.
Includes routes for home, search, scraping, dashboard, and API endpoints.
"""

import logging
import json
from functools import wraps
from threading import Thread
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

import database as db
import models
import utils
from scraper import scrape_amazon, scrape_flipkart
from sentiment import analyze_sentiment
from config import Config

logger = logging.getLogger(__name__)

# Global dictionary to track scraping status
scraping_status = {}


# ============================================================================
# BLUEPRINT DEFINITIONS
# ============================================================================

home_bp = Blueprint('home', __name__)
search_bp = Blueprint('search', __name__, url_prefix='/search')
scraper_bp = Blueprint('scraper', __name__, url_prefix='/scraper')
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ============================================================================
# HELPER DECORATORS
# ============================================================================

def require_json(f):
    """Decorator to require JSON request content type."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type must be application/json'
            }), 400
        return f(*args, **kwargs)
    return decorated_function


def handle_errors(f):
    """Decorator to handle common errors."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred'
            }), 500
    return decorated_function


# ============================================================================
# HOME ROUTES
# ============================================================================

@home_bp.route('/', methods=['GET'])
def index():
    """
    Home page route.
    
    Returns:
        HTML: Rendered homepage
    """
    try:
        logger.info("Rendering homepage")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering homepage: {e}")
        return render_template('error.html', error='Failed to load homepage'), 500


# ============================================================================
# SEARCH ROUTES
# ============================================================================

@search_bp.route('/', methods=['GET', 'POST'])
def search_page():
    """
    Search page route.
    
    Returns:
        HTML: Rendered search page
    """
    try:
        logger.info("Rendering search page")
        products = db.get_unique_products()
        return render_template(
            'search.html',
            products=products,
            platforms=['amazon', 'flipkart']
        )
    except Exception as e:
        logger.error(f"Error loading search page: {e}")
        return render_template('error.html', error='Failed to load search page'), 500


@search_bp.route('/product/<product_name>', methods=['GET'])
@handle_errors
def view_product_reviews(product_name):
    """
    View reviews for a specific product.
    
    Args:
        product_name (str): Product name
    
    Returns:
        HTML: Product review page
    """
    try:
        # Validate product name
        is_valid, error_msg = models.validate_product_name(product_name)
        if not is_valid:
            return render_template('error.html', error=error_msg), 400
        
        # Get page number
        page = request.args.get('page', 1, type=int)
        per_page = Config.REVIEWS_PER_PAGE
        
        # Fetch reviews
        reviews, total = db.get_reviews_by_product(product_name, page, per_page)
        
        # Get statistics
        stats = db.get_dashboard_stats(product_name)
        
        logger.info(f"Loaded {len(reviews)} reviews for product: {product_name}")
        
        return render_template(
            'reviews.html',
            product_name=product_name,
            reviews=reviews,
            stats=stats,
            page=page,
            total_reviews=total,
            reviews_per_page=per_page,
            total_pages=(total + per_page - 1) // per_page
        )
    except Exception as e:
        logger.error(f"Error loading product reviews: {e}")
        return render_template('error.html', error='Failed to load reviews'), 500


# ============================================================================
# SCRAPER ROUTES
# ============================================================================

@scraper_bp.route('/start', methods=['POST'])
@require_json
@handle_errors
def start_scraping():
    """
    Start scraping reviews for a product.
    
    Request JSON:
        {
            "product_name": "string",
            "platform": "amazon|flipkart",
            "min_reviews": 50
        }
    
    Returns:
        JSON: Scraping task ID and status
    """
    try:
        data = request.get_json()
        
        # Validate input
        product_name = data.get('product_name', '').strip()
        platform = data.get('platform', 'amazon').lower()
        min_reviews = int(data.get('min_reviews', Config.MIN_REVIEWS_TO_SCRAPE))
        
        # Validate product name
        is_valid, error_msg = models.validate_product_name(product_name)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        # Validate platform
        if platform not in ['amazon', 'flipkart']:
            return jsonify({
                'success': False,
                'message': 'Platform must be "amazon" or "flipkart"'
            }), 400
        
        # Generate task ID
        task_id = f"{product_name}_{platform}_{datetime.utcnow().timestamp()}"
        
        # Initialize scraping status
        scraping_status[task_id] = {
            'status': 'running',
            'product': product_name,
            'platform': platform,
            'reviews_count': 0,
            'start_time': datetime.utcnow().isoformat(),
            'message': 'Starting scraper...'
        }
        
        logger.info(f"Starting scraping task: {task_id}")
        
        # Start scraping in background thread
        thread = Thread(
            target=_scrape_reviews_task,
            args=(task_id, product_name, platform, min_reviews)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Scraping started',
            'task_id': task_id
        }), 202
        
    except ValueError as e:
        logger.warning(f"Invalid scraper request: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error starting scraper: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to start scraper'}), 500


@scraper_bp.route('/status/<task_id>', methods=['GET'])
@handle_errors
def get_scraping_status(task_id):
    """
    Get status of a scraping task.
    
    Args:
        task_id (str): Task ID
    
    Returns:
        JSON: Task status
    """
    if task_id not in scraping_status:
        return jsonify({
            'success': False,
            'message': 'Task not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': scraping_status[task_id]
    }), 200


def _scrape_reviews_task(task_id, product_name, platform, min_reviews):
    """
    Background task to scrape reviews.
    
    Args:
        task_id (str): Task ID
        product_name (str): Product name to scrape
        platform (str): Platform ('amazon' or 'flipkart')
        min_reviews (int): Minimum reviews to scrape
    """
    try:
        logger.info(f"Scraping task started: {task_id}")
        scraping_status[task_id]['message'] = 'Launching browser...'
        
        # Select scraper based on platform
        if platform == 'amazon':
            scraped_reviews = scrape_amazon(product_name, min_reviews)
        else:  # flipkart
            scraped_reviews = scrape_flipkart(product_name, min_reviews)
        
        if not scraped_reviews:
            scraping_status[task_id]['status'] = 'failed'
            scraping_status[task_id]['message'] = 'No reviews found'
            logger.warning(f"No reviews scraped for: {product_name}")
            return
        
        logger.info(f"Scraped {len(scraped_reviews)} reviews")
        scraping_status[task_id]['message'] = f'Analyzing sentiment ({len(scraped_reviews)} reviews)...'
        
        # Analyze sentiment for each review
        for review in scraped_reviews:
            polarity, subjectivity = analyze_sentiment(review['review_text'])
            review['polarity'] = polarity
            review['subjectivity'] = subjectivity
            review['sentiment'] = models.classify_sentiment(polarity)
        
        # Insert into database
        scraping_status[task_id]['message'] = 'Saving to database...'
        review_ids = db.insert_many_reviews(scraped_reviews)
        
        # Update status
        scraping_status[task_id]['status'] = 'completed'
        scraping_status[task_id]['reviews_count'] = len(review_ids)
        scraping_status[task_id]['message'] = f'Successfully scraped and saved {len(review_ids)} reviews'
        scraping_status[task_id]['end_time'] = datetime.utcnow().isoformat()
        
        logger.info(f"Scraping task completed: {task_id} - {len(review_ids)} reviews saved")
        
    except Exception as e:
        logger.error(f"Scraping task failed: {task_id} - {e}", exc_info=True)
        scraping_status[task_id]['status'] = 'failed'
        scraping_status[task_id]['message'] = f'Error: {str(e)}'
        scraping_status[task_id]['end_time'] = datetime.utcnow().isoformat()


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@dashboard_bp.route('/', methods=['GET'])
def dashboard():
    """
    Dashboard page route.
    
    Returns:
        HTML: Rendered dashboard
    """
    try:
        product_name = request.args.get('product', '')
        
        if not product_name:
            products = db.get_unique_products()
            if products:
                product_name = products[0]
            else:
                return render_template('dashboard.html', no_data=True)
        
        logger.info(f"Rendering dashboard for: {product_name}")
        
        return render_template(
            'dashboard.html',
            product_name=product_name,
            products=db.get_unique_products()
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('error.html', error='Failed to load dashboard'), 500


# ============================================================================
# API ROUTES - REVIEWS
# ============================================================================

@api_bp.route('/reviews', methods=['GET'])
@handle_errors
def get_reviews():
    """
    Get reviews with pagination and filtering.
    
    Query Parameters:
        product (str): Filter by product name
        sentiment (str): Filter by sentiment
        min_rating (int): Filter by minimum rating
        max_rating (int): Filter by maximum rating
        page (int): Page number (default: 1)
        per_page (int): Reviews per page (default: 20)
        search (str): Full-text search query
    
    Returns:
        JSON: List of reviews with pagination info
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', Config.API_RESULTS_PER_PAGE, type=int)
        
        # Limit per_page
        per_page = min(per_page, Config.API_MAX_RESULTS_PER_PAGE)
        
        product_name = request.args.get('product', '')
        sentiment = request.args.get('sentiment', '')
        search_query = request.args.get('search', '')
        min_rating = request.args.get('min_rating', type=int)
        max_rating = request.args.get('max_rating', type=int)
        
        # Perform search if query provided
        if search_query:
            reviews, total = db.search_reviews(search_query, product_name, page, per_page)
        # Perform filtering
        else:
            reviews, total = db.filter_reviews(
                product_name=product_name if product_name else None,
                sentiment=sentiment if sentiment else None,
                min_rating=min_rating,
                max_rating=max_rating,
                page=page,
                per_page=per_page
            )
        
        return jsonify({
            'success': True,
            'data': reviews,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch reviews'}), 500


@api_bp.route('/reviews/<review_id>', methods=['GET'])
@handle_errors
def get_review(review_id):
    """
    Get a specific review by ID.
    
    Args:
        review_id (str): Review ObjectId
    
    Returns:
        JSON: Review details
    """
    review = db.get_review_by_id(review_id)
    
    if not review:
        return jsonify({
            'success': False,
            'message': 'Review not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': review
    }), 200


@api_bp.route('/reviews', methods=['POST'])
@require_json
@handle_errors
def create_review():
    """
    Create a new review manually.
    
    Request JSON:
        {
            "product_name": "string",
            "review_text": "string",
            "rating": 1-5,
            "reviewer_name": "string",
            "review_date": "string",
            "platform": "amazon|flipkart"
        }
    
    Returns:
        JSON: Created review with ID
    """
    data = request.get_json()
    
    # Create review object
    review = models.create_review(
        product_name=data.get('product_name', ''),
        review_text=data.get('review_text', ''),
        rating=int(data.get('rating', 0)),
        reviewer_name=data.get('reviewer_name', ''),
        review_date=data.get('review_date', datetime.utcnow().isoformat()),
        platform=data.get('platform', 'amazon')
    )
    
    # Validate review
    is_valid, error_msg = review.validate()
    if not is_valid:
        return jsonify({
            'success': False,
            'message': error_msg
        }), 400
    
    # Analyze sentiment
    polarity, subjectivity = analyze_sentiment(review.review_text)
    review.polarity = polarity
    review.subjectivity = subjectivity
    review.sentiment = models.classify_sentiment(polarity)
    
    # Insert into database
    review_id = db.insert_review(review.to_dict())
    
    logger.info(f"Manual review created: {review_id}")
    
    return jsonify({
        'success': True,
        'message': 'Review created successfully',
        'review_id': review_id
    }), 201


@api_bp.route('/reviews/<review_id>', methods=['DELETE'])
@handle_errors
def delete_review(review_id):
    """
    Delete a specific review.
    
    Args:
        review_id (str): Review ObjectId
    
    Returns:
        JSON: Deletion status
    """
    deleted = db.delete_review_by_id(review_id)
    
    if not deleted:
        return jsonify({
            'success': False,
            'message': 'Review not found'
        }), 404
    
    logger.info(f"Review deleted: {review_id}")
    
    return jsonify({
        'success': True,
        'message': 'Review deleted successfully'
    }), 200


# ============================================================================
# API ROUTES - STATISTICS
# ============================================================================

@api_bp.route('/stats/product/<product_name>', methods=['GET'])
@handle_errors
def get_product_stats(product_name):
    """
    Get comprehensive statistics for a product.
    
    Args:
        product_name (str): Product name
    
    Returns:
        JSON: Product statistics
    """
    is_valid, error_msg = models.validate_product_name(product_name)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    stats = db.get_dashboard_stats(product_name)
    
    if not stats or stats.get('total_reviews', 0) == 0:
        return jsonify({
            'success': False,
            'message': 'No reviews found for this product'
        }), 404
    
    return jsonify({
        'success': True,
        'data': stats
    }), 200


@api_bp.route('/stats/sentiment', methods=['GET'])
@handle_errors
def get_sentiment_stats():
    """
    Get sentiment statistics for a product.
    
    Query Parameters:
        product (str): Product name (required)
    
    Returns:
        JSON: Sentiment statistics
    """
    product_name = request.args.get('product', '').strip()
    
    if not product_name:
        return jsonify({
            'success': False,
            'message': 'Product name is required'
        }), 400
    
    stats = db.get_sentiment_stats(product_name)
    
    if not stats or stats.get('total_reviews', 0) == 0:
        return jsonify({
            'success': False,
            'message': 'No reviews found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': stats
    }), 200


@api_bp.route('/stats/rating-distribution', methods=['GET'])
@handle_errors
def get_rating_distribution():
    """
    Get rating distribution for a product.
    
    Query Parameters:
        product (str): Product name (required)
    
    Returns:
        JSON: Rating distribution
    """
    product_name = request.args.get('product', '').strip()
    
    if not product_name:
        return jsonify({
            'success': False,
            'message': 'Product name is required'
        }), 400
    
    distribution = db.get_rating_distribution(product_name)
    
    return jsonify({
        'success': True,
        'data': distribution
    }), 200


# ============================================================================
# API ROUTES - PRODUCTS
# ============================================================================

@api_bp.route('/products', methods=['GET'])
@handle_errors
def get_products():
    """
    Get all products in database.
    
    Returns:
        JSON: List of product names
    """
    products = db.get_unique_products()
    
    return jsonify({
        'success': True,
        'data': products,
        'count': len(products)
    }), 200


# ============================================================================
# EXPORT ROUTES
# ============================================================================

@api_bp.route('/export/csv', methods=['GET'])
@handle_errors
def export_csv():
    """
    Export reviews to CSV file.
    
    Query Parameters:
        product (str): Filter by product name
        sentiment (str): Filter by sentiment
    
    Returns:
        File: CSV file for download
    """
    try:
        product_name = request.args.get('product', '').strip()
        sentiment = request.args.get('sentiment', '').strip()
        
        # Fetch all matching reviews (no pagination)
        reviews, _ = db.filter_reviews(
            product_name=product_name if product_name else None,
            sentiment=sentiment if sentiment else None,
            per_page=100000  # Get all reviews
        )
        
        if not reviews:
            return jsonify({
                'success': False,
                'message': 'No reviews to export'
            }), 404
        
        # Convert to Review objects
        review_objects = [models.review_from_dict(r) for r in reviews]
        
        # Export to CSV
        filename = utils.export_to_csv(review_objects, product_name)
        
        logger.info(f"Exported {len(reviews)} reviews to CSV: {filename}")
        
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"reviews_{product_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        ), 200
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to export CSV'
        }), 500


@api_bp.route('/export/json', methods=['GET'])
@handle_errors
def export_json():
    """
    Export reviews to JSON file.
    
    Query Parameters:
        product (str): Filter by product name
        sentiment (str): Filter by sentiment
    
    Returns:
        JSON: Reviews data
    """
    product_name = request.args.get('product', '').strip()
    sentiment = request.args.get('sentiment', '').strip()
    
    # Fetch matching reviews
    reviews, _ = db.filter_reviews(
        product_name=product_name if product_name else None,
        sentiment=sentiment if sentiment else None,
        per_page=100000
    )
    
    if not reviews:
        return jsonify({
            'success': False,
            'message': 'No reviews to export'
        }), 404
    
    return jsonify({
        'success': True,
        'data': reviews,
        'count': len(reviews),
        'exported_at': datetime.utcnow().isoformat()
    }), 200


# ============================================================================
# SEARCH HISTORY ROUTES
# ============================================================================

@api_bp.route('/search-history', methods=['POST'])
@require_json
@handle_errors
def save_search_history():
    """
    Save a search query to history.
    
    Request JSON:
        {
            "query": "string",
            "platform": "amazon|flipkart",
            "results_count": int
        }
    
    Returns:
        JSON: Status
    """
    data = request.get_json()
    
    search = models.SearchHistory(
        query=data.get('query', ''),
        platform=data.get('platform', 'amazon'),
        results_count=int(data.get('results_count', 0))
    )
    
    # Here you could save to database if needed
    logger.info(f"Search recorded: {search.query} on {search.platform}")
    
    return jsonify({
        'success': True,
        'message': 'Search saved'
    }), 201


# ============================================================================
# UTILITY ROUTES
# ============================================================================

@api_bp.route('/clear-product/<product_name>', methods=['DELETE'])
@handle_errors
def clear_product_reviews(product_name):
    """
    Delete all reviews for a product.
    
    Args:
        product_name (str): Product name
    
    Returns:
        JSON: Number of deleted reviews
    """
    is_valid, error_msg = models.validate_product_name(product_name)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    deleted_count = db.delete_reviews_by_product(product_name)
    
    logger.info(f"Deleted {deleted_count} reviews for product: {product_name}")
    
    return jsonify({
        'success': True,
        'message': f'Deleted {deleted_count} reviews',
        'deleted_count': deleted_count
    }), 200


@api_bp.route('/database/stats', methods=['GET'])
@handle_errors
def get_database_stats():
    """
    Get overall database statistics.
    
    Returns:
        JSON: Database statistics
    """
    try:
        products = db.get_unique_products()
        total_reviews = sum(db.get_sentiment_stats(p).get('total_reviews', 0) for p in products)
        
        return jsonify({
            'success': True,
            'data': {
                'total_products': len(products),
                'total_reviews': total_reviews,
                'products': products
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get database stats'
        }), 500
