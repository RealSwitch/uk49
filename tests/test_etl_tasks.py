import unittest
import pandas as pd
from airflow.scripts import etl_tasks

class TestETLTasks(unittest.TestCase):
    def test_transform_empty(self):
        df = pd.DataFrame()
        result = etl_tasks.transform(df)
        self.assertIsInstance(result, pd.DataFrame)

if __name__ == '__main__':
    unittest.main()
