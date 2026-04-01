from collections import defaultdict
import itertools
import time


class HierarchicalCompleteCube:
    """
    Hierarchical Complete Cube Algorithm.

    Produces the FULL hierarchical datacube — every possible aggregate cell,
    including cross-dimension projections to ALL — without any closedness
    filtering.

    Two-phase approach:
      Phase 1 — Hierarchical Roll-Up (same as LevelUpCube, optimized with
                 dim_index for O(1) lookups): builds every hierarchical
                 parent cell from its direct children, dimension by dimension.

      Phase 2 — ALL Expansion: for each non-empty subset of dimensions to
                 "collapse" to ALL, we aggregate the TOP-LEVEL values for
                 each collapsed dimension independently.
                 A cell contributes to a given ALL-subset projection if
                 its value for each collapsed dimension is at the TOP of
                 that dimension's hierarchy (i.e. has no parent).
                 This is O(|cube_compact| * 2^n_dims) — far smaller than
                 a fresh raw-data aggregation.
    """

    SENTINEL_ALL = "ALL"

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

        # child -> parent map
        self._inv_maps = {}
        for dim_name in self.dim_cols:
            self._inv_maps[dim_name] = {
                v: k
                for k, vs in self.hierarchy.get(dim_name, {}).items()
                for v in vs
            }

        # Pre-compute depth + group by depth for roll-up ordering
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

            vbd = defaultdict(list)
            for val, d in depth_map.items():
                if val in inv_map:
                    vbd[d].append(val)
            self._dim_vals_by_depth[dim_name] = vbd

    def generate_cube(self, aggregation_dict=None, verbose=False):
        """
        Build the complete hierarchical datacube.

        Returns a list of tuples: (dim0_val, dim1_val, ..., measure0, ...).
        Dimensions fully aggregated across all values use SENTINEL_ALL = 'ALL'.
        """
        start_time = time.perf_counter()

        if aggregation_dict is None:
            aggregation_dict = {"COUNT": "SUM"}

        n_dims = len(self.dim_cols)
        n_measures = len(self.measure_cols)
        ops = [aggregation_dict.get(m, "SUM") for m in self.measure_cols]
        ALL = self.SENTINEL_ALL

        # ------------------------------------------------------------------
        # Phase 1 — Pre-aggregate + Hierarchical Roll-Up
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
                cube_acc[dim_key] = [1 if ops[idx] == "COUNT" else measures[idx]
                                     for idx in range(n_measures)]
                cube_cnt[dim_key] = 1

        # dim_index for O(1) roll-up
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

            extra_leaves = []
            max_known = max(depth_map.values()) if depth_map else 0
            for val in set(dim_index[i].keys()):
                if val not in depth_map:
                    depth_map[val] = max_known + 1
                    extra_leaves.append(val)

            current_depth = max(depth_map.values(), default=0)
            while current_depth > 0:
                for val in vals_by_depth.get(current_depth, []):
                    p_val = inv_map[val]
                    for k in list(dim_index[i].get(val, [])):
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
                            for j in range(n_dims):
                                dim_index[j][pk[j]].add(pk)
                current_depth -= 1

            for val in extra_leaves:
                del depth_map[val]

        # Finalize AVG
        has_avg = any(op == "AVG" for op in ops)
        if has_avg:
            for key in cube_acc:
                for idx in range(n_measures):
                    if ops[idx] == "AVG":
                        cube_acc[key][idx] /= cube_cnt[key]

        # ------------------------------------------------------------------
        # Phase 2 — ALL Expansion
        #
        # Strategy: for each non-empty subset S of dimensions to project to
        # ALL, we find the "roof" values in those dimensions (values with no
        # parent). Only those roof cells contribute to the ALL projection,
        # preventing double-counting.
        #
        # Key insight: a cell k contributes to a projection where dimension i
        # is collapsed to ALL if and only if k[i] has NO parent in dim i's
        # hierarchy (it is already the topmost value).
        #
        # We iterate over all 2^n_dims -1 non-empty subsets of dimensions to
        # collapse. For each subset, we scan cells where ALL collapsed dims
        # are roof values and aggregate them into the ALL-key.
        # ------------------------------------------------------------------

        # Pre-compute roof value sets per dimension
        roof_per_dim = []
        for i, dim_name in enumerate(self.dim_cols):
            inv_map = self._inv_maps.get(dim_name, {})
            roof = {v for v in dim_index[i].keys() if v not in inv_map}
            roof_per_dim.append(roof)

        # For efficiency, build a reverse index: for each dim i,
        # roof_index[i] = set of keys whose dim i value is a roof value.
        roof_index = [set() for _ in range(n_dims)]
        for k in cube_acc:
            for i in range(n_dims):
                if k[i] in roof_per_dim[i]:
                    roof_index[i].add(k)

        all_cube = {}
        all_cnt = {}

        dim_indices = list(range(n_dims))
        for r in range(1, n_dims + 1):
            for subset in itertools.combinations(dim_indices, r):
                subset_set = set(subset)
                # Candidate keys: must be root in ALL collapsed dims
                # Start with roof_index of first collapsed dim, then intersect
                candidate_keys = roof_index[subset[0]]
                for idx in subset[1:]:
                    candidate_keys = candidate_keys & roof_index[idx]

                for k in candidate_keys:
                    proj_key = list(k)
                    for i in subset_set:
                        proj_key[i] = ALL
                    proj_key = tuple(proj_key)

                    a = cube_acc[k]
                    cnt = cube_cnt[k]

                    if proj_key in all_cube:
                        b = all_cube[proj_key]
                        all_cnt[proj_key] += cnt
                        for m_idx in range(n_measures):
                            op = ops[m_idx]
                            if op in ("SUM", "AVG", "COUNT"):
                                b[m_idx] += a[m_idx]
                            elif op == "MAX":
                                if a[m_idx] > b[m_idx]:
                                    b[m_idx] = a[m_idx]
                            elif op == "MIN":
                                if a[m_idx] < b[m_idx]:
                                    b[m_idx] = a[m_idx]
                    else:
                        all_cube[proj_key] = list(a)
                        all_cnt[proj_key] = cnt

        # Finalize AVG for ALL cells
        if has_avg:
            for key in all_cube:
                for idx in range(n_measures):
                    if ops[idx] == "AVG":
                        all_cube[key][idx] /= all_cnt[key]

        # Merge hierarchical cube + ALL projections
        full_cube = dict(cube_acc)
        full_cube.update(all_cube)

        if verbose:
            try:
                from tabulate import tabulate
                headers = self.dim_cols + self.measure_cols
                rows_out = sorted(
                    [list(k) + v for k, v in full_cube.items()],
                    key=lambda row: sum(1 for x in row[:n_dims] if x == ALL)
                )
                print(tabulate(rows_out, headers=headers, tablefmt="fancy_grid"))
            except ImportError:
                for k, v in sorted(full_cube.items()):
                    print(k, v)

        self.time = time.perf_counter() - start_time
        return [tuple(list(k) + v) for k, v in full_cube.items()]
