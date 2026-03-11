import time
import sqlite3
from collections import defaultdict
from tabulate import tabulate
from itertools import product
import re


class HierarchicalBUC:
    """
    Hierarchical Bottom-Up Cubing Algorithm.

    This algorithm extends BUC to handle hierarchical dimensions (e.g., Country > City).
    It respects hierarchical paths to avoid calculating invalid combinations.
    """
    # Hiérarchie statique intégrée à la classe
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

    def run_buc_from_simple_hierarchical_db(self, db_path, table_name="Pokemon", isPrinted=False):
        """
        Load data from a SQLite DB and run the hierarchical BUC algorithm.

        Args:
            db_path (str): Path to the SQLite database.
            table_name (str): Name of the table to process.
            isPrinted (bool): If True, prints the resulting cube.
        """
        start = time.time()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        
        columns = [desc[0] for desc in cursor.description]
        raw_rows = cursor.fetchall()
        conn.close()

        has_count = "COUNT" in columns
        data = []
        for row in raw_rows:
            if any(val is None for val in row):
                continue
            
            row_list = list(row)
            if not has_count:
                row_list.append(1)
            data.append(row_list)

        self.row_count = len(data)
        
        if not has_count:
            columns.append("COUNT")
            
        dims = [col for col in columns if col != "COUNT"]
        meas = ["COUNT"]

        results = self._run_flat_buc(
            {i: row for i, row in enumerate(data)},
            dims + meas,
            {"COUNT": "SUM"},
            self.STATIC_HIERARCHY,
            isPrinted=isPrinted
        )

        self.last_tuple_count = sum(len(g) for g in results.values())

        self.time = time.time() - start
        '''print(
            f"\nDurée d'exécution BUC hiérarchique : {self.time:.5f} secondes "
            f"(lignes traitées : {self.row_count}, tuples générés : {self.last_tuple_count})"
        )'''
        return results

    def _run_flat_buc(self, data_dict, dimensions, aggregation, hierarchy, isPrinted=True):
        """
        Core logic for processing hierarchical BUC calculations on a dataset.

        Args:
            data_dict (dict): Input data rows.
            dimensions (list): Column names.
            aggregation (dict): Aggregation functions for measures.
            hierarchy (dict): Hierarchical relationships.
            isPrinted (bool): If True, output results to terminal.

        Returns:
            dict: Grouped cuboids by their pattern.
        """
        data = list(data_dict.values())
        measure_names = list(aggregation.keys())
        dim_names = [d for d in dimensions if d not in measure_names]
        dim_suffixes = {d: f"ALL_{d[0].lower()}" for d in dim_names}
        results_by_pattern = defaultdict(list)

        for mask in product([True, False], repeat=len(dim_names)):
            groupings = defaultdict(list)
            for row in data:
                dims = row[:len(dim_names)]
                meas = row[len(dim_names):]
                key = tuple(dim_suffixes[dim_names[i]] if mask[i] else dims[i] for i in range(len(mask)))
                groupings[key].append(meas)

            for key, measures in groupings.items():
                result = dict(zip(dim_names, key))
                for i, m in enumerate(measure_names):
                    vals = [row[i] for row in measures]
                    if aggregation[m] == "SUM":
                        result[m] = sum(vals)
                    elif aggregation[m] == "AVG":
                        result[m] = round(sum(vals) / len(vals), 2)
                    elif aggregation[m] == "MAX":
                        result[m] = max(vals)
                    elif aggregation[m] == "MIN":
                        result[m] = min(vals)
                result["_pattern"] = tuple(k.startswith("ALL") for k in key)
                result["_all_count"] = result["_pattern"].count(True)
                results_by_pattern[result["_pattern"]].append(result)

        if isPrinted:
            self._print_results(results_by_pattern, dim_names, measure_names)

        return results_by_pattern

    def _print_results(self, results, dim_names, measure_names):
        """
        Perform complex sorting and printing of the hierarchical data cube results.

        Args:
            results (dict): Pattern-grouped results.
            dim_names (list): Dimension column names.
            measure_names (list): Measure column names.
        """
        def get_sort_key(val):
            if isinstance(val, str) and val.startswith("ALL"):
                return (1e9,)
            match = re.search(r'\d+', str(val))
            return (int(match.group()),) if match else (1e9,)

        all_rows = []
        for pattern in sorted(results, key=lambda p: (sum(p), p)):
            group = results[pattern]
            group.sort(key=lambda r: (r["_all_count"], [get_sort_key(r[d]) for d in dim_names]))
            all_rows.extend(group + [{"separator": True}])

        headers = dim_names + measure_names
        table = []
        for row in all_rows:
            if "separator" in row:
                table.append(["=" * 10] * len(headers))
            else:
                table.append([row.get(col, "") for col in headers])

        print("\n" + "=" * 80 + "\nTABLEAU GLOBAL DES CUBOÏDES\n" + "=" * 80)
        print(tabulate(table, headers=headers, tablefmt="fancy_grid"))
