"""
Sentiment Analysis Service
Uses VADER (primary) + TextBlob (secondary) for NLP sentiment classification.
Provides: per-review classification, aggregate stats, keyword frequency, trend data.
"""

import re
from collections import Counter
from datetime import datetime, timedelta
import random

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

_analyzer = SentimentIntensityAnalyzer()

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "did", "do", "does",
    "doing", "don", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into",
    "is", "it", "its", "itself", "me", "more", "most", "my", "myself",
    "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or",
    "other", "our", "ours", "ourselves", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "you", "your", "yours", "yourself",
    "yourselves",
    # Generic e-commerce filler words (NOT sentiment words)
    "product", "item", "thing", "buy", "bought", "purchase", "amazon",
    "flipkart", "get", "got", "one", "use", "used", "would", "also",
    "really", "much", "many", "even", "still", "just", "can", "could",
    "will", "time", "like", "well", "very",
    # NOTE: intentionally keeping: good, great, bad, excellent, terrible, etc.
    # so that word frequency reflects real sentiment vocabulary
}


# ─── Core Sentiment ───────────────────────────────────────────────────────────
def analyze_review(text: str) -> dict:
    """Run VADER + TextBlob on a single review text."""
    vs = _analyzer.polarity_scores(text)
    compound = vs["compound"]

    # Classification thresholds
    if compound >= 0.05:
        sentiment = "Positive"
        color = "#22c55e"
    elif compound <= -0.05:
        sentiment = "Negative"
        color = "#ef4444"
    else:
        sentiment = "Neutral"
        color = "#f59e0b"

    # TextBlob for subjectivity
    blob = TextBlob(text)

    return {
        "sentiment": sentiment,
        "compound_score": round(compound, 4),
        "positive_score": round(vs["pos"], 4),
        "negative_score": round(vs["neg"], 4),
        "neutral_score": round(vs["neu"], 4),
        "subjectivity": round(blob.sentiment.subjectivity, 4),
        "color": color,
    }


# ─── Batch Analysis ───────────────────────────────────────────────────────────
def analyze_reviews(reviews: list) -> list:
    """Analyze a list of review dicts (must have 'text' key)."""
    enriched = []
    for review in reviews:
        result = analyze_review(review.get("text", ""))
        enriched.append({**review, **result})
    return enriched


# ─── Aggregate Stats ──────────────────────────────────────────────────────────
def compute_summary(reviews: list) -> dict:
    """Compute aggregate sentiment stats from a list of analyzed reviews."""
    if not reviews:
        return {}

    total = len(reviews)
    pos = sum(1 for r in reviews if r.get("sentiment") == "Positive")
    neg = sum(1 for r in reviews if r.get("sentiment") == "Negative")
    neu = total - pos - neg
    avg_compound = sum(r.get("compound_score", 0) for r in reviews) / total
    avg_rating = sum(r.get("rating", 3) for r in reviews) / total

    return {
        "total_reviews": total,
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": neu,
        "positive_pct": round(pos / total * 100, 1),
        "negative_pct": round(neg / total * 100, 1),
        "neutral_pct": round(neu / total * 100, 1),
        "avg_compound": round(avg_compound, 4),
        "avg_rating": round(avg_rating, 2),
        "overall_sentiment": (
            "Positive" if avg_compound >= 0.05
            else "Negative" if avg_compound <= -0.05
            else "Neutral"
        ),
    }


# ─── Keyword / Word Frequency ─────────────────────────────────────────────────
def _tokenize(text: str) -> list:
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def compute_word_frequency(reviews: list, top_n: int = 20) -> dict:
    """Return top N words split by positive and negative reviews."""
    pos_words, neg_words, all_words = [], [], []

    for review in reviews:
        tokens = _tokenize(review.get("text", ""))
        all_words.extend(tokens)
        if review.get("sentiment") == "Positive":
            pos_words.extend(tokens)
        elif review.get("sentiment") == "Negative":
            neg_words.extend(tokens)

    def top(word_list):
        return [{"word": w, "count": c} for w, c in Counter(word_list).most_common(top_n)]

    return {
        "all": top(all_words),
        "positive": top(pos_words),
        "negative": top(neg_words),
    }


# ─── Trend Over Time ──────────────────────────────────────────────────────────
def compute_trend(reviews: list) -> list:
    """
    Group reviews by date and compute average compound score per day.
    Returns a list sorted by date ascending.
    If all reviews share the same date (common with mock data), spreads them
    across weekly buckets so the chart is still meaningful.
    """
    from collections import defaultdict

    daily = defaultdict(list)
    for review in reviews:
        date_str = review.get("date", "")
        if date_str:
            try:
                # Normalize to YYYY-MM-DD
                date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
                daily[date_obj.strftime("%Y-%m-%d")].append(review.get("compound_score", 0))
            except ValueError:
                pass

    trend = []
    for date, scores in sorted(daily.items()):
        avg = sum(scores) / len(scores)
        trend.append({
            "date": date,
            "avg_sentiment": round(avg, 4),
            "review_count": len(scores),
            "label": "Positive" if avg >= 0.05 else "Negative" if avg <= -0.05 else "Neutral",
        })

    # If only one date bucket, spread reviews into weekly buckets for a useful chart
    if len(trend) <= 1 and reviews:
        weekly = defaultdict(list)
        for review in reviews:
            date_str = review.get("date", "")
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    # Round down to the start of the week (Monday)
                    week_start = date_obj - timedelta(days=date_obj.weekday())
                    weekly[week_start.strftime("%Y-%m-%d")].append(review.get("compound_score", 0))
                except ValueError:
                    pass

        if len(weekly) > 1:
            trend = []
            for date, scores in sorted(weekly.items()):
                avg = sum(scores) / len(scores)
                trend.append({
                    "date": date,
                    "avg_sentiment": round(avg, 4),
                    "review_count": len(scores),
                    "label": "Positive" if avg >= 0.05 else "Negative" if avg <= -0.05 else "Neutral",
                })

    return trend


# ─── Rating Distribution ──────────────────────────────────────────────────────
def compute_rating_distribution(reviews: list) -> list:
    """Count reviews per star rating (1–5)."""
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in reviews:
        rating = int(review.get("rating", 3))
        if 1 <= rating <= 5:
            dist[rating] += 1

    return [{"stars": k, "count": v} for k, v in dist.items()]
