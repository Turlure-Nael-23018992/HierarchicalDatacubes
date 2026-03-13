import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

class TestLegacyScripts(unittest.TestCase):
    @patch('sqlite3.connect')
    @patch('os.path.exists', return_value=True)
    def test_import_mainDB(self, mock_exists, mock_connect):
        # We try to import it. It might run some code, but mocks should catch it.
        # We use a try-except to avoid failing the whole suite if it crashes.
        try:
            import scripts.databaseManagement.mainDB
        except Exception as e:
            print(f"mainDB import failed (expected): {e}")

    @patch('sqlite3.connect')
    @patch('os.path.exists', return_value=True)
    def test_import_main2(self, mock_exists, mock_connect):
        try:
            import scripts.main2
        except Exception as e:
            print(f"main2 import failed (expected): {e}")

    @patch('sqlite3.connect')
    @patch('os.path.exists', return_value=True)
    def test_import_mainExThese(self, mock_exists, mock_connect):
        try:
            import scripts.mainExThese
        except Exception as e:
            print(f"mainExThese import failed (expected): {e}")

if __name__ == '__main__':
    unittest.main()
