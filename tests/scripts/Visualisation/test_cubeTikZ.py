import unittest
import os
import sys
from unittest.mock import patch, mock_open, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.Visualisation.cubeTikZ import cubeTikz

class TestCubeTikz(unittest.TestCase):
    def setUp(self):
        # 3 dimensions + 1 measure
        self.data = [
            ("Paris", "2022", "Fraise", 10),
            ("Paris", "2022", "Fraise", 5),
            ("Marseille", "2023", "Citron", 20)
        ]
        self.ct = cubeTikz(self.data)

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_exportCubeToTikZ(self, mock_makedirs, mock_file):
        col_names = ["Geo", "Time", "Food"]
        self.ct.exportCubeToTikZ(col_names, "test_cube.tex")
        
        mock_file.assert_called_with(os.path.abspath("test_cube.tex"), "w", encoding="utf-8")
        handle = mock_file()
        full_content = "".join(call[0][0] for call in handle.write.call_args_list)
        
        self.assertIn("\\documentclass", full_content)
        self.assertIn("Geo", full_content)
        self.assertIn("Time", full_content)
        self.assertIn("Food", full_content)
        self.assertIn("Paris & 2022 & Fraise & 15", full_content) # Aggregated 10+5

    @patch('scripts.Visualisation.cubeTikZ.plt')
    def test_generateCube(self, mock_plt):
        # Mock plt.subplots and plt.table
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # This shouldn't block because plt is mocked
        self.ct.generateCube()
        
        mock_plt.subplots.assert_called_once()
        self.assertGreater(mock_plt.table.call_count, 0)
        mock_plt.show.assert_called_once()

if __name__ == '__main__':
    unittest.main()
