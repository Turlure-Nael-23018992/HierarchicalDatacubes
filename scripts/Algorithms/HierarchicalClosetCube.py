import itertools
from collections import defaultdict
import time


class HierarchicalClosetCube:
    """
    Optimized Hierarchical ClosetCube Algorithm.

    Core insight: at 1M rows, the dimension space (Geography × Time × Food) is
    finite and small. Pre-aggregating by unique dimension tuple reduces the
    generalization fan-out from O(N) to O(U) where U << N.

    Pipeline:
      1. Pre-aggregate raw data by unique dim tuple → U unique cells (U << N)
      2. For each unique cell, generate generalizations and merge into cube
      3. Closedness check via direct parent lookup (O(K × D))
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
            self._inv_maps[dim_name] = {
                v: k
                for k, vs in self.hierarchy.get(dim_name, {}).items()
                for v in vs
            }

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

        n_dims = len(self.dim_cols)
        n_measures = len(self.measure_cols)
        ops = [aggregation_dict.get(m, "SUM") for m in self.measure_cols]

        # ------------------------------------------------------------------
        # Step 1 — Pre-aggregate by unique dimension tuple
        #
        # Key optimization: instead of iterating all N rows × all combos,
        # first collapse N rows into U unique dim-tuples (U is bounded by the
        # finite cartesian product of leaf values — typically U << N at scale).
        #
        # This means _generate_generalizations is called at most U times,
        # and the expensive combo fan-out loop runs U times instead of N times.
        # ------------------------------------------------------------------
        leaf_acc = {}   # dim_key -> [agg_value per measure]
        leaf_cnt = {}   # dim_key -> row count (for AVG)

        for row in self.data:
            dim_key = tuple(row[:n_dims])
            measures = row[n_dims:]

            if dim_key in leaf_acc:
                a = leaf_acc[dim_key]
                leaf_cnt[dim_key] += 1
                for i in range(n_measures):
                    op = ops[i]
                    if op == "SUM" or op == "AVG":
                        a[i] += measures[i]
                    elif op == "COUNT":
                        a[i] += 1
                    elif op == "MAX":
                        if measures[i] > a[i]:
                            a[i] = measures[i]
                    elif op == "MIN":
                        if measures[i] < a[i]:
                            a[i] = measures[i]
            else:
                a = []
                for i in range(n_measures):
                    a.append(1 if ops[i] == "COUNT" else measures[i])
                leaf_acc[dim_key] = a
                leaf_cnt[dim_key] = 1

        # ------------------------------------------------------------------
        # Step 2 — Expand unique cells into the full cube via generalization
        #
        # Now we only loop over U unique dim-tuples (not N raw rows).
        # Each unique cell fans out to its ancestor combos and merges its
        # already-aggregated value — no raw measure lists needed.
        # ------------------------------------------------------------------
        cube_acc = {}
        cube_cnt = {}

        for dim_key, pre_agg in leaf_acc.items():
            pre_cnt = leaf_cnt[dim_key]

            for combo in self._generate_generalizations(dim_key):
                if combo in cube_acc:
                    a = cube_acc[combo]
                    cube_cnt[combo] += pre_cnt
                    for i in range(n_measures):
                        op = ops[i]
                        if op == "SUM" or op == "AVG" or op == "COUNT":
                            a[i] += pre_agg[i]
                        elif op == "MAX":
                            if pre_agg[i] > a[i]:
                                a[i] = pre_agg[i]
                        elif op == "MIN":
                            if pre_agg[i] < a[i]:
                                a[i] = pre_agg[i]
                else:
                    cube_acc[combo] = list(pre_agg)
                    cube_cnt[combo] = pre_cnt

        # Finalize AVG
        aggregated = {}
        for key, a in cube_acc.items():
            result = list(a)
            for i in range(n_measures):
                if ops[i] == "AVG":
                    result[i] = a[i] / cube_cnt[key]
            aggregated[key] = result

        # ------------------------------------------------------------------
        # Step 3 — Closedness check via direct parent lookup (O(K × D))
        #
        # For each cube key, check only its D immediate parents (one per dim).
        # Correctness: if a distant ancestor shares the same measures, the
        # direct parent does too (monotonicity of aggregation over supersets).
        # ------------------------------------------------------------------
        key_set = set(aggregated.keys())
        inv_maps = self._inv_maps

        closed = {}
        for k, v in aggregated.items():
            v_tuple = tuple(v)
            is_closed = True

            for i, dim_name in enumerate(self.dim_cols):
                parent_val = inv_maps.get(dim_name, {}).get(k[i])
                if parent_val is not None:
                    parent_key = k[:i] + (parent_val,) + k[i + 1:]
                    if parent_key in key_set and tuple(aggregated[parent_key]) == v_tuple:
                        is_closed = False
                        break

            if is_closed:
                closed[k] = v

        if verbose:
            from tabulate import tabulate
            headers = self.dim_cols + self.measure_cols
            rows_out = [list(k) + v for k, v in closed.items()]
            print(tabulate(rows_out, headers=headers, tablefmt="fancy_grid"))

        self.time = time.perf_counter() - start_time

        return [tuple(list(k) + v) for k, v in closed.items()]

    def _is_more_general(self, gen, spec):
        return all(
            g == s or g in self._get_all_ancestors(s, dim_name)
            for g, s, dim_name in zip(gen, spec, self.dim_cols)
        )