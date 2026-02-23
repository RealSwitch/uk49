import unittest
from api import stats, database

class TestStats(unittest.TestCase):
    def test_rolling_frequency_empty(self):
        result = stats.get_rolling_frequency(database.engine, target_date=None)
        self.assertIn('draw_date', result)
        self.assertIn('frequencies', result)

if __name__ == '__main__':
    unittest.main()
