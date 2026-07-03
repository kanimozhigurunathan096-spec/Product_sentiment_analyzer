import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app


class ScrapeEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("app.save_reviews_to_db")
    @patch("app.scrape_reviews", return_value=["This product is excellent and works really well for everyday use."])
    def test_scrape_endpoint_returns_summary_and_saves_reviews(self, scrape_mock, save_mock):
        response = self.client.post(
            "/scrape",
            json={"url": "https://www.amazon.in/product"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["total_reviews"], 1)
        self.assertEqual(payload["positive"], 1)
        self.assertEqual(payload["negative"], 0)
        self.assertEqual(payload["neutral"], 0)
        save_mock.assert_called_once()

    @patch("app.save_reviews_to_db")
    @patch("app.scrape_reviews", return_value={"reviews": ["This product is excellent."], "rating": 4.6, "review_count": 150})
    def test_scrape_endpoint_returns_flipkart_metadata(self, scrape_mock, save_mock):
        response = self.client.post(
            "/scrape",
            json={"url": "https://www.flipkart.com/product"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["total_reviews"], 1)
        self.assertEqual(payload["reviewCount"], 150)
        self.assertEqual(payload["rating"], "4.6/5")
        self.assertEqual(payload["positive"], 1)
        save_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
