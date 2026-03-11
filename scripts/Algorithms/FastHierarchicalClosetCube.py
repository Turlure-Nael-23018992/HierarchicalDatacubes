import itertools
from collections import defaultdict
import time


class FastHierarchicalClosetCube:
    """
    Optimized Hierarchical ClosetCube Algorithm.
    """
    STATIC_HIERARCHY = {
        "Geography": {
            "Europe": ["France", "Allemagne", "Espagne", "Italie", "Belgique"],
            "France": ["Île-de-France", "PACA", "Hauts-de-France"],
            "Allemagne": ["Bavière", "Rhénanie"],
            "Espagne": ["Catalogne", "Andalousie"],
            "Italie": ["Lombardie", "Piémont"],
            "Belgique": ["Wallonie"],
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
            "2021": ["2021-12", "2021-05"],
            "2022": ["2022-01", "2022-12", "2022-07", "2022-04"],
            "2023": ["2023-01", "2023-02", "2023-07", "2023-08", "2023-12", "2023-05", "2023-11"],
            "2024": ["2024-03", "2024-06", "2024-07"],
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
            "Fruits": ["Fruits rouges", "Agrumes"],
            "Légumes": ["Légumes verts", "Tubercules"],
            "Viandes": ["Viandes rouges", "Poissons"],
            "Produits laitiers": ["Fromages", "Yaourts"],
            "Céréales": ["Pâtes"],
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

    def __init__(self, data, column_names, iceberg_threshold=0, skip_first_col=True):
        self.iceberg_threshold = iceberg_threshold
        self.hierarchy = self.STATIC_HIERARCHY
        self.dim_cols = column_names[1:4] if skip_first_col else column_names[:3]
        self.measure_cols = column_names[4:] if skip_first_col else column_names[3:]

        self.data = [row[1:] if skip_first_col else row for row in data]
        self.time = 0

        if any(len(row) != len(self.dim_cols) + len(self.measure_cols) for row in self.data):
            raise ValueError("Longueur des tuples incohérente avec colonnes")

        self._inv_maps = {}
        for dim_name in self.dim_cols:
            self._inv_maps[dim_name] = {v: k for k, vs in self.hierarchy.get(dim_name, {}).items() for v in vs}

        self._ancestors_cache = {}
        self._generalizations_cache = {}

    def _get_all_ancestors(self, val, dim_name):
        cache_key = (val, dim_name)
        if cache_key in self._ancestors_cache:
            return self._ancestors_cache[cache_key]

        ancestors = []
        inv_map = self._inv_maps.get(dim_name, {})
        current = val
        while current in inv_map:
            parent = inv_map[current]
            ancestors.append(parent)
            current = parent

        self._ancestors_cache[cache_key] = ancestors
        return ancestors

    def _generate_generalizations(self, row_dims):
        cache_key = tuple(row_dims)
        if cache_key in self._generalizations_cache:
            return self._generalizations_cache[cache_key]

        all_paths = []
        for dim_val, dim_name in zip(row_dims, self.dim_cols):
            ancestors = self._get_all_ancestors(dim_val, dim_name)
            all_paths.append([dim_val] + ancestors)

        results = list(itertools.product(*all_paths))
        self._generalizations_cache[cache_key] = results
        return results

    def generate_closed_cube(self, aggregation_dict=None, verbose=False, as_dataframe=False):
        start_time = time.perf_counter()
        if aggregation_dict is None:
            aggregation_dict = {"COUNT": "SUM"}

        cube = defaultdict(list)

        for row in self.data:
            dim_values = row[:len(self.dim_cols)]
            measures = row[len(self.dim_cols):]
            for combo in self._generate_generalizations(dim_values):
                cube[combo].append(measures)

        aggregated = {}
        for key, rows in cube.items():
            result = []
            for i, m in enumerate(self.measure_cols):
                op = aggregation_dict.get(m, "SUM")
                if op == "SUM":
                    result.append(sum(r[i] for r in rows))
                elif op == "COUNT":
                    result.append(len(rows))
                elif op == "AVG":
                    result.append(sum(r[i] for r in rows) / len(rows))
                elif op == "MAX":
                    result.append(max(r[i] for r in rows))
                elif op == "MIN":
                    result.append(min(r[i] for r in rows))
                else:
                    raise ValueError(f"Agrégation inconnue : {op}")
            aggregated[key] = result

        closed = {}

        # Optimization 3: Replace O(N^2) matching with sub-O(N) generation check
        grouped_by_measure = defaultdict(set)
        for k, v in aggregated.items():
            grouped_by_measure[tuple(v)].add(k)

        for k1, v1 in aggregated.items():
            is_closed = True

            same_measure_keys = grouped_by_measure[tuple(v1)]

            # Since a tuple is NOT closed if a more general tuple has the EXACT SAME measure.
            # "More general tuple" literally means it's an ancestor combination of k1.
            # We can just generate all generalizations of k1, and check if any (except k1) exists in the same measure group.
            for gen_tuple in self._generate_generalizations(k1):
                if gen_tuple != k1 and gen_tuple in same_measure_keys:
                    is_closed = False
                    break

            if is_closed:
                closed[k1] = v1

        if verbose:
            from tabulate import tabulate
            headers = self.dim_cols + self.measure_cols
            rows = [list(k) + v for k, v in closed.items()]
            print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

        self.time = time.perf_counter() - start_time

        return [tuple(list(k) + v) for k, v in closed.items()]

    def _is_more_general(self, gen, spec):
        return all(g == s or g in self._get_all_ancestors(s, dim_name)
                   for g, s, dim_name in zip(gen, spec, self.dim_cols))