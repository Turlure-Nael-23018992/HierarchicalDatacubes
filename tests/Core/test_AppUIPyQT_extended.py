import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Scoped mocking for PyQt and Matplotlib
class TestAppUIExtended(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup Scoped Mocks
        cls.mock_modules = {}
        
        # Mock PyQt6 properly for inheritance
        mock_qt_core = MagicMock()
        # QThread must be a class-like object that doesn't crash on inheritance/init
        mock_qt_core.QThread = type('QThread', (object,), {"__init__": lambda self, *args, **kwargs: None})
        mock_qt_core.pyqtSignal = MagicMock
        cls.mock_modules['PyQt6.QtCore'] = mock_qt_core

        mock_qt_widgets = MagicMock()
        mock_qt_widgets.QMainWindow = type('QMainWindow', (object,), {"__init__": lambda self, *args, **kwargs: None})
        mock_qt_widgets.QWidget = type('QWidget', (object,), {"__init__": lambda self, *args, **kwargs: None})
        cls.mock_modules['PyQt6.QtWidgets'] = mock_qt_widgets

        cls.mock_modules['PyQt6'] = MagicMock()
        cls.mock_modules['PyQt6.QtGui'] = MagicMock()
        
        # Mock matplotlib (crucial: give it a __path__ so it's treated as a package)
        mock_mpl = MagicMock()
        mock_mpl.__path__ = []
        cls.mock_modules['matplotlib'] = mock_mpl
        cls.mock_modules['matplotlib.backends.backend_qtagg'] = MagicMock()
        cls.mock_modules['matplotlib.figure'] = MagicMock()

        # Apply patches
        cls.patcher = patch.dict('sys.modules', cls.mock_modules)
        cls.patcher.start()

        # Late imports to ensure it uses the mocks
        from Core.AppUIPyQT import AlgoWorker, BatchWorker
        cls.AlgoWorker = AlgoWorker
        cls.BatchWorker = BatchWorker

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_parse_results_star_cubing(self):
        worker = self.AlgoWorker("Star-Cubing", "dummy.db", False)
        main_mock = MagicMock()
        # results: list of dicts
        results = [{"A": "v1", "B": "ALL", "Val": 10}, {"A": "ALL", "B": "ALL", "Val": 30}]
        headers, rows = worker.parse_results(results, main_mock)
        self.assertEqual(headers, ["Level", "A", "B", "Val"])
        # row1, separator, row2
        self.assertEqual(len(rows), 3)

    def test_parse_results_hierarchical_star_cubing(self):
        worker = self.AlgoWorker("Hierarchical Star-Cubing", "dummy.db", True)
        main_mock = MagicMock()
        results = [{"A": "v1", "B": "ALL", "Val": 10}, {"A": "ALL", "B": "ALL", "Val": 30}]
        headers, rows = worker.parse_results(results, main_mock)
        self.assertEqual(headers, ["Level", "A", "B", "Val"])
        self.assertEqual(len(rows), 3)

    def test_parse_results_error_path(self):
        worker = self.AlgoWorker("Unknown", "dummy.db", False)
        # Should return [], [] if not handled
        headers, rows = worker.parse_results([], None)
        self.assertEqual(headers, [])
        self.assertEqual(rows, [])

    def test_batch_worker_run_logic(self):
        with patch('Core.AppUIPyQT.Main') as MockMain:
            mock_instance = MockMain.return_value
            mock_instance.time = 0.5
            
            worker = self.BatchWorker(["BUC"], [("test_R100.db", "test_R100.db")], smart_match=False)
            worker.progress = MagicMock()
            worker.finished = MagicMock()
            
            worker.run()
            
            # Verify if finished was emitted with correct results
            self.assertTrue(worker.finished.emit.called)
            results = worker.finished.emit.call_args[0][0]
            self.assertIn(100, results["BUC"])
            self.assertEqual(results["BUC"][100], 0.5)

    def test_batch_worker_smart_match_reverse(self):
        worker = self.BatchWorker(["BUC"], [("hierarchie_db_R10.db", "hierarchie_db_R10.db")], smart_match=True)
        worker.progress = MagicMock()
        worker.finished = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('Core.AppUIPyQT.Main') as MockMain:
            worker.run()
            call_args = MockMain.call_args[0][0]
            self.assertIn("cosky_db_R10.db", call_args)

if __name__ == '__main__':
    unittest.main()
