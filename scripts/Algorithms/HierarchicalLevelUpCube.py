from collections import defaultdict
import time


class HierarchicalLevelUpCube:
    """
    Optimized Hierarchical Level-Up Cubing Algorithm.

    Core insight: instead of finding all ancestors directly from leaves,
    we compute parent cells level-by-level from their direct children.

    Key optimizations over the naïve roll-up:
      - dim_index[i][val] -> set(keys): O(1) lookup of all cube cells
        containing a given value at dimension i, avoiding O(|cube|) scans.
      - vals_by_depth: pre-grouped values by depth so we never linearly
        scan the depth dict at every level iteration.
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
        self.time: float = 0

        if any(len(row) != len(self.dim_cols) + len(self.measure_cols) for row in self.data):
            raise ValueError("Longueur des tuples incohérente avec colonnes")

        # child -> parent mapping for fast lookup
        self._inv_maps = {}
        for dim_name in self.dim_cols:
            self._inv_maps[dim_name] = {
                v: k
                for k, vs in self.hierarchy.get(dim_name, {}).items()
                for v in vs
            }

        # Pre-compute depth of each node in each dimension hierarchy
        # depth[dim_name][val] = int  (0 = root / no parent, higher = deeper)
        self._dim_depths = {}
        self._dim_vals_by_depth = {}
        for dim_name in self.dim_cols:
            inv_map = self._inv_maps.get(dim_name, {})
            depth_map = {}

            def _get_depth(node, _inv=inv_map, _d=depth_map):
                if node in _d:
                    return _d[node]
                if node not in _inv:
                    _d[node] = 0
                    return 0
                v = 1 + _get_depth(_inv[node])
                _d[node] = v
                return v

            for val in inv_map:
                _get_depth(val)

            self._dim_depths[dim_name] = depth_map

            # Pre-group by depth (only nodes that have a parent)
            vbd = defaultdict(list)
            for val, d in depth_map.items():
                if val in inv_map:
                    vbd[d].append(val)
            self._dim_vals_by_depth[dim_name] = vbd

        self._ancestors_cache = {}

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

    def generate_closed_cube(self, aggregation_dict=None, verbose=False, as_dataframe=False):
        start_time = time.perf_counter()

        if aggregation_dict is None:
            aggregation_dict = {"COUNT": "SUM"}

        n_dims = len(self.dim_cols)
        n_measures = len(self.measure_cols)
        ops = [aggregation_dict.get(m, "SUM") for m in self.measure_cols]

        # ------------------------------------------------------------------
        # Step 1 — Pre-aggregate by unique dimension tuple (Base Cuboids)
        # ------------------------------------------------------------------
        cube_acc = {}
        cube_cnt = {}

        for row in self.data:
            dim_key = tuple(row[:n_dims])
            measures = row[n_dims:]

            if dim_key in cube_acc:
                a = cube_acc[dim_key]
                cube_cnt[dim_key] += 1
                for idx in range(n_measures):
                    op = ops[idx]
                    if op in ("SUM", "AVG"):
                        a[idx] += measures[idx]
                    elif op == "COUNT":
                        a[idx] += 1
                    elif op == "MAX":
                        if measures[idx] > a[idx]:
                            a[idx] = measures[idx]
                    elif op == "MIN":
                        if measures[idx] < a[idx]:
                            a[idx] = measures[idx]
            else:
                a = [1 if ops[idx] == "COUNT" else measures[idx] for idx in range(n_measures)]
                cube_acc[dim_key] = a
                cube_cnt[dim_key] = 1

        # ------------------------------------------------------------------
        # Step 2 — Dimension-by-Dimension Topological Roll-Up
        #
        # Optimization: dim_index[dim_pos][value] -> set of keys
        # Allows O(1) retrieval of all cells sharing a given value at position i
        # instead of scanning all cube keys each time.
        # ------------------------------------------------------------------
        dim_index = [defaultdict(set) for _ in range(n_dims)]
        for k in cube_acc:
            for i in range(n_dims):
                dim_index[i][k[i]].add(k)

        for i, dim_name in enumerate(self.dim_cols):
            inv_map = self._inv_maps.get(dim_name, {})
            if not inv_map:
                continue

            depth_map = self._dim_depths[dim_name]
            vals_by_depth = self._dim_vals_by_depth[dim_name]

            # Assign depth to any leaf values from DB not already in hierarchy
            unique_vals_in_cube = set(dim_index[i].keys())
            if depth_map:
                max_known = max(depth_map.values())
            else:
                max_known = 0
            extra_leaves = []
            for val in unique_vals_in_cube:
                if val not in depth_map:
                    depth_map[val] = max_known + 1
                    extra_leaves.append(val)

            current_depth = max(depth_map.values(), default=0)

            while current_depth > 0:
                for val in vals_by_depth.get(current_depth, []):
                    p_val = inv_map[val]
                    # O(1) lookup via dim_index
                    keys_with_val = list(dim_index[i].get(val, []))
                    for k in keys_with_val:
                        pk = k[:i] + (p_val,) + k[i + 1:]

                        pre_val = cube_acc[k]
                        pre_cnt = cube_cnt[k]

                        if pk in cube_acc:
                            a = cube_acc[pk]
                            cube_cnt[pk] += pre_cnt
                            for m_idx in range(n_measures):
                                op = ops[m_idx]
                                if op in ("SUM", "AVG", "COUNT"):
                                    a[m_idx] += pre_val[m_idx]
                                elif op == "MAX":
                                    if pre_val[m_idx] > a[m_idx]:
                                        a[m_idx] = pre_val[m_idx]
                                elif op == "MIN":
                                    if pre_val[m_idx] < a[m_idx]:
                                        a[m_idx] = pre_val[m_idx]
                        else:
                            cube_acc[pk] = list(pre_val)
                            cube_cnt[pk] = pre_cnt
                            # Register the new parent key in dim_index for all dims
                            for j in range(n_dims):
                                dim_index[j][pk[j]].add(pk)

                current_depth -= 1

            # Clean up temporary leaf entries in depth_map to keep it reusable
            for val in extra_leaves:
                del depth_map[val]

        # Finalize AVG
        aggregated = {}
        has_avg = any(op == "AVG" for op in ops)
        for key, a in cube_acc.items():
            if has_avg:
                result = list(a)
                for idx in range(n_measures):
                    if ops[idx] == "AVG":
                        result[idx] = a[idx] / cube_cnt[key]
                aggregated[key] = result
            else:
                aggregated[key] = a

        # ------------------------------------------------------------------
        # Step 3 — Closedness check via direct parent lookup
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
