"""
Flask Application Entry Point
Product Sentiment Analyzer & Review Dashboard — Backend API
"""

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

# Routes
from routes.scraper_routes import scraper_bp
from routes.products_routes import products_bp
from routes.sentiment_routes import sentiment_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["DEBUG"] = Config.DEBUG

    # CORS — allow frontend origins
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

    # Register blueprints under /api
    app.register_blueprint(scraper_bp, url_prefix="/api")
    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(sentiment_bp, url_prefix="/api")

    # Health check
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "service": "Product Sentiment Analyzer API",
            "version": "1.0.0",
        }), 200

    # 404 handler
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    # 500 handler
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
