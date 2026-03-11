import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.Algorithms.FastHierarchicalClosetCube import FastHierarchicalClosetCube
from scripts.Algorithms.HierarchicalClosetCube import HierarchicalClosetCube

# Même dataset que test_HierarchicalClosetCube — les deux algos doivent produire
# des résultats sémantiquement identiques (même propriété fermée, même hiérarchie).
# Geography: Paris ∈ Île-de-France ∈ France ∈ Europe
#            Marseille ∈ PACA ∈ France ∈ Europe
# Time:      2022-01-01 ∈ 2022-01 ∈ 2022
# Food:      Fraise ∈ Fruits rouges ∈ Fruits
#            Framboise ∈ Fruits rouges ∈ Fruits
COLS = ["ID", "Geography", "Time", "Food", "COUNT"]
DATA = [
    (1, "Paris",     "2022-01-01", "Fraise",    10),
    (2, "Paris",     "2022-01-01", "Framboise",  5),
    (3, "Marseille", "2022-01-01", "Fraise",    20),
]
TOTAL = 35  # 10 + 5 + 20

VALID_GEO  = {"Paris", "Marseille", "Île-de-France", "PACA", "France", "Europe"}
VALID_TIME = {"2022-01-01", "2022-01", "2022"}
VALID_FOOD = {"Fraise", "Framboise", "Fruits rouges", "Fruits"}


def make_algo():
    return FastHierarchicalClosetCube(DATA, COLS, iceberg_threshold=0, skip_first_col=True)


class TestFastHierarchicalClosetCube(unittest.TestCase):
    """Tests des invariants théoriques du FastHierarchicalClosetCube.
    Même sémantique que HierarchicalClosetCube, avec un cache interne en plus."""

    def setUp(self):
        self.algo   = make_algo()
        self.result = self.algo.generate_closed_cube(aggregation_dict={"COUNT": "SUM"})
        self.dim_count = len(self.algo.dim_cols)

    # ── Propriété fermée ───────────────────────────────────────────────────────

    def test_closed_property(self):
        """Invariant fondamental : aucune paire (K1, K2) dans le résultat où K2
        est strictement plus général que K1 et a le même COUNT.
        L'algo FastClosetCube utilise une optimisation O(N) via regroupement par
        mesure, mais doit produire exactement les mêmes cuboïdes fermés."""
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

    def test_global_aggregate_equals_input_sum(self):
        """Le COUNT maximum dans le cube doit égaler la somme de tous les inputs."""
        max_count = max(t[-1] for t in self.result)
        self.assertEqual(max_count, TOTAL)

    def test_no_count_exceeds_total(self):
        """Aucun cuboïde ne peut avoir un COUNT supérieur à la somme totale des inputs."""
        for t in self.result:
            self.assertLessEqual(t[-1], TOTAL, f"COUNT {t[-1]} > TOTAL {TOTAL} pour {t}")

    def test_all_counts_strictly_positive(self):
        """Tout cuboïde dans le résultat doit avoir COUNT > 0."""
        for t in self.result:
            self.assertGreater(t[-1], 0, f"Cuboïde avec COUNT=0 : {t}")

    # ── Validité hiérarchique ──────────────────────────────────────────────────

    def test_dim_values_are_valid_hierarchy_nodes(self):
        """Toute valeur de dimension dans le résultat doit être une feuille ou
        un ancêtre valide dans STATIC_HIERARCHY."""
        for t in self.result:
            self.assertIn(t[0], VALID_GEO,  f"Valeur géo invalide : '{t[0]}'")
            self.assertIn(t[1], VALID_TIME, f"Valeur time invalide : '{t[1]}'")
            self.assertIn(t[2], VALID_FOOD, f"Valeur food invalide : '{t[2]}'")

    # ── Unicité ────────────────────────────────────────────────────────────────

    def test_no_duplicate_tuples(self):
        """Chaque clé de dimension doit apparaître au plus une fois."""
        dim_keys = [t[:self.dim_count] for t in self.result]
        self.assertEqual(len(dim_keys), len(set(dim_keys)),
                         "Des tuples de dimensions dupliqués ont été trouvés.")

    # ── Équivalence avec HierarchicalClosetCube ────────────────────────────────

    def test_same_results_as_reference_implementation(self):
        """FastHierarchicalClosetCube et HierarchicalClosetCube doivent produire
        exactement le même ensemble de cuboïdes fermés.
        L'optimisation ne doit changer que la vitesse, pas le résultat."""
        ref_algo   = HierarchicalClosetCube(DATA, COLS, iceberg_threshold=0, skip_first_col=True)
        ref_result = ref_algo.generate_closed_cube(aggregation_dict={"COUNT": "SUM"})

        fast_set = set(self.result)
        ref_set  = set(ref_result)
        self.assertEqual(fast_set, ref_set,
                         "FastHierarchicalClosetCube et HierarchicalClosetCube "
                         "ne produisent pas le même résultat.")

    # ── Cache interne ──────────────────────────────────────────────────────────

    def test_ancestor_cache_is_populated_after_run(self):
        """Le cache d'ancêtres doit être non vide après génération, ce qui confirme
        que la mise en cache est bien activée (et non contournée)."""
        self.assertGreater(len(self.algo._ancestors_cache), 0,
                           "Le cache d'ancêtres doit être peuplé après generate_closed_cube().")

    def test_generalization_cache_is_populated_after_run(self):
        """Le cache de généralisations doit être non vide après génération."""
        self.assertGreater(len(self.algo._generalizations_cache), 0,
                           "Le cache de généralisations doit être peuplé après generate_closed_cube().")

    def test_cache_gives_idempotent_results(self):
        """Un deuxième appel à generate_closed_cube() (avec cache déjà chaud)
        doit retourner exactement le même résultat que le premier appel."""
        result_second = self.algo.generate_closed_cube(aggregation_dict={"COUNT": "SUM"})
        self.assertEqual(set(self.result), set(result_second),
                         "Le résultat avec cache chaud diffère du résultat initial.")

    # ── Dataset vide ──────────────────────────────────────────────────────────

    def test_empty_dataset(self):
        """Un dataset vide doit retourner une liste vide."""
        algo_empty = FastHierarchicalClosetCube([], COLS, iceberg_threshold=0, skip_first_col=True)
        result = algo_empty.generate_closed_cube(aggregation_dict={"COUNT": "SUM"})
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
