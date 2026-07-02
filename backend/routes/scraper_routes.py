"""Routes — /api/scrape"""

from flask import Blueprint, request, jsonify
from services.scraper import scrape_product
from services.sentiment import analyze_reviews, compute_summary, compute_word_frequency, compute_trend, compute_rating_distribution
from services.db import save_product, save_reviews

scraper_bp = Blueprint("scraper", __name__)


@scraper_bp.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    if not data or not data.get("query"):
        return jsonify({"error": "Missing 'query' in request body"}), 400

    query = data["query"].strip()
    source = data.get("source", "both").lower()

    if source not in ("amazon", "flipkart", "both"):
        return jsonify({"error": "source must be 'amazon', 'flipkart', or 'both'"}), 400

    try:
        # 1. Scrape
        scraped = scrape_product(query, source)
        product = scraped["product"]
        raw_reviews = scraped["reviews"]

        # 2. Sentiment analysis on all reviews
        analyzed_reviews = analyze_reviews(raw_reviews)

        # 3. Aggregate stats
        summary = compute_summary(analyzed_reviews)
        word_freq = compute_word_frequency(analyzed_reviews)
        trend = compute_trend(analyzed_reviews)
        rating_dist = scraped.get("rating_distribution") or compute_rating_distribution(analyzed_reviews)

        # 4. Attach summary to product
        summary["marketplace_rating"] = product.get("rating")
        summary["marketplace_review_count"] = product.get("review_count")
        summary["analysis_review_count"] = len(analyzed_reviews)
        product["sentiment_summary"] = summary
        product["rating_distribution"] = rating_dist

        # 5. Persist to DB
        product_id = save_product(product)
        for rev in analyzed_reviews:
            rev["product_id"] = product_id
        save_reviews(analyzed_reviews)

        # Convert _id to string for JSON serialization
        if "_id" in product:
            product["_id"] = str(product["_id"])
        for rev in analyzed_reviews:
            if "_id" in rev:
                rev["_id"] = str(rev["_id"])

        return jsonify({
            "product_id": product_id,
            "product": product,
            "reviews": analyzed_reviews,
            "summary": summary,
            "word_frequency": word_freq,
            "trend": trend,
            "rating_distribution": rating_dist,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
