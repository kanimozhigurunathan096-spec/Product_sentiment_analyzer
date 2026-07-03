from urllib.parse import urlparse

from amazon import amazon_scraper
from flipkart import flipkart_scraper


def scrape_reviews(product_url):
    domain = urlparse(product_url or "").netloc.lower()

    print("Website:", domain)

    if "amazon" in domain:
        return amazon_scraper(product_url)

    if "flipkart" in domain:
        return flipkart_scraper(product_url)

    raise ValueError("Only Amazon and Flipkart product URLs are supported.")