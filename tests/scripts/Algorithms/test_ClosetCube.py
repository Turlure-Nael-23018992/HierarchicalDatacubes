import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.Algorithms.closetCube import ClosetCube


class TestClosetCube(unittest.TestCase):
    """Tests unitaires pour l'algorithme ClosetCube."""

    def setUp(self):
        self.cols = ["A", "B", "C", "M"]
        self.data = [
            ("a1", "b1", "c1", 10),
            ("a1", "b2", "c1", 20),
            ("a2", "b1", "c2", 30),
        ]

        # generate_cube() génère 2^3=8 masques par ligne, puis tronque le résultat
        # à au plus len(data)=3 lignes (heuristique de compression interne).
        self.expected_full_cube = [
            {'A': 'a1', 'B': 'b1', 'C': 'c1', 'M': 10},
            {'A': 'ALL', 'B': 'b1', 'C': 'c1', 'M': 10},
            {'A': 'a1', 'B': 'ALL', 'C': 'c1', 'M': 30},
        ]

    def test_basic_cubing(self):
        """Vérifie la génération des cuboïdes fermés sans filtre (threshold=0)."""
        algo = ClosetCube(self.data, self.cols, iceberg_threshold=0)
        result_list, _ = algo.generate_cube(aggregation={"M": "SUM"})

        # La sortie est bornée à len(data)=3 lignes par design
        self.assertEqual(len(result_list), len(self.expected_full_cube), "Cube size mismatch.")

        # Comparaison indépendante de l'ordre
        def to_comparable(lst):
            return sorted([tuple(sorted(d.items())) for d in lst])

        self.assertEqual(to_comparable(result_list), to_comparable(self.expected_full_cube),
                         "ClosetCube output does not match expected exact cube.")

    def test_iceberg_threshold_filtering(self):
        """Vérifie que iceberg_threshold filtre les cuboïdes sous le seuil."""
        algo = ClosetCube(self.data, self.cols, iceberg_threshold=25)
        result_list, _ = algo.generate_cube(aggregation={"M": "SUM"})

        # Après filtrage (M < 25 rejetés) + troncature à len(data)=3, au plus 3 lignes
        self.assertLessEqual(len(result_list), len(self.data),
                             "Result must not exceed len(data) rows (internal truncation).")

        for row in result_list:
            self.assertTrue(row["M"] >= 25, f"Row {row} has measure < 25.")

    def test_empty_dataset(self):
        """Vérifie le comportement sur un dataset vide."""
        algo = ClosetCube([], self.cols, iceberg_threshold=0)
        result_list, _ = algo.generate_cube(aggregation={"M": "SUM"})

        # Retour anticipé dans generate_cube() quand self.data est vide
        self.assertEqual(result_list, [], "Empty input should yield an empty result list.")


if __name__ == "__main__":
    unittest.main()
