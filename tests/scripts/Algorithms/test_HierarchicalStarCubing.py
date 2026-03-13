import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.Algorithms.HierarchicalStarCubing import HierarchicalStarCubing

# Dataset à 2 niveaux hiérarchiques de colonnes :
#   City (enfant) → Country (parent)
# La contrainte hiérarchique interdit : Country=ALL et City=specific simultanément.
# (Un pays ne peut pas être ignoré si on spécifie une ville)
DIMS      = ["City", "Country", "COUNT"]
AGG       = {"COUNT": "SUM"}
# format hierarchy attendu par HierarchicalStarCubing : {parent: [enfants]}
# → l'algo construit self.hierarchy = {enfant: parent} pour les cols présentes dans DIMS
HIERARCHY = {"Country": ["City"]}

DATA = {
    0: ["Paris",  "France",  10],
    1: ["Lyon",   "France",   5],
    2: ["Berlin", "Germany", 20],
}
TOTAL = 35   # 10 + 5 + 20


def run(data=None):
    d = data if data is not None else DATA
    hsc = HierarchicalStarCubing(d, DIMS, AGG, HIERARCHY)
    return hsc.run_star_cubing_with_hierarchy(isPrinted=False)


class TestHierarchicalStarCubing(unittest.TestCase):
    """Tests des invariants théoriques du StarCubing hiérarchique."""

    def setUp(self):
        self.result = run()

    # ── Contrainte hiérarchique ────────────────────────────────────────────────

    def test_no_invalid_hierarchy_combination(self):
        """Invariant clé : aucun tuple ne doit avoir Country=ALL avec City≠ALL.
        Cette combinaison est hiérarchiquement incohérente (ville connue mais pays ignoré).
        C'est la contrainte centrale que HierarchicalStarCubing ajoute au Star-Cubing classique."""
        for row in self.result:
            if row["Country"] == "ALL":
                self.assertEqual(row["City"], "ALL",
                                 f"Combinaison invalide : City={row['City']} mais Country=ALL")

    def test_valid_combinations_are_present(self):
        """Les combinaisons hiérarchiquement valides doivent toutes apparaître :
        (City=specific, Country=specific) et (City=ALL, Country=specific) et (City=ALL, Country=ALL)."""
        city_all_country_specific = [r for r in self.result if r["City"] == "ALL" and r["Country"] != "ALL"]
        city_specific_country_specific = [r for r in self.result if r["City"] != "ALL" and r["Country"] != "ALL"]
        city_all_country_all = [r for r in self.result if r["City"] == "ALL" and r["Country"] == "ALL"]

        self.assertGreater(len(city_all_country_specific), 0,
                           "Les rollups (City=ALL, Country=specific) doivent exister.")
        self.assertGreater(len(city_specific_country_specific), 0,
                           "Les tuples feuilles (City=specific, Country=specific) doivent exister.")
        self.assertEqual(len(city_all_country_all), 1,
                         "Le tuple global (ALL, ALL) doit apparaître exactement une fois.")

    # ── Conservation de la mesure ──────────────────────────────────────────────

    def test_global_aggregate_equals_input_sum(self):
        """Le tuple (City=ALL, Country=ALL) doit avoir COUNT = somme de tous les inputs."""
        global_rows = [r for r in self.result if r["City"] == "ALL" and r["Country"] == "ALL"]
        self.assertEqual(len(global_rows), 1)
        self.assertEqual(global_rows[0]["COUNT"], TOTAL)

    def test_no_count_exceeds_total(self):
        """Aucun cuboïde ne peut avoir un COUNT supérieur à la somme totale des inputs."""
        for row in self.result:
            self.assertLessEqual(row["COUNT"], TOTAL,
                                 f"COUNT {row['COUNT']} > TOTAL {TOTAL} pour {row}")

    # ── Monotonie hiérarchique ─────────────────────────────────────────────────

    def test_country_rollup_geq_city_count(self):
        """COUNT(City=ALL, Country=X) doit être ≥ COUNT(City=Y, Country=X) pour tout Y.
        Un rollup pays ne peut pas être inférieur à l'un de ses villes."""
        country_rollups = {r["Country"]: r["COUNT"]
                           for r in self.result if r["City"] == "ALL" and r["Country"] != "ALL"}
        city_specifics = [(r["Country"], r["COUNT"])
                          for r in self.result if r["City"] != "ALL"]

        for country, city_count in city_specifics:
            if country in country_rollups:
                self.assertGreaterEqual(
                    country_rollups[country], city_count,
                    f"Monotonie violée : COUNT(City=ALL, Country={country})={country_rollups[country]} "
                    f"< COUNT(ville)={city_count}"
                )

    def test_country_rollup_equals_sum_of_cities(self):
        """COUNT(City=ALL, Country=X) doit être exactement la somme des COUNT
        de toutes les villes de ce pays.
        Vérifie la cohérence verticale de l'agrégation."""
        country_rollups = {r["Country"]: r["COUNT"]
                           for r in self.result if r["City"] == "ALL" and r["Country"] != "ALL"}
        city_specifics  = {}
        for r in self.result:
            if r["City"] != "ALL":
                city_specifics.setdefault(r["Country"], 0)
                city_specifics[r["Country"]] += r["COUNT"]

        for country, expected_sum in city_specifics.items():
            self.assertIn(country, country_rollups,
                          f"Le rollup pour Country={country} est absent du résultat.")
            self.assertEqual(country_rollups[country], expected_sum,
                             f"Somme incohérente pour Country={country} : "
                             f"attendu {expected_sum}, obtenu {country_rollups[country]}")

    # ── Unicité ────────────────────────────────────────────────────────────────

    def test_no_duplicate_tuples(self):
        """Chaque combinaison (City, Country) ne doit apparaître qu'une seule fois."""
        keys = [(r["City"], r["Country"]) for r in self.result]
        self.assertEqual(len(keys), len(set(keys)), "Des tuples dupliqués ont été trouvés.")

    # ── Dataset vide ──────────────────────────────────────────────────────────

    def test_empty_dataset(self):
        """Un dataset vide ne doit produire aucun cuboïde."""
        result = run(data={})
        self.assertEqual(result, [], "Un dataset vide doit retourner une liste vide.")


if __name__ == "__main__":
    unittest.main()
