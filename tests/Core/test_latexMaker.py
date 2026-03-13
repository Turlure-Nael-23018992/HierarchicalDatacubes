import unittest
import os
import sys
import json
from unittest.mock import patch, mock_open, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Core.latexMaker import LatexMaker

class TestLatexMaker(unittest.TestCase):
    
    @patch('Core.latexMaker.UniversalLatexGenerator')
    def test_generate_all_default_benchmarks(self, mock_ulg_class):
        maker = LatexMaker()
        mock_ulg_instance = maker.generator
        
        with patch('Core.latexMaker.os.makedirs') as mock_makedirs:
            maker.generate_all_default_benchmarks("dummy.json", "out_folder")
            
            mock_makedirs.assert_called_once()
            mock_ulg_instance.generate_graphs_from_json.assert_called_once()
            
            # Check the arguments passed, they should be absolute paths
            args, kwargs = mock_ulg_instance.generate_graphs_from_json.call_args
            self.assertTrue(os.path.isabs(args[0]))
            self.assertTrue(os.path.isabs(args[1]))

    @patch('Core.latexMaker.UniversalLatexGenerator')
    @patch('Core.latexMaker.os.makedirs')
    def test_generate_custom_comparison(self, mock_makedirs, mock_ulg_class):
        maker = LatexMaker()
        mock_ulg_instance = maker.generator
        
        # Create a mock JSON payload representing the benchmark output
        mock_json_data = {
            "AlgoA": {
                "10": [1.5],
                "fichier_db_R100.db": {"duration_seconds": 15.0} # Mixed formats test
            },
            "AlgoB": {
                "10": [2.0],
                "fichier_db_R100.db": {"duration_seconds": 20.0}
            }
        }
        
        mock_json_str = json.dumps(mock_json_data)
        
        with patch('builtins.open', mock_open(read_data=mock_json_str)):
            maker.generate_custom_comparison("dummy.json", "out.tex", ["AlgoA", "AlgoB"], "Test Title")

        mock_makedirs.assert_called()
        mock_ulg_instance.generate_latex.assert_called_once()
        
        args, kwargs = mock_ulg_instance.generate_latex.call_args
        time_dicts = args[0]
        max_card_list = args[1]
        max_time_list = args[2]
        algos = args[3]
        
        # Verify parsed data structure
        self.assertEqual(len(time_dicts), 2)
        self.assertEqual(algos, ["AlgoA", "AlgoB"])
        self.assertEqual(max_card_list, [100])
        self.assertAlmostEqual(max_time_list[0], 20.0) # AlgoB has 20.0 which is the max
        self.assertEqual(time_dicts[0][10], 1.5)
        self.assertEqual(time_dicts[0][100], 15.0)

    @patch('Core.latexMaker.LatexMaker.generate_custom_comparison')
    def test_generate_single_algo_report(self, mock_gen_custom):
        maker = LatexMaker()
        maker.generate_single_algo_report("test.json", "out.tex", "AlgoA")
        
        mock_gen_custom.assert_called_once_with(
            "test.json",
            "out.tex",
            ["AlgoA"],
            "Performance of AlgoA"
        )

if __name__ == '__main__':
    unittest.main()
