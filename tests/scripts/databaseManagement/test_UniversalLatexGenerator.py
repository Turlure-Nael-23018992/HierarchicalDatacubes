import unittest
import os
import sys
import math
from unittest.mock import patch, mock_open

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.databaseManagement.UniversalLatexGenerator import UniversalLatexGenerator

class TestUniversalLatexGenerator(unittest.TestCase):
    def setUp(self):
        self.gen = UniversalLatexGenerator(output_path="test_output.tex")

    def test_get_rgb_value(self):
        rgb, mode = self.gen.get_rgb_value("skyblue")
        self.assertEqual(rgb, "135,206,235")
        self.assertEqual(mode, "RGB")
        
        rgb, mode = self.gen.get_rgb_value("unknown")
        self.assertEqual(rgb, "0,0,0")

    def test_round_to_axis(self):
        self.assertEqual(self.gen.round_to_axis(123), 200)
        self.assertEqual(self.gen.round_to_axis(0), 10)
        self.assertEqual(self.gen.round_to_axis(950), 1000)

    def test_format_tick_label(self):
        self.assertEqual(self.gen.format_tick_label(100), "$100$")
        self.assertEqual(self.gen.format_tick_label(1000), "$1 \\times 10^{3}$")
        self.assertEqual(self.gen.format_tick_label(0), "$0$")

    @patch('builtins.open', new_callable=mock_open)
    def test_generate_latex(self, mock_file):
        timeDicts = [{10: [1.0], 100: [2.0]}]
        maxRowsList = [100]
        maxTimeList = [2.0]
        algos = ["Algo1"]
        
        self.gen.generate_latex(timeDicts, maxRowsList, maxTimeList, algos)
        
        mock_file.assert_called_with("test_output.tex", "w")
        handle = mock_file()
        content = handle.write.call_args_list
        # Verify some LaTeX content was written
        full_content = "".join(call[0][0] for call in content)
        self.assertIn("\\documentclass", full_content)
        self.assertIn("Algo1", full_content)
        self.assertIn("Cardinality", full_content)

if __name__ == '__main__':
    unittest.main()
