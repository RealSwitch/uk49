import unittest
import pandas as pd
from app import streamlit_app

class TestStreamlitApp(unittest.TestCase):
    def test_compute_frequency_empty(self):
        df = pd.DataFrame()
        freq = streamlit_app.compute_frequency(df)
        self.assertIsInstance(freq, pd.DataFrame)
        self.assertListEqual(list(freq.columns), ['number','count'])

if __name__ == '__main__':
    unittest.main()
