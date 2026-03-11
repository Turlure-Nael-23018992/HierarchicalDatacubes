import unittest
import os
import sys
import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.Algorithms.BUC import BUC


class TestBUC(unittest.TestCase):
    """Tests unitaires pour l'algorithme BUC (Bottom-Up Cubing)."""

    def setUp(self):
        # BUC lit depuis SQLite. 4 colonnes requises pour éviter le mode COUNT
        # (déclenché automatiquement quand len(colonnes) == 3).
        self.db_path = os.path.join(os.path.dirname(__file__), "temp_buc.db")
        self.data = [
            ("a1", "b1", "c1", 10),
            ("a1", "b2", "c1", 20),
            ("a2", "b1", "c2", 30),
        ]

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE Pokemon (A TEXT, B TEXT, C TEXT, M INTEGER)")
        cursor.executemany("INSERT INTO Pokemon VALUES (?, ?, ?, ?)", self.data)
        conn.commit()
        conn.close()

        # Cube complet attendu : 3 lignes × 2^3 masques = 18 clés uniques, valeurs en SUM
        self.expected_full_cube = {
            ('ALL', 'ALL', 'ALL'): 60.0,
            ('ALL', 'ALL', 'c1'): 30.0,
            ('ALL', 'ALL', 'c2'): 30.0,
            ('ALL', 'b1', 'ALL'): 40.0,
            ('ALL', 'b1', 'c1'): 10.0,
            ('ALL', 'b1', 'c2'): 30.0,
            ('ALL', 'b2', 'ALL'): 20.0,
            ('ALL', 'b2', 'c1'): 20.0,
            ('a1', 'ALL', 'ALL'): 30.0,
            ('a1', 'ALL', 'c1'): 30.0,
            ('a1', 'b1', 'ALL'): 10.0,
            ('a1', 'b1', 'c1'): 10.0,
            ('a1', 'b2', 'ALL'): 20.0,
            ('a1', 'b2', 'c1'): 20.0,
            ('a2', 'ALL', 'ALL'): 30.0,
            ('a2', 'ALL', 'c2'): 30.0,
            ('a2', 'b1', 'ALL'): 30.0,
            ('a2', 'b1', 'c2'): 30.0,
        }

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_basic_cubing(self):
        """Vérifie que BUC génère les 18 cuboïdes corrects (threshold=0)."""
        buc = BUC(self.db_path, iceberg_threshold=0)
        accum_result, _ = buc.run()

        # run() retourne toujours le dict complet, sans filtrage iceberg
        self.assertEqual(len(accum_result), len(self.expected_full_cube), "Full cube size mismatch.")

        for key, expected_val in self.expected_full_cube.items():
            self.assertIn(key, accum_result, f"Missing key {key} in BUC result.")
            self.assertEqual(accum_result[key], expected_val, f"Mismatch value for key {key}.")

    def test_iceberg_threshold_filtering(self):
        """Vérifie le filtrage iceberg appliqué manuellement sur le dict retourné par BUC."""
        buc = BUC(self.db_path, iceberg_threshold=25)
        accum_result, _ = buc.run()

        # BUC ne filtre pas le dict retourné (le seuil ne s'applique que dans _print_results)
        filtered_result = {k: v for k, v in accum_result.items() if v >= 25}

        self.assertNotIn(("a1", "b1", "c1"), filtered_result)   # sum=10 → exclu
        self.assertNotIn(("ALL", "b2", "ALL"), filtered_result)  # sum=20 → exclu
        self.assertIn(("a2", "b1", "ALL"), filtered_result)      # sum=30 → inclus
        self.assertIn(("ALL", "ALL", "ALL"), filtered_result)    # sum=60 → inclus

        # Sur 18 cuboïdes : 7 ont sum < 25 (valeurs 10 et 20), il en reste 11
        self.assertEqual(len(filtered_result), 11, "Iceberg threshold 25 should leave exactly 11 cuboids.")

    def test_empty_dataset(self):
        """Vérifie que BUC retourne un dict vide sur un dataset vide."""
        conn = sqlite3.connect(self.db_path)
        conn.cursor().execute("DELETE FROM Pokemon")
        conn.commit()
        conn.close()

        buc = BUC(self.db_path, iceberg_threshold=0)
        accum_result, _ = buc.run()

        # fetchmany() ne renvoie rien → l'accumulateur reste vide
        self.assertEqual(accum_result, {}, "Empty dataset should yield an empty datacube.")


if __name__ == "__main__":
    unittest.main()
