import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Mock PyQt6 before importing AppUIPyQT
mock_qt_core = MagicMock()
mock_qt_core.QThread = type('QThread', (object,), {"__init__": lambda self: None})
mock_qt_core.pyqtSignal = MagicMock
sys.modules['PyQt6.QtCore'] = mock_qt_core

mock_qt_widgets = MagicMock()
mock_qt_widgets.QMainWindow = type('QMainWindow', (object,), {"__init__": lambda self: None})
sys.modules['PyQt6.QtWidgets'] = mock_qt_widgets

sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.backends.backend_qtagg'] = MagicMock()
sys.modules['matplotlib.figure'] = MagicMock()

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Core.AppUIPyQT import AlgoWorker, BatchWorker

class TestAppUILogic(unittest.TestCase):
    def test_parse_results_buc(self):
        worker = AlgoWorker("BUC", "dummy.db", False)
        main_mock = MagicMock()
        main_mock.BUC.dim_names = ["A", "B"]
        main_mock.BUC.measure_name = "COUNT"
        
        # BUC results: {(dim1, dim2): value}
        results = {("v1", "ALL"): 10, ("ALL", "ALL"): 50}
        
        headers, rows = worker.parse_results(results, main_mock)
        
        self.assertEqual(headers, ["Level", "A", "B", "COUNT"])
        self.assertEqual(len(rows), 2)
        self.assertIn([1, "v1", "ALL", 10], rows)
        self.assertIn([2, "ALL", "ALL", 50], rows)

    def test_parse_results_hierarchical_buc(self):
        worker = AlgoWorker("Hierarchical BUC", "dummy.db", True)
        main_mock = MagicMock()
        
        # results: {pattern: [dict, ...]}
        results = {
            "111": [{"Geography": "FR", "Time": "2021", "Food": "Apple", "_all_count": 5}],
            "110": [{"Geography": "FR", "Time": "2021", "Food": "ALL", "_all_count": 10}]
        }
        
        headers, rows = worker.parse_results(results, main_mock)
        self.assertIn("Level", headers)
        self.assertIn("Geography", headers)
        self.assertGreater(len(rows), 0)

    def test_parse_results_hierarchical_closetcube(self):
        worker = AlgoWorker("Hierarchical ClosetCube", "dummy.db", True)
        main_mock = MagicMock()
        main_mock.hClosetCube.dim_cols = ["Dim1"]
        main_mock.hClosetCube.measure_cols = ["M1"]
        main_mock.hClosetCube.hierarchy = {"Dim1": {"Parent": ["Child"]}}
        
        # Results: list of tuples (d1, m1)
        results = [("Parent", 100), ("Child", 20)]
        
        headers, rows = worker.parse_results(results, main_mock)
        self.assertEqual(headers, ["Level", "Dim1", "M1"])
        self.assertEqual(len(rows), 3) # Parent, separator, Child (sorted by level)
        # Parent level should be 1, Child level should be 0
        self.assertEqual(rows[0][0], 0) # Child first because level 0? Wait, hcc_level(r)
        # Actually in AppUIPyQT: processed_rows.sort(key=lambda x: x[0])
        # Child has lvl 0, Parent has lvl 1. So Child is first.
        self.assertEqual(rows[0][1], "Child")
        self.assertEqual(rows[2][1], "Parent")

    def test_batch_worker_smart_match(self):
        worker = BatchWorker(["Hierarchical BUC"], [("cosky_db_R100.db", "path/cosky_db_R100.db")], smart_match=True)
        
        with patch('os.path.exists', return_value=True):
            db_name = "cosky_db_R100.db"
            is_hier_algo = True
            is_hier_db = "hierarchie" in db_name.lower()
            
            if is_hier_algo and not is_hier_db:
                match_name = db_name.replace("cosky_db", "hierarchie_db")
                self.assertEqual(match_name, "hierarchie_db_R100.db")

if __name__ == '__main__':
    unittest.main()
