import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.Algorithms.HierarchicalBUC import HierarchicalBUC

# Dataset minimal avec valeurs présentes dans STATIC_HIERARCHY
# Geography: Paris ∈ Île-de-France ∈ France ∈ Europe
#            Marseille ∈ PACA ∈ France ∈ Europe
# Time:      2022-01-01 ∈ 2022-01 ∈ 2022
# Food:      Fraise ∈ Fruits rouges ∈ Fruits
#            Framboise ∈ Fruits rouges ∈ Fruits
DIMS  = ["Geography", "Time", "Food", "COUNT"]
AGG   = {"COUNT": "SUM"}
DATA  = {
    0: ["Paris",     "2022-01-01", "Fraise",    10],
    1: ["Paris",     "2022-01-01", "Framboise",  5],
    2: ["Marseille", "2022-01-01", "Fraise",    20],
}
TOTAL     = 35   # 10 + 5 + 20
N_DIMS    = 3    # Geography, Time, Food
N_PATTERNS = 2 ** N_DIMS  # 8


def run(data=None):
    buc = HierarchicalBUC()
    return buc._run_flat_buc(
        data if data is not None else DATA,
        DIMS, AGG, HierarchicalBUC.STATIC_HIERARCHY,
        isPrinted=False
    )


class TestHierarchicalBUC(unittest.TestCase):
    """Tests des invariants théoriques du BUC hiérarchique."""

    def setUp(self):
        self.result = run()

    # ── Structure du cube ─────────────────────────────────────────────────────

    def test_all_patterns_generated(self):
        """BUC doit générer exactement 2^d patterns (un par combinaison masque)."""
        self.assertEqual(len(self.result), N_PATTERNS)

    def test_all_counts_strictly_positive(self):
        """Tout cuboïde stocké doit avoir un COUNT > 0 (pas de cellules vides)."""
        for rows in self.result.values():
            for row in rows:
                self.assertGreater(row["COUNT"], 0, f"Cuboïde vide trouvé : {row}")

    # ── Conservation de la mesure ──────────────────────────────────────────────

    def test_global_aggregate_equals_input_sum(self):
        """Le pattern tout-ALL doit contenir exactement 1 ligne dont COUNT = somme des inputs."""
        all_pattern = (True, True, True)
        self.assertIn(all_pattern, self.result)
        rows = self.result[all_pattern]
        self.assertEqual(len(rows), 1, "Le pattern tout-ALL doit avoir 1 seule ligne.")
        self.assertEqual(rows[0]["COUNT"], TOTAL)

    def test_partial_aggregate_sums_to_total(self):
        """La somme des COUNT d'un pattern à 1 dimension libre doit égaler TOTAL
        si cette dimension a des valeurs identiques pour toutes les lignes.
        Ici Time est la même pour toutes les lignes, donc (False, True, False) regroupe tout."""
        # Le masque (True, True, False) agrège sur Geo et Time → 1 groupe par Food
        # La somme de tous ces groupes doit valoir TOTAL
        partial = (True, True, False)
        total_in_partial = sum(r["COUNT"] for r in self.result[partial])
        self.assertEqual(total_in_partial, TOTAL)

    # ── Présence des feuilles ──────────────────────────────────────────────────

    def test_leaf_pattern_contains_all_inputs(self):
        """Le pattern tout-spécifique (False,False,False) doit contenir autant
        de lignes que de lignes dans le dataset d'entrée."""
        leaf_pattern = (False, False, False)
        self.assertIn(leaf_pattern, self.result)
        self.assertEqual(len(self.result[leaf_pattern]), len(DATA))

    def test_leaf_counts_match_input_values(self):
        """Les COUNT du pattern feuille doivent correspondre exactement aux valeurs d'entrée."""
        leaf_rows = self.result[(False, False, False)]
        leaf_counts = sorted(r["COUNT"] for r in leaf_rows)
        input_counts = sorted(row[-1] for row in DATA.values())
        self.assertEqual(leaf_counts, input_counts)

    # ── Convention de nommage ALL ──────────────────────────────────────────────

    def test_all_marker_naming_convention(self):
        """Les marqueurs ALL doivent suivre la convention ALL_<première lettre de la dim>."""
        expected_prefixes = {d: f"ALL_{d[0].lower()}" for d in ["Geography", "Time", "Food"]}
        all_pattern = (True, True, True)
        row = self.result[all_pattern][0]
        for dim, expected_prefix in expected_prefixes.items():
            self.assertEqual(row[dim], expected_prefix,
                             f"Marqueur ALL incorrect pour '{dim}' : attendu '{expected_prefix}', obtenu '{row[dim]}'")

    # ── Dataset vide ──────────────────────────────────────────────────────────

    def test_empty_dataset(self):
        """Un dataset vide ne doit produire aucun cuboïde dans le résultat."""
        result = run(data={})
        total_rows = sum(len(v) for v in result.values())
        self.assertEqual(total_rows, 0, "Un dataset vide ne doit produire aucun cuboïde.")


if __name__ == "__main__":
    unittest.main()
