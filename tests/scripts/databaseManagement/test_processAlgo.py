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
        mock_process.side_effect = [{"success": True, "duration_seconds": 1.0}, {"success": True, "duration_seconds": 2.0}]
        
        self.proc.runBUC()
        
        mock_process.assert_called()
        mock_save.assert_called_once()
        results_passed = mock_save.call_args[0][0]
        self.assertIn("file1.db", results_passed)

    @patch('os.listdir')
    @patch('scripts.databaseManagement.processAlgo.extract_row_count', return_value=10)
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._process_file_star')
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._save_results')
    def test_runStarCubing(self, mock_save, mock_process, mock_extract, mock_listdir):
        mock_listdir.return_value = ["file1.db"]
        mock_process.return_value = {"success": True, "duration_seconds": 1.0}
        self.proc.runStarCubing()
        mock_process.assert_called()
        mock_save.assert_called_with(unittest.mock.ANY, key="StarCubing")

    @patch('os.listdir')
    @patch('scripts.databaseManagement.processAlgo.extract_row_count', return_value=10)
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._process_file_closet')
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._save_results')
    def test_runClosetCube(self, mock_save, mock_process, mock_extract, mock_listdir):
        mock_listdir.return_value = ["file1.db"]
        mock_process.return_value = {"success": True, "duration_seconds": 1.0}
        with patch('os.path.exists', return_value=True):
            self.proc.runClosetCube()
        mock_process.assert_called()
        mock_save.assert_called_with(unittest.mock.ANY, key="ClosetCube")

    @patch('os.listdir')
    @patch('scripts.databaseManagement.processAlgo.extract_row_count', return_value=10)
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._process_file_hierarchical_buc')
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._save_results')
    def test_runHierarchicalBUC(self, mock_save, mock_process, mock_extract, mock_listdir):
        mock_listdir.return_value = ["file1.db"]
        mock_process.return_value = {"success": True, "duration_seconds": 1.0}
        self.proc.runHierarchicalBUC()
        mock_process.assert_called()

    @patch('os.listdir')
    @patch('scripts.databaseManagement.processAlgo.extract_row_count', return_value=10)
    @patch('scripts.databaseManagement.processAlgo.HierarchicalStarCubing')
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._save_results')
    def test_runHierarchicalStarCubing(self, mock_save, mock_hstar, mock_extract, mock_listdir):
        mock_listdir.return_value = ["file1.db"]
        mock_hstar.return_value.run_from_db.return_value = {"success": True, "duration_seconds": 1.0}
        self.proc.runHierarchicalStarCubing()
        mock_hstar.return_value.run_from_db.assert_called()

    @patch('os.listdir')
    @patch('os.path.isfile', return_value=True)
    @patch('scripts.databaseManagement.processAlgo.extract_row_count', return_value=10)
    @patch('scripts.databaseManagement.processAlgo.pd.read_sql_query')
    @patch('scripts.databaseManagement.processAlgo.sqlite3.connect')
    @patch('scripts.databaseManagement.processAlgo.HierarchicalClosetCube')
    @patch('scripts.databaseManagement.processAlgo.ProcessAlgo._save_results')
    def test_runHierarchicalClosetCube(self, mock_save, mock_hcloset, mock_conn, mock_read, mock_extract, mock_isfile, mock_listdir):
        mock_listdir.return_value = ["file1.db"]
        
        import pandas as pd
        mock_df = pd.DataFrame({
            "Geography": ["France"],
            "Time": ["2021"],
            "Food": ["Fruits"],
            "COUNT": [1]
        })
        mock_read.return_value = mock_df
        
        mock_hcloset.return_value.generate_closed_cube.return_value = []
        
        self.proc.runHierarchicalClosetCube()
        mock_hcloset.return_value.generate_closed_cube.assert_called()

    @patch('builtins.open', new_callable=mock_open, read_data='{"Algo1": {"file_R100": {"success": true, "duration_seconds": 1.0}}}')
    @patch('os.makedirs')
    def test_plot_execution_times(self, mock_makedirs, mock_file):
        self.proc.plot_execution_times_from_json("dummy.json", "out_folder")
        # Check if some output file was "opened" for writing
        # The function writes multiple files, let's just check it was called
        self.assertTrue(mock_file.called)

    @patch('builtins.open', new_callable=mock_open, read_data='{"BUC": {"file_R100": {"success": true, "duration_seconds": 1.0}}}')
    @patch('os.makedirs')
    def test_generate_execution_graphs_from_summary(self, mock_makedirs, mock_file):
        self.proc.generate_execution_graphs_from_summary("dummy.json", "out_folder")
        self.assertTrue(mock_file.called)

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
