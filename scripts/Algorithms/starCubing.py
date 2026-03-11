import time
from tabulate import tabulate
import random
from collections import defaultdict

class StarCubing:
    """
    Star-Cubing Algorithm Implementation.

    Star-Cubing uses a Star-tree structure to compress data, allowing for 
    efficient hierarchical and non-hierarchical aggregation by merging common prefixes.
    """
    def __init__(self, data, dimensions, iceberg_threshold=0):
        """
        Initialize Star-Cubing.

        Args:
            data (list): Input data rows.
            dimensions (list): List of dimension names (the last one is the measure).
            iceberg_threshold (int): Minimum measure value for a cuboid to be kept.
        """
        self.dims = dimensions[:-1]
        self.measure = dimensions[-1]
        self.iceberg_threshold = iceberg_threshold
        self.data = data

    def _group_by_dim(self, data_rows, dim_idx):
        """
        Group data rows based on a specific dimension.

        Args:
            data_rows (list): Subset of rows to group.
            dim_idx (int): The index of the dimension column.

        Returns:
            defaultdict: A mapping from dimension value to list of rows.
        """
        groups = defaultdict(list)
        for row in data_rows:
            groups[row[dim_idx]].append(row)
        return groups

    def _recursive_star_generator(self, data_subset, dim_idx):
        """
        Recursive generator that creates star-tree like aggregations.

        Args:
            data_subset (list): Subset of data to aggregate.
            dim_idx (int): Current dimension index in the recursion.

        Yields:
            tuple: (dim_combination, total_measure, count)
        """
        if dim_idx == len(self.dims):
            total = sum(row[-1] for row in data_subset)
            count = len(data_subset)
            yield tuple(), total, count
            return

        groups = self._group_by_dim(data_subset, dim_idx)
        for val, group_rows in groups.items():
            for key_tail, total, count in self._recursive_star_generator(group_rows, dim_idx + 1):
                yield (val,) + key_tail, total, count
        for key_tail, total, count in self._recursive_star_generator(data_subset, dim_idx + 1):
            yield ('ALL',) + key_tail, total, count

    def run(self, isPrinted=False, write_to_file=False, output_path="output.txt", aggregation: dict = None):
        """
        Execute the Star-Cubing algorithm.

        Args:
            isPrinted (bool): Whether to print results.
            write_to_file (bool): Whether to save results to a file.
            output_path (str): Path to the output file.
            aggregation (dict): Aggregation rules (e.g., {"Measure": "SUM"}).

        Returns:
            tuple: (results, execution_time)
        """
        start_time = time.perf_counter()
        measure_name = self.measure
        agg = (aggregation or {}).get(measure_name, "SUM").upper()
        generated_tuples = 0
        results = []

        for key, total, count in self._recursive_star_generator(self.data, 0):
            if agg == "SUM":
                value = total
            elif agg == "COUNT":
                value = count
            elif agg == "AVG":
                value = (total / count) if count else 0
            else:
                continue
            if value < self.iceberg_threshold:
                continue
            
            row_dict = dict(zip(self.dims, key))
            row_dict[measure_name] = value
            results.append(row_dict)
            generated_tuples += 1

        end_time = time.perf_counter()
        self.time = end_time - start_time
        print(f"\nDurée d'exécution StarCubing : {self.time:.5f} secondes (lignes traitées : {len(self.data)}, tuples générés : {generated_tuples})")
        return results, self.time


    def export_star_tree_like_structure(self,
                                        group_by_subtables: bool = True,
                                        show_all_as_one_table: bool = True,
                                        aggregation: dict = None):
        result, _ = self.run(isPrinted=False, aggregation=aggregation)

        dim_names = self.dims[:-1]
        measure_name = self.measure
        cuboids_by_level = defaultdict(list)

        for row in result:
            level = list(row.values())[:-1].count("ALL")
            cuboids_by_level[level].append(row)

        def sort_key(record):
            dims = [record.get(dim) for dim in dim_names]
            count_all = dims.count("ALL")
            return count_all, [str(d) for d in dims]

        full_output = ""
        all_results_flat = []

        for level in sorted(cuboids_by_level.keys()):
            cuboids = cuboids_by_level[level]
            all_results_flat.extend(sorted(cuboids, key=sort_key))

            if group_by_subtables:
                full_output += f"\n{'=' * 80}\n"
                full_output += f"CUBOÏDES DE NIVEAU {level} (avec {level} 'ALL') :\n"
                full_output += f"{'=' * 80}\n"

                groupings = defaultdict(list)
                for cuboid in cuboids:
                    key = tuple(k for k, v in cuboid.items() if v != "ALL" and k != measure_name)
                    groupings[key].append(cuboid)

                for group_key, tables in groupings.items():
                    full_output += f"\n-- Sous-groupe : {', '.join(group_key) if group_key else 'TOTAL'} --\n"
                    full_output += tabulate(tables, headers="keys", tablefmt="fancy_grid") + "\n"

        if show_all_as_one_table:
            headers = dim_names + [measure_name]
            table_rows = []

            # Tri avec ALL
            def sort_key(row):
                dims = [row.get(dim) for dim in dim_names]
                count_all = dims.count("ALL")
                return (count_all, [str(d) for d in dims])

            all_results_flat.sort(key=sort_key)

            last_all_count = -1
            for row in all_results_flat:
                dims = [row.get(dim) for dim in dim_names]
                current_all_count = dims.count("ALL")
                if current_all_count != last_all_count and table_rows:
                    table_rows.append(["=" * 10] * len(headers))
                table_rows.append([row.get(col, "") for col in headers])
                last_all_count = current_all_count
            full_output += f"\n{'=' * 80}\n"
            full_output += f"TABLEAU GLOBAL : toutes les combinaisons possibles\n"
            full_output += f"{'=' * 80}\n"
            full_output += tabulate(table_rows, headers=headers, tablefmt="grid") + "\n"

        print(full_output)
        return full_output
