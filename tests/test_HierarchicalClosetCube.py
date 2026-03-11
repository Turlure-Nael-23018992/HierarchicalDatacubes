import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.Algorithms.HierarchicalClosetCube import HierarchicalClosetCube

# Colonnes : ID (ignoré) | Geography | Time | Food | COUNT
# Hiérarchies utilisées (STATIC_HIERARCHY) :
#   Paris → Île-de-France → France → Europe
#   Marseille → PACA → France → Europe
#   2022-01-01 → 2022-01 → 2022
#   Fraise → Fruits rouges → Fruits
#   Framboise → Fruits rouges → Fruits
COLS = ["ID", "Geography", "Time", "Food", "COUNT"]
DATA = [
    (1, "Paris",     "2022-01-01", "Fraise",    10),
    (2, "Paris",     "2022-01-01", "Framboise",  5),
    (3, "Marseille", "2022-01-01", "Fraise",    20),
]
TOTAL = 35   # 10 + 5 + 20

# Ancêtres valides dans STATIC_HIERARCHY pour ce dataset
VALID_GEO   = {"Paris", "Marseille", "Île-de-France", "PACA", "France", "Europe"}
VALID_TIME  = {"2022-01-01", "2022-01", "2022"}
VALID_FOOD  = {"Fraise", "Framboise", "Fruits rouges", "Fruits"}


def make_algo():
    return HierarchicalClosetCube(DATA, COLS, iceberg_threshold=0, skip_first_col=True)


class TestHierarchicalClosetCube(unittest.TestCase):
    """Tests des invariants théoriques du ClosetCube hiérarchique."""

    def setUp(self):
        self.algo   = make_algo()
        self.result = self.algo.generate_closed_cube(aggregation_dict={"COUNT": "SUM"})
        # Chaque élément est un tuple (geo, time, food, count)
        self.dim_count = len(self.algo.dim_cols)

    # ── Propriété fermée ───────────────────────────────────────────────────────

    def test_closed_property(self):
        """Invariant fondamental : pour toute paire (K1, K2) dans le résultat,
        si K2 est strictement plus générale que K1 (K2 = ancêtre de K1),
        alors COUNT(K1) ≠ COUNT(K2).
        Un cuboïde non fermé serait redondant avec un ancêtre de même mesure."""
        for t1 in self.result:
            k1, v1 = t1[:self.dim_count], t1[self.dim_count]
            for t2 in self.result:
                k2, v2 = t2[:self.dim_count], t2[self.dim_count]
                if k1 == k2:
                    continue
                if self.algo._is_more_general(k2, k1):
                    self.assertNotEqual(
                        v1, v2,
                        f"Propriété fermée violée : {k2}={v2} est plus général que "
                        f"{k1}={v1} avec le même COUNT"
                    )

    # ── Conservation de la mesure ──────────────────────────────────────────────

    def test_global_aggregate_present_and_correct(self):
        """Le cuboïde racine (ancêtre commun de toutes les lignes) doit exister
        et avoir COUNT = somme de tous les inputs."""
        # L'ancêtre commun de Paris et Marseille est France (ou Europe),
        # tous deux avec même Time=2022 et Food=Fruits.
        # Au moins un tuple racine de COUNT=TOTAL doit exister.
        max_count = max(t[-1] for t in self.result)
        self.assertEqual(max_count, TOTAL,
                         "Le COUNT maximum dans le cube doit égaler la somme totale des inputs.")

    def test_no_count_exceeds_total(self):
        """Aucun cuboïde ne peut avoir un COUNT supérieur à la somme totale des inputs."""
        for t in self.result:
            self.assertLessEqual(t[-1], TOTAL,
                                 f"COUNT {t[-1]} > TOTAL {TOTAL} pour le tuple {t}")

    def test_all_counts_strictly_positive(self):
        """Tout cuboïde dans le résultat doit avoir COUNT > 0."""
        for t in self.result:
            self.assertGreater(t[-1], 0, f"Cuboïde avec COUNT=0 trouvé : {t}")

    # ── Validité hiérarchique des valeurs ──────────────────────────────────────

    def test_dim_values_are_valid_hierarchy_nodes(self):
        """Toute valeur de dimension dans le résultat doit être soit une valeur
        d'entrée, soit un ancêtre valide dans STATIC_HIERARCHY.
        Une valeur hors hiérarchie signalerait un bug de généralisation."""
        for t in self.result:
            geo, time, food = t[0], t[1], t[2]
            self.assertIn(geo,  VALID_GEO,  f"Valeur géo invalide : '{geo}'")
            self.assertIn(time, VALID_TIME, f"Valeur time invalide : '{time}'")
            self.assertIn(food, VALID_FOOD, f"Valeur food invalide : '{food}'")

    # ── Unicité ────────────────────────────────────────────────────────────────

    def test_no_duplicate_tuples(self):
        """Chaque clé de dimension doit apparaître au plus une fois dans le résultat."""
        dim_keys = [t[:self.dim_count] for t in self.result]
        self.assertEqual(len(dim_keys), len(set(dim_keys)),
                         "Des tuples de dimensions dupliqués ont été trouvés.")

    # ── Dataset vide ──────────────────────────────────────────────────────────

    def test_empty_dataset(self):
        """Un dataset vide doit retourner une liste vide (pas de cuboïdes à fermer)."""
        algo_empty = HierarchicalClosetCube([], COLS, iceberg_threshold=0, skip_first_col=True)
        result = algo_empty.generate_closed_cube(aggregation_dict={"COUNT": "SUM"})
        self.assertEqual(result, [], "Un dataset vide doit retourner une liste vide.")


if __name__ == "__main__":
    unittest.main()
