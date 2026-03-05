import itertools
from collections import defaultdict
import time

class HierarchicalClosetCube:
    """
    Hierarchical ClosetCube Algorithm.

    Analyzes hierarchical structures to find closed cuboids, respecting 
    specified dimension levels (e.g., Parent-Child ancestors).
    """
    STATIC_HIERARCHY = {
        "Geography": {
            "ALL": ["Europe", "Amérique", "Asie"],
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
            "ALL": ["2021", "2022", "2023", "2024"],
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
            "ALL": ["Fruits", "Légumes", "Viandes", "Produits laitiers", "Céréales"],
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
        """
        Initialize Hierarchical ClosetCube.

        Args:
            data (list): Raw data rows.
            column_names (list): Headers for the data.
            iceberg_threshold (int): Minimum threshold for results.
            skip_first_col (bool): Whether the first column is an ID to be ignored.
        """
        self.iceberg_threshold = iceberg_threshold
        self.hierarchy = self.STATIC_HIERARCHY
        self.dim_cols = column_names[1:4] if skip_first_col else column_names[:3]
        self.measure_cols = column_names[4:] if skip_first_col else column_names[3:]

        self.data = [row[1:] if skip_first_col else row for row in data]

        if any(len(row) != len(self.dim_cols) + len(self.measure_cols) for row in self.data):
            raise ValueError("Longueur des tuples incohérente avec colonnes")

    def _get_all_ancestors(self, val, dim_name):
        """
        Retrieve all ancestors of a value within a specific dimension hierarchy.

        Args:
            val (str): The value to find ancestors for.
            dim_name (str): The name of the dimension.

        Returns:
            list: A list of ancestor values.
        """
        ancestors = []
        inv_map = {v: k for k, vs in self.hierarchy.get(dim_name, {}).items() for v in vs}
        current = val
        while current in inv_map:
            parent = inv_map[current]
            ancestors.append(parent)
            current = parent
        return ancestors

    def _generate_generalizations(self, row_dims):
        """
        Generate all valid hierarchical generalizations for a set of dimension values.

        Args:
            row_dims (list): Values for each dimension in a row.

        Returns:
            iterable: All valid combinations (product of value paths).
        """
        all_paths = []
        for dim_val, dim_name in zip(row_dims, self.dim_cols):
            ancestors = self._get_all_ancestors(dim_val, dim_name)
            all_paths.append([dim_val] + ancestors)
        return itertools.product(*all_paths)

    def generate_closed_cube(self, aggregation_dict=None, verbose=False, as_dataframe=False):
        """
        Generate the closed hierarchical data cube.

        Args:
            aggregation_dict (dict): Rules for aggregating measures.
            verbose (bool): If True, prints a fancy grid of results.
            as_dataframe (bool): Reserved for future use.

        Returns:
            list: List of closed hierarchical tuples.
        """
        if aggregation_dict is None:
            aggregation_dict = {"COUNT": "SUM"}

        cube = defaultdict(list)

        for row in self.data:
            dim_values = row[:len(self.dim_cols)]
            measures = row[len(self.dim_cols):]
            for combo in self._generate_generalizations(dim_values):
                cube[tuple(combo)].append(measures)

        aggregated = {}
        for key, rows in cube.items():
            result = []
            for i, m in enumerate(self.measure_cols):
                values = [r[i] for r in rows]
                op = aggregation_dict.get(m, "SUM")
                if op == "SUM":
                    result.append(sum(values))
                elif op == "COUNT":
                    result.append(len(values))
                elif op == "AVG":
                    result.append(sum(values) / len(values))
                elif op == "MAX":
                    result.append(max(values))
                elif op == "MIN":
                    result.append(min(values))
                else:
                    raise ValueError(f"Agrégation inconnue : {op}")
            aggregated[key] = result

        closed = {}
        for k1, v1 in aggregated.items():
            is_closed = True
            for k2, v2 in aggregated.items():
                if k1 == k2:
                    continue
                if self._is_more_general(k2, k1) and v1 == v2:
                    is_closed = False
                    break
            if is_closed:
                closed[k1] = v1

        if verbose:
            from tabulate import tabulate
            headers = self.dim_cols + self.measure_cols
            rows = [list(k) + v for k, v in closed.items()]
            print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

        return [tuple(list(k) + v) for k, v in closed.items()]

    def _is_more_general(self, gen, spec):
        return all(g == s or g in self._get_all_ancestors(s, dim_name)
                   for g, s, dim_name in zip(gen, spec, self.dim_cols))
