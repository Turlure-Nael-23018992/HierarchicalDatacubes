import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from collections import defaultdict
from scripts.Algorithms.OptimizedHierarchicalStarCubing import OptimizedHierarchicalStarCubing

# Dataset à 2 dimensions hiérarchiques et 1 dimension normale :
# Geography: Paris ∈ France ∈ Europe
#            Berlin ∈ Germany ∈ Europe
# Time:      2023-01 ∈ 2023
#            2023-02 ∈ 2023

HIERARCHIES = {
    "Geography": {"ALL": ["Europe"], "Europe": ["France", "Germany"], "France": ["Paris"], "Germany": ["Berlin"]},
    "Time": {"ALL": ["2023"], "2023": ["2023-01", "2023-02"]}
}

DIMS = ["Geography", "Time", "Sales"]
AGG = {"Sales": "SUM"}

DATA = {
    0: ["Paris",  "2023-01", 10],
    1: ["Paris",  "2023-02", 20],
    2: ["Berlin", "2023-01", 30],
}
TOTAL = 60   # 10 + 20 + 30


def run_algo(data=DATA, agg=AGG, threshold=0):
    algo = OptimizedHierarchicalStarCubing(data, DIMS, agg, HIERARCHIES, iceberg_threshold=threshold)
    return algo.run(isPrinted=False)


class TestOptimizedHierarchicalStarCubing(unittest.TestCase):

    def setUp(self):
        self.result = run_algo()

    # ── Vérification structurelle ─────────────────────────────────────────────
    
    def test_global_aggregate_equals_total(self):
        """Le tuple (Geography=ALL, Time=ALL) doit valoir la somme totale."""
        global_rows = [r for r in self.result if r["Geography"] == "ALL" and r["Time"] == "ALL"]
        self.assertEqual(len(global_rows), 1)
        self.assertEqual(global_rows[0]["Sales"], TOTAL)

    def test_leaf_nodes_preserved(self):
        """Les feuilles exactes présentes dans les données doivent exister."""
        paris_jan_rows = [r for r in self.result if r["Geography"] == "Paris" and r["Time"] == "2023-01"]
        self.assertEqual(len(paris_jan_rows), 1)
        self.assertEqual(paris_jan_rows[0]["Sales"], 10)

        berlin_jan_rows = [r for r in self.result if r["Geography"] == "Berlin" and r["Time"] == "2023-01"]
        self.assertEqual(len(berlin_jan_rows), 1)
        self.assertEqual(berlin_jan_rows[0]["Sales"], 30)

    def test_hierarchical_rollup_sum(self):
        """Rolup parent (France) = somme des enfants (Paris)."""
        france_rows = [r for r in self.result if r["Geography"] == "France" and r["Time"] == "ALL"]
        self.assertEqual(len(france_rows), 1)
        self.assertEqual(france_rows[0]["Sales"], 30) # Paris 2023-01 + Paris 2023-02

        germany_rows = [r for r in self.result if r["Geography"] == "Germany" and r["Time"] == "ALL"]
        self.assertEqual(len(germany_rows), 1)
        self.assertEqual(germany_rows[0]["Sales"], 30) # Berlin 2023-01
        
        europe_rows = [r for r in self.result if r["Geography"] == "Europe" and r["Time"] == "ALL"]
        self.assertEqual(len(europe_rows), 1)
        self.assertEqual(europe_rows[0]["Sales"], TOTAL)

    # ── Autres Fonctions d'Agrégation ────────────────────────────────────────
    
    def test_aggregation_max(self):
        result = run_algo(agg={"Sales": "MAX"})
        global_rows = [r for r in result if r["Geography"] == "ALL" and r["Time"] == "ALL"]
        self.assertEqual(global_rows[0]["Sales"], 30)

    def test_aggregation_min(self):
        result = run_algo(agg={"Sales": "MIN"})
        global_rows = [r for r in result if r["Geography"] == "ALL" and r["Time"] == "ALL"]
        self.assertEqual(global_rows[0]["Sales"], 10)

    def test_aggregation_count(self):
        result = run_algo(agg={"Sales": "COUNT"})
        global_rows = [r for r in result if r["Geography"] == "ALL" and r["Time"] == "ALL"]
        self.assertEqual(global_rows[0]["Sales"], 3)

    def test_aggregation_avg(self):
        result = run_algo(agg={"Sales": "AVG"})
        global_rows = [r for r in result if r["Geography"] == "ALL" and r["Time"] == "ALL"]
        self.assertEqual(global_rows[0]["Sales"], 20.0) # (10+20+30)/3 = 20.0
        
        france_rows = [r for r in result if r["Geography"] == "France" and r["Time"] == "ALL"]
        self.assertEqual(france_rows[0]["Sales"], 15.0) # (10+20)/2 = 15.0

    # ── Iceberg Threshold ───────────────────────────────────────────────────

    def test_iceberg_threshold(self):
        result = run_algo(threshold=25)
        # 10 et 20 < 25, donc "Paris 2023-01" et "Paris 2023-02" doivent être supprimés
        paris_jan_rows = [r for r in result if r["Geography"] == "Paris" and r["Time"] == "2023-01"]
        self.assertEqual(len(paris_jan_rows), 0)

        paris_feb_rows = [r for r in result if r["Geography"] == "Paris" and r["Time"] == "2023-02"]
        self.assertEqual(len(paris_feb_rows), 0)

        # "Berlin 2023-01" est à 30 >= 25, donc il reste
        berlin_jan_rows = [r for r in result if r["Geography"] == "Berlin" and r["Time"] == "2023-01"]
        self.assertEqual(len(berlin_jan_rows), 1)
        self.assertEqual(berlin_jan_rows[0]["Sales"], 30)

        # "France ALL" est à 30 >= 25
        france_rows = [r for r in result if r["Geography"] == "France" and r["Time"] == "ALL"]
        self.assertEqual(len(france_rows), 1)

    # ── Dataset Vide ────────────────────────────────────────────────────────

    def test_empty_dataset(self):
        result = run_algo(data={})
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
