import re
import time

import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from driver import get_driver


def _clean_review_text(text):
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return ""
    if len(cleaned) < 20:
        return ""
    return cleaned


def _extract_reviews_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    reviews = []
    seen = set()
    candidates = []

    for selector in ["[data-hook='review-body']", ".review-text-content", ".review-text", "[class*='review']"]:
        for item in soup.select(selector):
            text = _clean_review_text(item.get_text(" ", strip=True))
            if text and text not in seen:
                seen.add(text)
                candidates.append(text)

    for item in soup.find_all(["span", "div", "p"]):
        text = _clean_review_text(item.get_text(" ", strip=True))
        if not text:
            continue
        if len(text) < 30 or text in seen:
            continue
        if any(marker in text.lower() for marker in ["verified purchase", "was this review helpful", "report abuse", "see all reviews"]):
            continue
        candidates.append(text)

    for text in candidates:
        if text not in seen:
            seen.add(text)
            reviews.append(text)

    return reviews[:20]


def amazon_scraper(product_url):
    reviews = []
    driver = None

    try:
        driver = get_driver()
        driver.get(product_url)
        time.sleep(4)

        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(2)

        review_elements = []
        try:
            review_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[data-hook='review-body']"))
            )
        except TimeoutException:
            review_elements = driver.find_elements(By.CSS_SELECTOR, "span[data-hook='review-body']")

        for review in review_elements:
            text = _clean_review_text(review.text)
            if text and text not in reviews:
                reviews.append(text)

        try:
            all_review = driver.find_element(By.PARTIAL_LINK_TEXT, "See all reviews")
            all_review.click()
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[data-hook='review-body']"))
            )
            for review in driver.find_elements(By.CSS_SELECTOR, "span[data-hook='review-body']"):
                text = _clean_review_text(review.text)
                if text and text not in reviews:
                    reviews.append(text)
        except Exception:
            pass
    except Exception as exc:
        print(f"Amazon scraper failed: {exc}")
    finally:
        if driver:
            driver.quit()

    if reviews:
        return reviews

    try:
        response = requests.get(product_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        response.raise_for_status()
        return _extract_reviews_from_html(response.text)
    except Exception as exc:
        print(f"Amazon fallback scraper failed: {exc}")
        return []