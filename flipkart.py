import json
import re

import requests
from bs4 import BeautifulSoup


def _clean_review_text(text):
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return ""
    if len(cleaned) < 25:
        return ""
    return cleaned


def _extract_initial_state(text):
    marker = "window.__INITIAL_STATE__"
    start = text.find(marker)
    if start == -1:
        return None

    start = text.find("=", start)
    if start == -1:
        return None

    start = text.find("{", start)
    if start == -1:
        return None

    brace_level = 0
    in_string = False
    escaped = False

    for idx, char in enumerate(text[start:], start):
        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            brace_level += 1
        elif char == "}":
            brace_level -= 1
            if brace_level == 0:
                return text[start : idx + 1]

    return None


def _extract_reviews_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    reviews = []

    for element in soup.find_all(["div", "span", "p"]):
        text = _clean_review_text(element.get_text(" ", strip=True))
        if not text or text in reviews:
            continue
        if any(marker in text.lower() for marker in ["reviews", "rating", "view details", "add to cart"]):
            continue
        reviews.append(text)

    return reviews[:20]


def _extract_flipkart_data(html):
    json_text = _extract_initial_state(html)
    if not json_text:
        return None

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return None

    page_data = data.get("multiWidgetState", {}).get("pageDataResponse", {})
    seo_data = page_data.get("seoData", {})
    schema_items = seo_data.get("schema", [])

    rating = None
    review_count = None
    reviews = []

    for item in schema_items:
        if not isinstance(item, dict):
            continue

        aggregate = item.get("aggregateRating")
        if isinstance(aggregate, dict):
            if rating is None:
                rating = aggregate.get("ratingValue")
            if review_count is None:
                review_count = aggregate.get("reviewCount")

        raw_reviews = item.get("review")
        if isinstance(raw_reviews, list):
            for review in raw_reviews:
                if not isinstance(review, dict):
                    continue
                body = review.get("reviewBody") or review.get("reviewText") or review.get("description") or ""
                cleaned = _clean_review_text(body)
                if cleaned and cleaned not in reviews:
                    reviews.append(cleaned)

    page_context = page_data.get("pageContext", {})
    psi_pr = page_context.get("fdpEventTracking", {}).get("events", {}).get("psi", {}).get("pr", {})
    if isinstance(psi_pr, dict):
        if rating is None:
            rating = psi_pr.get("rating")
        if review_count is None:
            review_count = psi_pr.get("reviewsCount")

    return {"rating": rating, "review_count": review_count, "reviews": reviews}


def flipkart_scraper(product_url):
    metadata = {"rating": None, "review_count": None}
    reviews = []
    try:
        response = requests.get(
            product_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.flipkart.com/",
            },
            timeout=20,
        )
        response.raise_for_status()

        extracted = _extract_flipkart_data(response.text)
        if extracted:
            metadata["rating"] = extracted.get("rating")
            metadata["review_count"] = extracted.get("review_count")
            reviews.extend(extracted.get("reviews", []))

        fallback_reviews = _extract_reviews_from_html(response.text)
        for review in fallback_reviews:
            if review not in reviews:
                reviews.append(review)

    except Exception as exc:
        print(f"Flipkart scraper failed: {exc}")

    return {"reviews": reviews[:20], "rating": metadata["rating"], "review_count": metadata["review_count"]}
