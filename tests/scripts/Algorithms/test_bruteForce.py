import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Attempt to import pandas, or mock it if not available (though we added it to pyproject.toml)
try:
    import pandas as pd
except ImportError:
    pd = None

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.Algorithms.bruteForce import powerset, bruteForce

class TestBruteForce(unittest.TestCase):
    def test_powerset(self):
        s = [1, 2]
        res = powerset(s)
        # combinations of 1 and 2: (1,), (2,), (1, 2)
        self.assertEqual(len(res), 3)
        self.assertIn((1,), res)
        self.assertIn((2,), res)
        self.assertIn((1, 2), res)

    @unittest.skipIf(pd is None, "pandas not installed")
    @patch('scripts.Algorithms.bruteForce.time.time', side_effect=[0, 1])
    def test_bruteForce(self, mock_time):
        # Create a sample DataFrame
        df = pd.DataFrame({
            "année": [2021, 2021],
            "mois": ["Jan", "Fev"],
            "pays": ["FR", "FR"],
            "ville": ["Paris", "Paris"],
            "ventes": [100, 200]
        })
        
        # Capture print output if needed, but for now just run to ensure no crash
        with patch('builtins.print'):
            bruteForce(df)
        
        # Verify time.time was called twice
        self.assertEqual(mock_time.call_count, 2)

if __name__ == '__main__':
    unittest.main()
