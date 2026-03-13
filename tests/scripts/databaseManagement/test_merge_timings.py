import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock, mock_open

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.databaseManagement.merge_timings import merge_timings

class TestMergeTimings(unittest.TestCase):
    @patch('os.listdir')
    @patch('os.path.isdir', return_value=True)
    @patch('os.path.isfile', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    def test_merge_timings(self, mock_json_dump, mock_json_load, mock_open_file, mock_isfile, mock_isdir, mock_listdir):
        # Mock directory structure
        mock_listdir.return_value = ["Algo1"]
        # Mock json content for Algo1/c3.json
        mock_json_load.return_value = {
            "time_data": {
                "100": [1.0, 2.0],
                "500": [5.0]
            }
        }
        
        output_path = "merged_output.json"
        merge_timings(execution_time_dir="dummy_dir", output_path=output_path)
        
        # Verify json.dump was called with merged data
        args, kwargs = mock_json_dump.call_args
        merged_data = args[0]
        
        self.assertIn("Algo1", merged_data)
        self.assertIn("Algo1_R100", merged_data["Algo1"])
        self.assertEqual(merged_data["Algo1"]["Algo1_R100"]["duration_seconds"], 1.5)
        self.assertEqual(merged_data["Algo1"]["Algo1_R500"]["duration_seconds"], 5.0)

if __name__ == '__main__':
    unittest.main()
