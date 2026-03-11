import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.Algorithms.starCubing import StarCubing


class TestStarCubing(unittest.TestCase):
    """Tests unitaires pour l'algorithme Star-Cubing."""

    def setUp(self):
        self.cols = ["A", "B", "C", "M"]
        self.data = [
            ("a1", "b1", "c1", 10),
            ("a1", "b2", "c1", 20),
            ("a2", "b1", "c2", 30),
        ]

        # Cube complet attendu : 18 cuboïdes distincts (toutes combinaisons valeur|ALL
        # sur 3 dimensions, avec agrégation SUM pour la mesure M)
        self.expected_full_cube = [
            {'A': 'a1',  'B': 'b1',  'C': 'c1',  'M': 10},
            {'A': 'a1',  'B': 'b1',  'C': 'ALL', 'M': 10},
            {'A': 'a1',  'B': 'b2',  'C': 'c1',  'M': 20},
            {'A': 'a1',  'B': 'b2',  'C': 'ALL', 'M': 20},
            {'A': 'a1',  'B': 'ALL', 'C': 'c1',  'M': 30},
            {'A': 'a1',  'B': 'ALL', 'C': 'ALL', 'M': 30},
            {'A': 'a2',  'B': 'b1',  'C': 'c2',  'M': 30},
            {'A': 'a2',  'B': 'b1',  'C': 'ALL', 'M': 30},
            {'A': 'a2',  'B': 'ALL', 'C': 'c2',  'M': 30},
            {'A': 'a2',  'B': 'ALL', 'C': 'ALL', 'M': 30},
            {'A': 'ALL', 'B': 'b1',  'C': 'c1',  'M': 10},
            {'A': 'ALL', 'B': 'b1',  'C': 'c2',  'M': 30},
            {'A': 'ALL', 'B': 'b1',  'C': 'ALL', 'M': 40},
            {'A': 'ALL', 'B': 'b2',  'C': 'c1',  'M': 20},
            {'A': 'ALL', 'B': 'b2',  'C': 'ALL', 'M': 20},
            {'A': 'ALL', 'B': 'ALL', 'C': 'c1',  'M': 30},
            {'A': 'ALL', 'B': 'ALL', 'C': 'c2',  'M': 30},
            {'A': 'ALL', 'B': 'ALL', 'C': 'ALL', 'M': 60},
        ]

    def test_basic_cubing(self):
        """Vérifie que Star-Cubing génère les 18 cuboïdes attendus (threshold=0)."""
        algo = StarCubing(self.data, self.cols, iceberg_threshold=0)
        result_list, _ = algo.run(aggregation={"M": "SUM"})

        self.assertEqual(len(result_list), len(self.expected_full_cube), "Full cube size mismatch.")

        # Comparaison indépendante de l'ordre de génération
        def to_comparable(lst):
            return sorted([tuple(sorted(d.items())) for d in lst])

        self.assertEqual(to_comparable(result_list), to_comparable(self.expected_full_cube),
                         "StarCubing output does not match expected exact cube.")

    def test_iceberg_threshold_filtering(self):
        """Vérifie que le filtre iceberg est appliqué inline dans run()."""
        algo = StarCubing(self.data, self.cols, iceberg_threshold=25)
        result_list, _ = algo.run(aggregation={"M": "SUM"})

        # Sur 18 cuboïdes : 7 ont M < 25 (valeurs 10 et 20), il en reste 11
        # Contrairement à BUC, StarCubing filtre directement avant d'ajouter au résultat
        self.assertEqual(len(result_list), 11, "Iceberg threshold 25 should leave exactly 11 rows.")

        for row in result_list:
            self.assertTrue(row["M"] >= 25, f"Row {row} has measure < 25.")

    def test_empty_dataset(self):
        """Vérifie le comportement sur un dataset vide."""
        algo = StarCubing([], self.cols, iceberg_threshold=0)
        result_list, _ = algo.run(aggregation={"M": "SUM"})

        # Le générateur récursif produit 1 seul yield en bas de récursion : ALL=0
        self.assertTrue(len(result_list) <= 1, "Empty input should yield at most 1 empty ALL row.")
        if len(result_list) == 1:
            self.assertEqual(result_list[0]["M"], 0, "Empty measure sum should be 0.")


if __name__ == "__main__":
    unittest.main()
