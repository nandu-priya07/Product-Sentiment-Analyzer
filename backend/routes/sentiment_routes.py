"""Routes — /api/sentiment"""

from flask import Blueprint, jsonify
from services.db import get_reviews_for_product, get_product_by_id
from services.sentiment import (
    analyze_reviews, compute_summary, compute_word_frequency,
    compute_trend, compute_rating_distribution
)

sentiment_bp = Blueprint("sentiment", __name__)


@sentiment_bp.route("/sentiment/<product_id>", methods=["GET"])
def get_sentiment(product_id: str):
    product = get_product_by_id(product_id)
    if product is None:
        # MongoDB may be offline (demo mode) — return a clear message
        return jsonify({
            "error": "Product not found. The database may be offline (demo mode). "
                     "Use the main search to analyze products — results are computed live."
        }), 503

    reviews = get_reviews_for_product(product_id)
    if not reviews:
        return jsonify({
            "error": "No reviews found for this product. "
                     "The database may be in demo mode. Try re-searching the product."
        }), 404

    # Re-analyze in case they weren't stored with sentiment scores
    analyzed = analyze_reviews(reviews)

    return jsonify({
        "product_id": product_id,
        "product_title": product.get("title", "Unknown"),
        "summary": compute_summary(analyzed),
        "word_frequency": compute_word_frequency(analyzed),
        "trend": compute_trend(analyzed),
        "rating_distribution": compute_rating_distribution(analyzed),
    }), 200
