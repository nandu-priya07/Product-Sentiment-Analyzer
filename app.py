"""
Product Sentiment Analyzer - Main Flask Application

This module initializes and configures the Flask web application.
It sets up the database connection, registers routes, and handles errors.
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """
    Application factory function to create and configure Flask app.
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    from config import Config
    app.config.from_object(Config)
    
    # Enable CORS for API endpoints
    CORS(app, resources={
        r"/api/*": {"origins": "*", "methods": ["GET", "POST", "DELETE", "OPTIONS"]}
    })
    
    logger.info("Flask app initialized with configuration loaded")
    
    return app


# Create Flask application instance
app = create_app()


# ============================================================================
# IMPORT MODULES (After app creation to avoid circular imports)
# ============================================================================

try:
    from database import init_db, get_db_connection
    from routes import (
        home_bp,
        search_bp,
        scraper_bp,
        dashboard_bp,
        api_bp
    )
    logger.info("All modules imported successfully")
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)


# ============================================================================
# REGISTER BLUEPRINTS
# ============================================================================

app.register_blueprint(home_bp)
app.register_blueprint(search_bp)
app.register_blueprint(scraper_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp)

logger.info("All blueprints registered successfully")


# ============================================================================
# INITIALIZE DATABASE
# ============================================================================

with app.app_context():
    try:
        db = init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    logger.warning(f"Bad request error: {error}")
    return jsonify({
        'success': False,
        'message': 'Bad request. Please check your input.',
        'error': str(error)
    }), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    logger.warning(f"404 error: {error}")
    return jsonify({
        'success': False,
        'message': 'Resource not found.',
        'error': str(error)
    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 Internal Server errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'message': 'Internal server error. Please try again later.',
        'error': str(error)
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle any unhandled exceptions."""
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify({
        'success': False,
        'message': 'An unexpected error occurred.',
        'error': str(error)
    }), 500


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        JSON: Health status with timestamp
    """
    try:
        db_conn = get_db_connection()
        db_status = "connected" if db_conn else "disconnected"
    except Exception as e:
        logger.error(f"Health check - Database error: {e}")
        db_status = "error"
    
    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'version': '1.0.0'
    }), 200 if db_status == 'connected' else 503


# ============================================================================
# BEFORE REQUEST HOOK
# ============================================================================

@app.before_request
def before_request():
    """Log incoming requests."""
    if request.method != 'OPTIONS':
        logger.debug(f"{request.method} {request.path}")


# ============================================================================
# AFTER REQUEST HOOK
# ============================================================================

@app.after_request
def after_request(response):
    """Add security headers and CORS headers to response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


# ============================================================================
# TEMPLATE CONTEXT PROCESSORS
# ============================================================================

@app.context_processor
def inject_version():
    """Inject app version into all templates."""
    return {'app_version': '1.0.0'}


@app.context_processor
def inject_now():
    """Inject current year for footer."""
    return {'current_year': datetime.now().year}


# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    """
    Run the Flask development server.
    
    This is used for local development only.
    For production, use a WSGI server like Gunicorn or uWSGI.
    """
    
    # Create necessary directories if they don't exist
    os.makedirs('exports', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    logger.info("Ensured exports and data directories exist")
    
    # Get debug mode from environment
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    use_reloader = debug_mode and os.name != 'nt'
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    
    logger.info(f"Starting Flask app in {'DEBUG' if debug_mode else 'PRODUCTION'} mode")
    logger.info(f"Server running at http://{host}:{port}")
    if debug_mode and os.name == 'nt':
        logger.info("Debug reloader disabled on Windows to avoid restart issues")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        use_reloader=use_reloader,
        use_debugger=debug_mode
    )
