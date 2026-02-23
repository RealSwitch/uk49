import unittest
from api import database

class TestDatabase(unittest.TestCase):
    def test_connection(self):
        self.assertTrue(database.test_connection())

if __name__ == '__main__':
    unittest.main()
