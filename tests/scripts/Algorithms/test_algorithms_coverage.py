import unittest
import os
import sys
import sqlite3
import io
from contextlib import redirect_stdout
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.Algorithms.BUC import BUC
from scripts.Algorithms.starCubing import StarCubing
from scripts.Algorithms.HierarchicalBUC import HierarchicalBUC
from scripts.Algorithms.HierarchicalStarCubing import HierarchicalStarCubing
from scripts.Algorithms.closetCube import ClosetCube

class TestAlgorithmsCoverage(unittest.TestCase):
    def setUp(self):
        self.db_path = f"tmp_test_cov_{os.getpid()}.db"
        self.data = [
            ("FR", "2021", "Apple", 10),
            ("FR", "2021", "Pear", 20),
            ("US", "2022", "Apple", 30),
        ]
        self.cols = ["Geo", "Time", "Food", "Val"]
        
        # Create a real DB for BUC and others that read from DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("CREATE TABLE Pokemon (Geo TEXT, Time TEXT, Food TEXT, Val INTEGER)")
        c.executemany("INSERT INTO Pokemon VALUES (?, ?, ?, ?)", self.data)
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_buc_printing_and_logic(self):
        buc = BUC(self.db_path)
        # Small data: should print
        f = io.StringIO()
        with redirect_stdout(f):
            buc.run(isPrinted=True)
        output = f.getvalue()
        self.assertIn("Geo", output)
        self.assertIn("Val", output)

        # Large data dummy to trigger warning
        buc.row_count = 101
        f = io.StringIO()
        with redirect_stdout(f):
            buc._print_results({})
        self.assertIn("Impression désactivée automatiquement", f.getvalue())

    def test_star_cubing_aggregations_and_export(self):
        # Convert data to list of lists for StarCubing if needed
        data_list = [list(r) for r in self.data]
        sc = StarCubing(data_list, self.cols)
        
        # Test AVG
        res_avg, _ = sc.run(aggregation={"Val": "AVG"})
        self.assertEqual(res_avg[0]["Val"], 10.0)
        
        # Test COUNT
        res_cnt, _ = sc.run(aggregation={"Val": "COUNT"})
        self.assertEqual(res_cnt[0]["Val"], 1)

        # Test export methods
        f = io.StringIO()
        with redirect_stdout(f):
            sc.export_star_tree_like_structure(group_by_subtables=True, show_all_as_one_table=True)
        output = f.getvalue()
        self.assertIn("TABLEAU GLOBAL", output)
        self.assertIn("CUBOÏDES DE NIVEAU", output)

    def test_hierarchical_buc_aggregations_and_print(self):
        hbuc = HierarchicalBUC()
        
        # Test aggregations in _run_flat_buc
        data_dict = {i: list(self.data[i]) for i in range(len(self.data))}
        
        # MAX
        res_max = hbuc._run_flat_buc(data_dict, self.cols, {"Val": "MAX"}, {}, isPrinted=False)
        all_val = res_max[(True, True, True)][0]["Val"]
        self.assertEqual(all_val, 30)

        # MIN
        res_min = hbuc._run_flat_buc(data_dict, self.cols, {"Val": "MIN"}, {}, isPrinted=False)
        all_val_min = res_min[(True, True, True)][0]["Val"]
        self.assertEqual(all_val_min, 10)

        # AVG
        res_avg = hbuc._run_flat_buc(data_dict, self.cols, {"Val": "AVG"}, {}, isPrinted=False)
        all_val_avg = res_avg[(True, True, True)][0]["Val"]
        self.assertEqual(all_val_avg, 20.0)

        # Test printing logic with regex
        f = io.StringIO()
        with redirect_stdout(f):
            hbuc._print_results(res_max, ["Geo", "Time", "Food"], ["Val"])
        self.assertIn("TABLEAU GLOBAL DES CUBOÏDES", f.getvalue())

    def test_hierarchical_star_cubing_coverage(self):
        data_dict = {i: list(self.data[i]) for i in range(len(self.data))}
        hsc = HierarchicalStarCubing(data_dict, self.cols, {"Val": "SUM"}, {})
        
        # Test flat run
        f = io.StringIO()
        with redirect_stdout(f):
            res_flat = hsc.run_flat_star_cubing(isPrinted=True)
        self.assertIn(3, res_flat) # Level 3 (all ALL)

        # Test aggregation error
        hsc.aggregation["Val"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            hsc._aggregate_measures([[10]])

        # Test run_from_db
        hsc.run_from_db(self.db_path, isPrinted=False)

    def test_closet_cube_coverage(self):
        data_list = [list(r) for r in self.data]
        cc = ClosetCube(data_list, self.cols)
        
        # Test AVG
        res_avg, _ = cc.generate_cube(aggregation={"Val": "AVG"})
        # US 2022 Apple 30 -> AVG 30
        self.assertTrue(any(r["Val"] == 30.0 for r in res_avg))

        # Test COUNT
        res_cnt, _ = cc.generate_cube(aggregation={"Val": "COUNT"})
        # US 2022 Apple 30 -> COUNT 1
        self.assertTrue(any(r["Val"] == 1 for r in res_cnt))

        # Test export
        f = io.StringIO()
        with redirect_stdout(f):
            cc.export_closet_cube_structure(res_avg)
        self.assertIn("TABLEAU GLOBAL DES CUBOÏDES FERMÉS", f.getvalue())

if __name__ == '__main__':
    unittest.main()
