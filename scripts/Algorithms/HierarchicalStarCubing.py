from collections import defaultdict
from itertools import product
import re
from tabulate import tabulate
import time
import sqlite3
import pandas as pd


class HierarchicalStarCubing:
    def __init__(self, data_dict, dimensions, aggregation, hierarchy):
        self.data = list(data_dict.values())
        self.dim_cols = [d for d in dimensions if d not in aggregation]
        self.measure_cols = list(aggregation.keys())
        self.aggregation = aggregation

        self.hierarchy = {}
        for parent, children in hierarchy.items():
            for child in children:
                if child in self.dim_cols:
                    self.hierarchy[child] = parent

        self.dim_to_idx = {dim: i for i, dim in enumerate(self.dim_cols)}

    def _is_generalization_valid(self, key):
        for child, parent in self.hierarchy.items():
            if parent:
                child_idx = self.dim_to_idx[child]
                parent_idx = self.dim_to_idx[parent]
                if key[parent_idx] == "ALL" and key[child_idx] != "ALL":
                    return False
        return True

    def _generate_generalizations(self, row):
        options = [[val, "ALL"] for val in row]
        all_combinations = product(*options)
        return [combo for combo in all_combinations if self._is_generalization_valid(combo)]

    def _aggregate_measures(self, rows):
        result = {}
        for i, name in enumerate(self.measure_cols):
            col = [r[i] for r in rows]
            op = self.aggregation[name]
            if op == "SUM":
                result[name] = round(sum(col), 2)
            elif op == "AVG":
                result[name] = round(sum(col) / len(col), 2)
            elif op == "MAX":
                result[name] = round(max(col), 2)
            elif op == "MIN":
                result[name] = round(min(col), 2)
            else:
                raise ValueError(f"Agrégation non supportée : {op}")
        return result

    def run_star_cubing_with_hierarchy(self, isPrinted=True):
        start = time.perf_counter()
        agg_dict = defaultdict(list)
        for row in self.data:
            dim_vals = row[:len(self.dim_cols)]
            meas_vals = row[len(self.dim_cols):]
            for gen in self._generate_generalizations(dim_vals):
                agg_dict[gen].append(meas_vals)

        results = []
        for key, vals in agg_dict.items():
            row = dict(zip(self.dim_cols, key))
            row.update(self._aggregate_measures(vals))
            results.append(row)

        results.sort(key=lambda x: tuple(self._sort_key(x[d]) for d in self.dim_cols))
        if isPrinted:
            print(tabulate(results, headers="keys", tablefmt="grid"))
        return results

    def run_flat_star_cubing(self, isPrinted=True):
        start = time.perf_counter()
        n_dims = len(self.dim_cols)
        results_by_level = defaultdict(list)

        for mask in product([True, False], repeat=n_dims):
            agg_dict = defaultdict(list)
            for row in self.data:
                dims = row[:n_dims]
                meas = row[n_dims:]
                key = tuple("ALL" if m else d for d, m in zip(dims, mask))
                agg_dict[key].append(meas)

            for key, vals in agg_dict.items():
                row = dict(zip(self.dim_cols, key))
                row.update(self._aggregate_measures(vals))
                level = sum(1 for v in key if v == "ALL")
                results_by_level[level].append(row)

        def print_block(block):
            block.sort(key=lambda x: tuple(self._sort_key(x[d]) for d in self.dim_cols))
            print(tabulate(block, headers="keys", tablefmt="grid"))
            print("═" * 100)

        if isPrinted:
            for lvl in sorted(results_by_level):
                print_block(results_by_level[lvl])

        print(f"\n⏱ Durée d'exécution Hierarchical StarCubing 2: {time.perf_counter() - start:.5f} sec")
        return results_by_level

    def _sort_key(self, val):
        if val == "ALL": return float('inf')
        match = re.search(r'\d+', str(val))
        return int(match.group()) if match else float('inf')

    def run_from_db(self, db_path, table_name="Pokemon", isPrinted=True):
        start = time.perf_counter()

        # Chargement du .db
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()

        # Nettoyage
        df = df.dropna()

        # Ajout de COUNT si absent
        if "COUNT" not in df.columns:
            df["COUNT"] = 1

        data = df.values.tolist()
        columns = list(df.columns)

        measure_cols = ["COUNT"]
        dim_cols = [col for col in columns if col not in measure_cols]

        hierarchy = {
            "Geography": {
                # Super-catégorie
                "Europe": ["France", "Allemagne", "Espagne", "Italie", "Belgique"],

                # Pays → Régions
                "France": ["Île-de-France", "PACA", "Hauts-de-France"],
                "Allemagne": ["Bavière", "Rhénanie"],
                "Espagne": ["Catalogne", "Andalousie"],
                "Italie": ["Lombardie", "Piémont"],
                "Belgique": ["Wallonie"],

                # Régions → Villes enrichies
                "Île-de-France": ["Paris", "Nanterre", "Versailles", "Boulogne-Billancourt", "Saint-Denis"],
                "PACA": ["Marseille", "Nice", "Toulon", "Avignon", "Aix-en-Provence"],
                "Hauts-de-France": ["Lille", "Amiens", "Roubaix", "Tourcoing", "Dunkerque"],
                "Bavière": ["Munich", "Nuremberg", "Augsbourg", "Würzburg", "Rosenheim"],
                "Rhénanie": ["Francfort", "Hambourg", "Strasbourg", "Mayence", "Trèves"],
                "Catalogne": ["Barcelone", "Girona", "Lleida", "Tarragone", "Manresa"],
                "Andalousie": ["Séville", "Grenade", "Cordoue", "Málaga", "Almería"],
                "Lombardie": ["Milan", "Bergame", "Brescia", "Côme", "Pavie"],
                "Piémont": ["Turin", "Alessandria", "Asti", "Cuneo", "Novare"],
                "Wallonie": ["Liège", "Namur", "Charleroi", "Mons", "La Louvière"]
            },

            "Time": {
                # Année → Mois
                "2021": ["2021-12", "2021-05"],
                "2022": ["2022-01", "2022-12", "2022-07", "2022-04"],
                "2023": ["2023-01", "2023-02", "2023-07", "2023-08", "2023-12", "2023-05", "2023-11"],
                "2024": ["2024-03", "2024-06", "2024-07"],

                # Mois → Jours
                "2021-05": ["2021-05-01"],
                "2021-12": ["2021-12-31"],
                "2022-01": ["2022-01-01"],
                "2022-04": ["2022-04-01"],
                "2022-07": ["2022-07-04"],
                "2022-12": ["2022-12-24", "2022-12-31"],
                "2023-01": ["2023-01-01", "2023-01-15"],
                "2023-02": ["2023-02-01", "2023-02-14"],
                "2023-05": ["2023-05-08"],
                "2023-07": ["2023-07-01"],
                "2023-08": ["2023-08-01", "2023-08-15"],
                "2023-11": ["2023-11-11"],
                "2023-12": ["2023-12-25"],
                "2024-03": ["2024-03-08"],
                "2024-06": ["2024-06-30"],
                "2024-07": ["2024-07-01", "2024-07-14", "2024-07-31"]
            },

            "Food": {
                # Catégorie → Type
                "Fruits": ["Fruits rouges", "Agrumes"],
                "Légumes": ["Légumes verts", "Tubercules"],
                "Viandes": ["Viandes rouges", "Poissons"],
                "Produits laitiers": ["Fromages", "Yaourts"],
                "Céréales": ["Pâtes"],

                # Type → Produits
                "Fruits rouges": ["Fraise", "Framboise"],
                "Agrumes": ["Orange", "Citron"],
                "Légumes verts": ["Épinard", "Brocoli"],
                "Tubercules": ["Pomme de terre", "Carotte"],
                "Viandes rouges": ["Boeuf", "Poulet"],
                "Poissons": ["Saumon", "Thon"],
                "Fromages": ["Camembert", "Comté"],
                "Yaourts": ["Yaourt nature", "Yaourt aux fruits"],
                "Pâtes": ["Spaghetti", "Penne"]
            }
        }

        # Lancement du cube
        cube = HierarchicalStarCubing(
            {i: row for i, row in enumerate(data)},
            dimensions=dim_cols + measure_cols,
            aggregation={"COUNT": "SUM"},
            hierarchy=hierarchy
        )

        cube.run_star_cubing_with_hierarchy(isPrinted=isPrinted)

        elapsed = time.perf_counter() - start
        # print(f"\n⏱ Durée d'exécution HierarchicalStarCubing : {elapsed:.5f} secondes (lignes traitées : {len(data)})")
        print(f"\n⏱ Durée d'exécution HierarchicalStarCubing : {elapsed:.5f} secondes.")

        return {"success": True, "duration_seconds": round(elapsed, 5)}
