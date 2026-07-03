import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import PyMongoError

FALLBACK_FILE = Path(__file__).with_name("reviews_cache.json")


def _load_env_file():
    env_values = {}
    for candidate in [Path(__file__).resolve().parent / ".env", Path(__file__).resolve().parent.parent / ".env"]:
        if not candidate.exists():
            continue

        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_values[key.strip()] = value.strip().strip('"').strip("'")

    return env_values


ENV_VALUES = _load_env_file()
MONGO_URI = os.getenv("MONGO_URI") or ENV_VALUES.get("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME") or ENV_VALUES.get("MONGO_DB_NAME", "sentiment_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME") or ENV_VALUES.get("MONGO_COLLECTION_NAME", "reviews")

client = None
db = None
reviews_collection = None


def _connect_to_mongo():
    global client, db, reviews_collection

    if reviews_collection is not None:
        return reviews_collection

    if not MONGO_URI:
        print("MongoDB is not configured. Set MONGO_URI in a .env file or environment variable.")
        return None

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connect=False)
        client.admin.command("ping")
        db = client[MONGO_DB_NAME]
        reviews_collection = db[MONGO_COLLECTION_NAME]
        return reviews_collection
    except Exception as exc:
        print(f"MongoDB connection failed: {exc}")
        print("Check your Atlas cluster status, username/password, and that your IP address is whitelisted in MongoDB Atlas.")
        return None


def _save_to_fallback_file(product_url, documents):
    try:
        existing = []
        if FALLBACK_FILE.exists():
            existing = json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))

        existing.extend(documents)
        FALLBACK_FILE.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
        return True
    except Exception as exc:
        print(f"Fallback file write failed: {exc}")
        return False


def save_reviews_to_db(product_url, reviews):
    documents = []
    for review in reviews:
        if isinstance(review, dict):
            text = review.get("review", "").strip()
            sentiment = review.get("sentiment", "Neutral")
        else:
            text = str(review).strip()
            sentiment = "Neutral"

        if not text:
            continue

        documents.append({
            "product": product_url,
            "review": text,
            "sentiment": sentiment,
            "created_at": datetime.now(timezone.utc),
        })

    if not documents:
        return False

    collection = _connect_to_mongo()
    if collection is None:
        print("MongoDB is unavailable; saving reviews to fallback file")
        return _save_to_fallback_file(product_url, documents)

    try:
        collection.insert_many(documents, ordered=False)
        return True
    except PyMongoError as exc:
        print(f"MongoDB insert failed: {exc}")
        return _save_to_fallback_file(product_url, documents)