import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.Algorithms.HierarchicalLevelUpCube import HierarchicalLevelUpCube

COLS = ["ID", "Geography", "Time", "Food", "COUNT"]
DATA = [
    (1, "Paris",     "2022-01-01", "Fraise",    10),
    (2, "Paris",     "2022-01-01", "Framboise",  5),
    (3, "Marseille", "2022-01-01", "Fraise",    20),
]
TOTAL = 35

VALID_GEO   = {"Paris", "Marseille", "Île-de-France", "PACA", "France", "Europe"}
VALID_TIME  = {"2022-01-01", "2022-01", "2022"}
VALID_FOOD  = {"Fraise", "Framboise", "Fruits rouges", "Fruits"}

def make_algo():
    return HierarchicalLevelUpCube(DATA, COLS, iceberg_threshold=0, skip_first_col=True)

class TestHierarchicalLevelUpCube(unittest.TestCase):
    def setUp(self):
        self.algo   = make_algo()
        self.result = self.algo.generate_closed_cube(aggregation_dict={"COUNT": "SUM"})
        self.dim_count = len(self.algo.dim_cols)

    def test_closed_property(self):
        for t1 in self.result:
            k1, v1 = t1[:self.dim_count], t1[self.dim_count]
            for t2 in self.result:
                k2, v2 = t2[:self.dim_count], t2[self.dim_count]
                if k1 == k2:
                    continue
                if self.algo._is_more_general(k2, k1):
                    self.assertNotEqual(
                        v1, v2,
                        f"Propriété fermée violée : {k2}={v2} est plus général que {k1}={v1}"
                    )

    def test_global_aggregate_present_and_correct(self):
        max_count = max(t[-1] for t in self.result)
        self.assertEqual(max_count, TOTAL)

    def test_no_count_exceeds_total(self):
        for t in self.result:
            self.assertLessEqual(t[-1], TOTAL)

    def test_all_counts_strictly_positive(self):
        for t in self.result:
            self.assertGreater(t[-1], 0)

    def test_dim_values_are_valid_hierarchy_nodes(self):
        for t in self.result:
            geo, time, food = t[0], t[1], t[2]
            self.assertIn(geo,  VALID_GEO,  f"Valeur géo invalide : '{geo}'")
            self.assertIn(time, VALID_TIME, f"Valeur time invalide : '{time}'")
            self.assertIn(food, VALID_FOOD, f"Valeur food invalide : '{food}'")

    def test_no_duplicate_tuples(self):
        dim_keys = [t[:self.dim_count] for t in self.result]
        self.assertEqual(len(dim_keys), len(set(dim_keys)))

    def test_empty_dataset(self):
        algo_empty = HierarchicalLevelUpCube([], COLS, iceberg_threshold=0, skip_first_col=True)
        result = algo_empty.generate_closed_cube(aggregation_dict={"COUNT": "SUM"})
        self.assertEqual(result, [])

    def test_cross_dimension_rollup(self):
        # We also want to make sure the cube output size for a single leaf is correct path length product
        algo_single = HierarchicalLevelUpCube([
            (1, "Paris", "2022-01-01", "Fraise", 10),
        ], COLS, skip_first_col=True)
        # depth: Geo (Paris, Ile, France, Europe)->4
        # Time (2022-01-01, 2022-01, 2022)->3
        # Food (Fraise, Fruits rouges, Fruits)->3
        # In ClosetCube and LevelUpCube, closed cells might be fewer, but without checking closedness:
        # Actually generate_closed_cube will reduce this. For single item, it just gives the most general one
        result = algo_single.generate_closed_cube(aggregation_dict={"COUNT": "SUM"})
        # The most general closed node for a single value is just its root.
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ("Europe", "2022", "Fruits", 10))

if __name__ == "__main__":
    unittest.main()
