import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Scoped mocking for PyQt and Matplotlib
mock_mpl = MagicMock()
mock_mpl.__path__ = []
mock_qt = MagicMock()

sys.modules['PyQt6'] = mock_qt
sys.modules['PyQt6.QtWidgets'] = mock_qt
sys.modules['PyQt6.QtCore'] = mock_qt
sys.modules['PyQt6.QtGui'] = mock_qt
sys.modules['matplotlib'] = mock_mpl
sys.modules['matplotlib.backends.backend_qtagg'] = MagicMock()
sys.modules['matplotlib.figure'] = MagicMock()

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Core.AppUIPyQT import AlgoWorker, BatchWorker

class TestAppUIExtended(unittest.TestCase):
    def test_parse_results_star_cubing(self):
        worker = AlgoWorker("Star-Cubing", "dummy.db", False)
        main_mock = MagicMock()
        # results: list of dicts
        results = [{"A": "v1", "B": "ALL", "Val": 10}, {"A": "ALL", "B": "ALL", "Val": 30}]
        headers, rows = worker.parse_results(results, main_mock)
        self.assertEqual(headers, ["Level", "A", "B", "Val"])
        self.assertEqual(len(rows), 3) # row1, separator, row2

    def test_parse_results_hierarchical_star_cubing(self):
        worker = AlgoWorker("Hierarchical Star-Cubing", "dummy.db", True)
        main_mock = MagicMock()
        results = [{"A": "v1", "B": "ALL", "Val": 10}, {"A": "ALL", "B": "ALL", "Val": 30}]
        headers, rows = worker.parse_results(results, main_mock)
        self.assertEqual(headers, ["Level", "A", "B", "Val"])
        self.assertEqual(len(rows), 3)

    def test_parse_results_error_path(self):
        worker = AlgoWorker("Unknown", "dummy.db", False)
        headers, rows = worker.parse_results([], None)
        self.assertEqual(headers, [])
        self.assertEqual(rows, [])

    def test_batch_worker_run_logic(self):
        # Mocking Main and its methods
        with patch('Core.AppUIPyQT.Main') as MockMain:
            mock_instance = MockMain.return_value
            mock_instance.time = 0.5
            
            worker = BatchWorker(["BUC"], [("test_R100.db", "test_R100.db")], smart_match=False)
            
            # We don't want to start the thread, just test the run logic
            # We can mock the progress signal
            worker.progress = MagicMock()
            worker.finished = MagicMock()
            
            worker.run()
            
            self.assertIn(100, worker.finished.call_args[0][0]["BUC"])
            self.assertEqual(worker.finished.call_args[0][0]["BUC"][100], 0.5)

    def test_batch_worker_smart_match_reverse(self):
        # hierarchie -> cosky
        worker = BatchWorker(["BUC"], [("hierarchie_db_R10.db", "hierarchie_db_R10.db")], smart_match=True)
        worker.progress = MagicMock()
        worker.finished = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('Core.AppUIPyQT.Main') as MockMain:
            worker.run()
            # It should have tried to run on cosky_db_R10.db
            # Check if MockMain was called with something containing cosky
            call_args = MockMain.call_args[0][0]
            self.assertIn("cosky_db_R10.db", call_args)

if __name__ == '__main__':
    unittest.main()
