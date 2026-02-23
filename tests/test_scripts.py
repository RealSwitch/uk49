import unittest
import importlib

class TestScripts(unittest.TestCase):
    def test_run_scraper_import(self):
        mod = importlib.import_module('scripts.run_scraper')
        self.assertTrue(hasattr(mod, 'main'))

    def test_analyze_html_import(self):
        mod = importlib.import_module('scripts.analyze_html')
        self.assertTrue(mod is not None)

if __name__ == '__main__':
    unittest.main()
