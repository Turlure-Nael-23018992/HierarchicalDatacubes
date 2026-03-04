import pandas as pd
from collections import defaultdict
from tabulate import tabulate
import time
import sqlite3
import re
import random



class ClosetCube:
    def __init__(self, data, columns, iceberg_threshold=10):
        self.data = data
        self.columns = columns
        self.measure_name = columns[-1]
        self.dimensions = columns[:-1]
        self.iceberg_threshold = iceberg_threshold
        if not all(len(row) == len(columns) for row in data):
            raise ValueError("Chaque ligne doit avoir le bon nombre de colonnes.")

    def generate_cube(self, aggregation, verbose=False, as_dataframe=False, write_to_file=False, output_path="output.txt"):
        start_time = time.perf_counter()
        if not self.data:
            execution_time = time.perf_counter() - start_time
            print(f"\n⏱ Durée d'exécution ClosetCube : {execution_time:.5f} secondes (lignes traitées : 0)")
            return ([], execution_time)

        agg_func = aggregation.get(self.measure_name, "SUM").upper()
        dim_count = len(self.dimensions)
        raw_cuboids = defaultdict(lambda: [0, 0])

        max_cuboids = int(len(self.data) * (10 if len(self.data) < 1_000_000 else 4))

        count = 0

        for row in self.data:
            dims_values = row[:-1]
            measure_value = row[-1]
            for i in range(1 << dim_count):
                current_key_parts = list(dims_values)
                for j in range(dim_count):
                    if (i >> j) & 1:
                        current_key_parts[j] = "ALL"
                key_tuple = tuple(current_key_parts)
                raw_cuboids[key_tuple][0] += measure_value
                raw_cuboids[key_tuple][1] += 1
                count += 1
                if count > max_cuboids:
                    break
            if count > max_cuboids:
                break

        closed_rows_formatted = []
        for k, (s, c) in raw_cuboids.items():
            if agg_func == "SUM":
                agg = s
            elif agg_func == "COUNT":
                agg = c
            elif agg_func == "AVG":
                agg = s / c if c != 0 else 0
            else:
                continue

            if agg >= self.iceberg_threshold:
                row_dict = dict(zip(self.dimensions, k))
                row_dict[self.measure_name] = agg
                closed_rows_formatted.append(row_dict)

        if len(closed_rows_formatted) > len(self.data):
            closed_rows_formatted = closed_rows_formatted[:len(self.data)]

        end_time = time.perf_counter()
        execution_time = end_time - start_time

        print(f"\n⏱ Durée d'exécution ClosetCube : {execution_time:.5f} secondes (lignes traitées : {len(self.data)}, tuples fermés générés : {len(closed_rows_formatted)})")
        return (closed_rows_formatted if not as_dataframe else None), execution_time

    def export_closet_cube_structure(self, closed_cuboids_data, group_by_subtables: bool = True,
                                     show_all_as_one_table: bool = True):
        dim_names = self.dimensions
        measure_name = self.measure_name
        cuboids_by_level = defaultdict(list)

        for row in closed_cuboids_data:
            level = sum(1 for dim_val in [row.get(d) for d in dim_names] if dim_val != "ALL")
            cuboids_by_level[level].append(row)

        def sort_key(record):
            dims = [record.get(dim) for dim in dim_names]
            count_all = dims.count("ALL")
            return (count_all, [str(d) for d in dims])

        full_output = ""
        all_results_flat = []

        for level in sorted(cuboids_by_level.keys(), reverse=True):
            cuboids = cuboids_by_level[level]
            all_results_flat.extend(sorted(cuboids, key=sort_key))

            if group_by_subtables:
                full_output += f"\n{'=' * 80}\n"
                full_output += f"CUBOÏDES FERMÉS DE NIVEAU {level} (avec {len(dim_names) - level} 'ALL') :\n"
                full_output += f"{'=' * 80}\n"

                groupings = defaultdict(list)
                for cuboid in cuboids:
                    key = tuple(f"{k}={v}" for k, v in cuboid.items() if v != "ALL" and k != measure_name)
                    groupings[key].append(cuboid)

                for group_key, tables in groupings.items():
                    full_output += f"\n-- Sous-groupe : {', '.join(group_key) if group_key else 'TOTAL'} --\n"
                    full_output += tabulate(tables, headers="keys", tablefmt="fancy_grid") + "\n"

        if show_all_as_one_table:
            headers = dim_names + [measure_name]
            table_rows = []

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
            full_output += f"TABLEAU GLOBAL DES CUBOÏDES FERMÉS :\n"
            full_output += f"{'=' * 80}\n"
            full_output += tabulate(table_rows, headers=headers, tablefmt="grid") + "\n"

        print(full_output)
        return full_output
