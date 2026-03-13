import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Core.main import Main

class TestMain(unittest.TestCase):
    def setUp(self):
        self.dummy_db_path = "dummy.db"
        self.main_app = Main(self.dummy_db_path)

    @patch('Core.main.dbGetter')
    def test_prepare_data_3_cols(self, mock_dbgetter):
        # Configure mock for a 3-column table (meaning it should add a COUNT measure automatically)
        mock_instance = mock_dbgetter.return_value
        mock_instance.get_table_names.return_value = ["TestTable"]
        mock_instance.get_column_names.return_value = ["ID", "Dim1", "Dim2", "Dim3"]
        # Dummy data: (ID, val1, val2, val3)
        mock_instance.get_all_data.return_value = [
            (1, "A", "B", "C"),
            (2, "X", "Y", "Z")
        ]

        data, all_cols, dims, measure = self.main_app._prepare_data()

        # Expected: ID is filtered out. Remaining are Dim1, Dim2, Dim3. A 1.0 is appended.
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], ("A", "B", "C", 1.0))
        self.assertEqual(dims, ["Dim1", "Dim2", "Dim3"])
        self.assertEqual(measure, "COUNT")
        self.assertEqual(all_cols, ["Dim1", "Dim2", "Dim3", "COUNT"])

    @patch('Core.main.dbGetter')
    def test_prepare_data_more_cols(self, mock_dbgetter):
        # Configure mock for >3 columns. The last column becomes the measure.
        mock_instance = mock_dbgetter.return_value
        mock_instance.get_table_names.return_value = ["TestTable"]
        mock_instance.get_column_names.return_value = ["ID", "Dim1", "Dim2", "Dim3", "MeasureCol"]
        
        mock_instance.get_all_data.return_value = [
            (1, "A", "B", "C", 50),
            (2, "X", "Y", "Z", 100)
        ]

        data, all_cols, dims, measure = self.main_app._prepare_data()

        # Expected: ID is removed. Last column is measure.
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], ("A", "B", "C", 50))
        self.assertEqual(dims, ["Dim1", "Dim2", "Dim3"])
        self.assertEqual(measure, "MeasureCol")
        self.assertEqual(all_cols, ["Dim1", "Dim2", "Dim3", "MeasureCol"])

    @patch('Core.main.BUC')
    def test_runBUC(self, mock_buc_class):
        mock_buc_instance = mock_buc_class.return_value
        mock_buc_instance.run.return_value = ({"fake": "result"}, 1.23)

        result = self.main_app.runBUC()

        self.assertEqual(result, {"fake": "result"})
        self.assertEqual(self.main_app.time, 1.23)
        mock_buc_class.assert_called_once_with(self.dummy_db_path)
        mock_buc_instance.run.assert_called_once_with(isPrinted=False)

    @patch('Core.main.HierarchicalBUC')
    def test_runHierarchicalBUC(self, mock_hbuc_class):
        mock_hbuc_instance = mock_hbuc_class.return_value
        mock_hbuc_instance.run_buc_from_simple_hierarchical_db.return_value = {"h_result": 42}
        mock_hbuc_instance.time = 4.56

        result = self.main_app.runHierarchicalBUC()

        self.assertEqual(result, {"h_result": 42})
        self.assertEqual(self.main_app.time, 4.56)
        mock_hbuc_instance.run_buc_from_simple_hierarchical_db.assert_called_once_with(self.dummy_db_path, isPrinted=False)

    @patch('Core.main.Main._prepare_data')
    @patch('Core.main.StarCubing')
    def test_runStarCubing(self, mock_sc_class, mock_prepare_data):
        mock_prepare_data.return_value = (["data"], ["all_cols"], ["dims"], "measure")
        mock_sc_instance = mock_sc_class.return_value
        mock_sc_instance.run.return_value = ({"sc_result": "ok"}, 2.5)

        result = self.main_app.runStarCubing()

        self.assertEqual(result, {"sc_result": "ok"})
        self.assertEqual(self.main_app.time, 2.5)
        mock_sc_class.assert_called_once_with(["data"], ["all_cols"])
        mock_sc_instance.run.assert_called_once_with(aggregation={"measure": "SUM"})

    @patch('Core.main.HierarchicalStarCubing')
    def test_runHierarchicalStarCubing(self, mock_hsc_class):
        mock_hsc_instance = mock_hsc_class.return_value
        mock_hsc_instance.run_from_db.return_value = {"hsc_result": "done"}
        mock_hsc_instance.time = 3.14

        result = self.main_app.runHierarchicalStarCubing()

        self.assertEqual(result, {"hsc_result": "done"})
        self.assertEqual(self.main_app.time, 3.14)
        mock_hsc_class.assert_called_once_with({}, [], {"COUNT": "SUM"}, {})
        mock_hsc_instance.run_from_db.assert_called_once_with(self.dummy_db_path, isPrinted=False)

    @patch('Core.main.Main._prepare_data')
    @patch('Core.main.ClosetCube')
    def test_runClosetCube(self, mock_cc_class, mock_prepare_data):
        mock_prepare_data.return_value = (["data"], ["all_cols"], ["dims"], "measure")
        mock_cc_instance = mock_cc_class.return_value
        mock_cc_instance.generate_cube.return_value = ({"cc_result": 1}, 1.1)

        result = self.main_app.runClosetCube()

        self.assertEqual(result, {"cc_result": 1})
        self.assertEqual(self.main_app.time, 1.1)
        mock_cc_class.assert_called_once_with(["data"], ["all_cols"])
        mock_cc_instance.generate_cube.assert_called_once_with(aggregation={"measure": "SUM"})

    @patch('Core.main.Main._prepare_data')
    @patch('Core.main.HierarchicalClosetCube')
    def test_runHierarchicalClosetCube(self, mock_hcc_class, mock_prepare_data):
        mock_prepare_data.return_value = (["data"], ["all_cols"], ["dims"], "measure")
        mock_hcc_instance = mock_hcc_class.return_value
        mock_hcc_instance.generate_closed_cube.return_value = {"hcc_result": 2}
        mock_hcc_instance.time = 2.2

        result = self.main_app.runHierarchicalClosetCube()

        self.assertEqual(result, {"hcc_result": 2})
        self.assertEqual(self.main_app.time, 2.2)
        mock_hcc_class.assert_called_once_with(["data"], ["all_cols"], skip_first_col=False)
        mock_hcc_instance.generate_closed_cube.assert_called_once_with(verbose=False)

if __name__ == '__main__':
    unittest.main()
