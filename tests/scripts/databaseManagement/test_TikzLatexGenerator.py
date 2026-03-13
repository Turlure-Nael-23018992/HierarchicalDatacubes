import unittest
import os
import sys
import json
from unittest.mock import patch, mock_open

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.databaseManagement.TikzLatexGenerator import TikzLatexGenerator

class TestTikzLatexGenerator(unittest.TestCase):
    def setUp(self):
        self.gen = TikzLatexGenerator(data_dir="test_data")

    def test_nice_max(self):
        self.assertEqual(self.gen._nice_max(12), 20)
        self.assertEqual(self.gen._nice_max(45), 50)
        self.assertEqual(self.gen._nice_max(80), 100)
        self.assertEqual(self.gen._nice_max(0), 10)

    def test_fmt(self):
        self.assertEqual(self.gen._fmt(0.5), "$0.5$")
        self.assertEqual(self.gen._fmt(1500), "$1.5\\!\\times\\!10^{3}$")
        self.assertEqual(self.gen._fmt(0.0001), "$0$")

    def test_to_pos_lin(self):
        # 50 out of 100 on a 320 canvas
        pos = self.gen._to_pos(50, 100, "lin", 320)
        self.assertEqual(pos, 160)

    @patch('os.path.isfile', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({"time_data": {"10": [1.0, 2.0]}}))
    def test_load(self, mock_file, mock_isfile):
        data = self.gen._load("Algo1")
        self.assertEqual(data, {10: 1.5})

    @patch('scripts.databaseManagement.TikzLatexGenerator.TikzLatexGenerator.load_all')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_generate(self, mock_makedirs, mock_file, mock_load_all):
        mock_load_all.return_value = [{10: 1.0, 100: 2.0}]
        
        self.gen.generate(["Algo1"], "out.tex")
        
        mock_file.assert_called_with("out.tex", "w", encoding="utf-8")
        handle = mock_file()
        full_content = "".join(call[0][0] for call in handle.write.call_args_list)
        self.assertIn("\\documentclass", full_content)
        self.assertIn("Algo1", full_content)

if __name__ == '__main__':
    unittest.main()
