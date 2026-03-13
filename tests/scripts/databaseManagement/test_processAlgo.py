import unittest
import os
import sys
import json
import sqlite3
from unittest.mock import patch, MagicMock, mock_open

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.databaseManagement.processAlgo import extract_row_count, load_data_and_columns_cleaned, ProcessAlgo

class TestProcessAlgoFunctions(unittest.TestCase):
    def test_extract_row_count(self):
        self.assertEqual(extract_row_count("data_R1000.db"), 1000)
        self.assertEqual(extract_row_count("hierarchie_db_C3_R50.db"), 50)
        self.assertIsNone(extract_row_count("invalid.db"))

    @patch('scripts.databaseManagement.processAlgo.sqlite3.connect')
    def test_load_data_and_columns_cleaned(self, mock_connect):
        mock_conn = mock_connect.return_value
        mock_cur = mock_conn.cursor.return_value
        
        # Mock table name
        mock_cur.fetchone.side_effect = [("TestTable",), (2,)]
        # Mock description
        mock_cur.description = [("Col1",), ("Col2",), ("Col3",)]
        # Mock data (3 columns) -> should add COUNT
        mock_cur.fetchall.return_value = [("A", "B", "C"), ("X", "Y", "Z")]
        
        data, columns = load_data_and_columns_cleaned("dummy.db", expected_attrib_count=3)
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], ["A", "B", "C", 1])
        self.assertEqual(columns, ["Col1", "Col2", "Col3", "COUNT"])

class TestProcessAlgo(unittest.TestCase):
    def setUp(self):
        self.proc = ProcessAlgo("test_folder", "test_timings.json")

    @patch('os.listdir')
    @patch('os.path.isfile', return_value=True)
    @patch('scripts.databaseManagement.processAlgo.extract_row_count')
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._process_file_buc')
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._save_results')
    def test_runBUC(self, mock_save, mock_process, mock_extract, mock_isfile, mock_listdir):
        mock_listdir.return_value = ["file1.db", "file2.db"]
        mock_extract.side_effect = [10, 20] # For sorting
        mock_process.side_effect = [{"res": 1}, {"res": 2}]
        
        with patch('os.path.exists', return_value=True):
            self.proc.runBUC()
        
        mock_process.assert_called()
        mock_save.assert_called_once()
        # Verify it passed a dict with both files
        results_passed = mock_save.call_args[0][0]
        self.assertIn("file1.db", results_passed)
        self.assertIn("file2.db", results_passed)

    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    @patch('os.path.exists', return_value=True)
    @patch('json.dump')
    def test_save_results_new(self, mock_json_dump, mock_exists, mock_open_file):
        new_res = {"file1.db": {"success": True, "duration_seconds": 10.0}}
        self.proc._save_results(new_res, "BUC")
        
        # Verify what was dumped
        args, kwargs = mock_json_dump.call_args
        self.assertEqual(args[0]["BUC"]["file1.db"], new_res["file1.db"])

if __name__ == '__main__':
    unittest.main()
