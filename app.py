from flask import Flask, request, jsonify
from flask_cors import CORS

from db import save_reviews_to_db
from scraper import scrape_reviews
from sentiment import analyze_sentiment

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return jsonify({"message": "Review Scraper API Running"})


@app.route("/scrape", methods=["POST"])
def scrape():
    try:
        data = request.get_json(silent=True) or {}
        url = (data.get("url") or "").strip()

        if not url:
            return jsonify({"success": False, "message": "Product URL is required"}), 400

        raw_result = scrape_reviews(url) or []
        metadata = {}
        if isinstance(raw_result, dict):
            metadata = raw_result
            raw_reviews = raw_result.get("reviews") or []
        else:
            raw_reviews = raw_result

        cleaned_reviews = []
        seen_reviews = set()

        for review in raw_reviews:
            text = str(review).strip()
            if not text or text in seen_reviews:
                continue

            normalized_text = " ".join(text.split())
            if len(normalized_text) < 20:
                continue

            seen_reviews.add(normalized_text)
            cleaned_reviews.append({
                "review": normalized_text,
                "sentiment": analyze_sentiment(normalized_text),
            })

        positive = sum(1 for item in cleaned_reviews if item["sentiment"] == "Positive")
        neutral = sum(1 for item in cleaned_reviews if item["sentiment"] == "Neutral")
        negative = sum(1 for item in cleaned_reviews if item["sentiment"] == "Negative")

        review_count = len(cleaned_reviews)
        average_rating = round((5 * positive + 3 * neutral + 1 * negative) / review_count, 1) if review_count else 0
        confidence = f"{min(99, 70 + review_count * 2)}%" if review_count else "N/A"
        recommendation = "Recommended" if positive > negative else "Needs attention"

        save_reviews_to_db(url, cleaned_reviews)

        rating_value = metadata.get("rating")
        actual_review_count = metadata.get("review_count")
        rating_text = (
            f"{rating_value}/5"
            if rating_value is not None
            else (f"{average_rating}/5" if review_count else "N/A")
        )

        return jsonify({
            "success": True,
            "total_reviews": review_count,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "reviews": [item["review"] for item in cleaned_reviews],
            "rating": rating_text,
            "reviewCount": actual_review_count if actual_review_count is not None else review_count,
            "confidence": confidence,
            "recommendation": recommendation,
        })

    except Exception as exc:
        app.logger.exception("Scrape failed")
        return jsonify({"success": False, "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)