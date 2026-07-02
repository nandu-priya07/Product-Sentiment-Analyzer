from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId
from datetime import datetime
from config import Config
import json

# ─── Connection ───────────────────────────────────────────────────────────────
_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        try:
            _client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
            _client.admin.command("ping")
            _db = _client.get_database()
            print("SUCCESS: Connected to MongoDB")
        except ConnectionFailure as e:
            print(f"WARNING: MongoDB not reachable: {e} — running in demo mode")
            _db = None
    return _db


# ─── Helper ───────────────────────────────────────────────────────────────────
def _to_str_id(doc):
    """Convert ObjectId to string for JSON serialization."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ─── Products ─────────────────────────────────────────────────────────────────
def save_product(product_data: dict) -> str:
    db = get_db()
    if db is None:
        return product_data.get("_id", "demo-id")

    product_data["scraped_at"] = datetime.utcnow()
    result = db.products.insert_one(product_data)
    return str(result.inserted_id)


def get_all_products(limit: int = 50) -> list:
    db = get_db()
    if db is None:
        return []
    products = list(db.products.find().sort("scraped_at", -1).limit(limit))
    return [_to_str_id(p) for p in products]


def get_product_by_id(product_id: str) -> dict | None:
    db = get_db()
    if db is None:
        return None
    try:
        doc = db.products.find_one({"_id": ObjectId(product_id)})
        return _to_str_id(doc)
    except Exception:
        return None


def delete_product(product_id: str) -> bool:
    db = get_db()
    if db is None:
        return False
    try:
        db.reviews.delete_many({"product_id": product_id})
        result = db.products.delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0
    except Exception:
        return False


# ─── Reviews ──────────────────────────────────────────────────────────────────
def save_reviews(reviews: list) -> int:
    db = get_db()
    if db is None:
        return 0
    if not reviews:
        return 0
    result = db.reviews.insert_many(reviews)
    return len(result.inserted_ids)


def get_reviews_for_product(product_id: str) -> list:
    db = get_db()
    if db is None:
        return []
    reviews = list(db.reviews.find({"product_id": product_id}).sort("date", -1))
    return [_to_str_id(r) for r in reviews]
