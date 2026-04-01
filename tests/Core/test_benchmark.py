import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock, call

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Core.benchmark import Benchmark
from scripts.Algorithms.BUC import BUC
from scripts.Algorithms.HierarchicalBUC import HierarchicalBUC

class TestBenchmark(unittest.TestCase):
    
    @patch('Core.benchmark.Main')
    @patch('Core.benchmark.Benchmark.save_single_result')
    def test_run_buc(self, mock_save_single_result, mock_main_class):
        # Configure the mock for Main
        mock_main_instance = mock_main_class.return_value
        mock_main_instance.time = 1.23

        # Temporarily patch COLS and ROWS in benchmark module to make it fast
        with patch('Core.benchmark.COLS', [3]), patch('Core.benchmark.ROWS', [10]), patch('Core.benchmark.os.path.exists', return_value=True):
            bench = Benchmark("BUC", isPrinted=False)
            bench.run()

        # Check if Main was called with the right DB logic and runBUC was called
        mock_main_class.assert_called()
        mock_main_instance.runBUC.assert_called_once()
        
        self.assertEqual(bench.times[10], [1.23])
        mock_save_single_result.assert_called_once_with(10, 1.23)

    @patch('Core.benchmark.Main')
    @patch('Core.benchmark.Benchmark.save_single_result')
    def test_run_hierarchical_buc(self, mock_save_single_result, mock_main_class):
        # Configure the mock for Main
        mock_main_instance = mock_main_class.return_value
        mock_main_instance.time = 4.56

        # Temporarily patch COLS and ROWS in benchmark module
        with patch('Core.benchmark.COLS', [3]), patch('Core.benchmark.ROWS', [10]), patch('Core.benchmark.os.path.exists', return_value=True):
            bench = Benchmark("HierarchicalBUC", isPrinted=False)
            bench.run()

        # Check if Main was called and runHierarchicalBUC was called
        mock_main_class.assert_called()
        mock_main_instance.runHierarchicalBUC.assert_called_once()
        
        self.assertEqual(bench.times[10], [4.56])
        mock_save_single_result.assert_called_once_with(10, 4.56)

    @patch('Core.benchmark.os.rename')
    @patch('Core.benchmark.os.remove')
    @patch('Core.benchmark.os.makedirs')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('Core.benchmark.json.dump')
    def test_save_single_result(self, mock_json_dump, mock_open, mock_makedirs, mock_remove, mock_rename):
        bench = Benchmark("BUC")
        bench.output_file = "dummy_output.json"

        # Mock os.path.exists to pretend config doesn't exist to simplify test
        with patch('Core.benchmark.os.path.exists', return_value=False):
            bench.save_single_result(10, 1.1)

        mock_makedirs.assert_called_once()
        mock_open.assert_called_once_with("dummy_output.json.tmp", "w", encoding="utf-8")
        
        # Check what was passed to json.dump
        called_args, called_kwargs = mock_json_dump.call_args
        data_written = called_args[0]
        
        self.assertEqual(data_written["time_data"], {"10": [1.1]})
        self.assertEqual(data_written["max_rows"], 10)
        self.assertEqual(data_written["max_time"], 1.1)
        self.assertEqual(data_written["server_config"], {})
        mock_rename.assert_called_once_with("dummy_output.json.tmp", "dummy_output.json")

if __name__ == '__main__':
    unittest.main()
