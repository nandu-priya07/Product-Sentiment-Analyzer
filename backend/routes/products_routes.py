"""Routes — /api/products"""

from flask import Blueprint, jsonify
from services.db import get_all_products, get_product_by_id, delete_product, get_reviews_for_product
from services.sentiment import compute_summary, compute_word_frequency, compute_trend, compute_rating_distribution

products_bp = Blueprint("products", __name__)


@products_bp.route("/products", methods=["GET"])
def list_products():
    products = get_all_products(limit=50)
    return jsonify({"products": products, "count": len(products)}), 200


@products_bp.route("/products/<product_id>", methods=["GET"])
def get_product(product_id: str):
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    reviews = get_reviews_for_product(product_id)
    summary = compute_summary(reviews) if reviews else {}
    word_freq = compute_word_frequency(reviews) if reviews else {}
    trend = compute_trend(reviews) if reviews else []
    rating_dist = product.get("rating_distribution") or (compute_rating_distribution(reviews) if reviews else [])

    if summary:
        summary["marketplace_rating"] = product.get("rating")
        summary["marketplace_review_count"] = product.get("review_count")
        summary["analysis_review_count"] = len(reviews)

    return jsonify({
        "product": product,
        "reviews": reviews,
        "summary": summary,
        "word_frequency": word_freq,
        "trend": trend,
        "rating_distribution": rating_dist,
    }), 200


@products_bp.route("/products/<product_id>", methods=["DELETE"])
def remove_product(product_id: str):
    success = delete_product(product_id)
    if not success:
        return jsonify({"error": "Product not found or could not be deleted"}), 404
    return jsonify({"message": "Product deleted successfully"}), 200
