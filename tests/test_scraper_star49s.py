import unittest
from airflow.scripts import scraper_star49s

class TestScraperStar49s(unittest.TestCase):
    def test_scrape_url_with_playwright_invalid(self):
        df = scraper_star49s.scrape_url_with_playwright('http://invalid-url', 'lunchtime')
        self.assertTrue(hasattr(df, 'empty'))

if __name__ == '__main__':
    unittest.main()
