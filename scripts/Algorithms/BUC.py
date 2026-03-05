import os
import time
import sqlite3
from collections import defaultdict
from tabulate import tabulate
from itertools import product

class BUC:
    """
    Bottom-Up Cubing (BUC) Algorithm Implementation.

    BUC is a recursive algorithm that computes a data cube by partitioning data 
    from the most detailed level up to the total aggregation.
    This implementation uses a flat permutation approach for lightweight processing.
    """
    def __init__(self, db_path, iceberg_threshold=1):
        """
        Initialize the BUC algorithm.

        Args:
            db_path (str): Path to the SQLite database.
            iceberg_threshold (int): Minimum value for an aggregate to be included (Iceberg Cube).
        """
        self.db_path = db_path
        self.iceberg_threshold = iceberg_threshold
        self.dim_names = []
        self.measure_name = ""
        self.use_count = False
        self.row_count = 0
        self.last_tuple_count = 0

    def run(self, isPrinted=False):
        """
        Execute the BUC algorithm.

        Args:
            isPrinted (bool): Whether to print the resulting cube to the console.

        Returns:
            tuple: (None, execution_time_in_seconds)
        """
        start_time = time.perf_counter()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(Pokemon)")
        columns_info = cursor.fetchall()
        all_columns = [row[1] for row in columns_info]
        filtered_columns = [col for col in all_columns if col.lower() not in ("rowid", "id", "row_id")]

        if len(filtered_columns) == 3:
            self.measure_name = "COUNT"
            self.dim_names = filtered_columns
            self.use_count = True
        else:
            self.measure_name = filtered_columns[-1]
            self.dim_names = filtered_columns[:-1]

        cursor.execute(f"SELECT COUNT(*) FROM Pokemon")
        total_rows = cursor.fetchone()[0]
        accum, elapsed = self.run_lightweight(filtered_columns)

        if isPrinted:
            self._print_results(accum)

        conn.close()
        print(f"\nDurée d'exécution BUC : {elapsed:.5f} secondes (lignes traitées : {self.row_count}, tuples générés : {self.last_tuple_count})")
        return accum, elapsed

    def run_lightweight(self, filtered_columns):
        """
        Process the database rows using a memory-efficient generator approach.

        Args:
            filtered_columns (list): Names of dimension and measure columns.

        Returns:
            float: Elapsed time for the computation.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        col_str = ", ".join(filtered_columns)
        cursor.execute(f"SELECT {col_str} FROM Pokemon")

        start_time = time.perf_counter()
        accum = defaultdict(float)
        tuple_count = 0

        while True:
            rows = cursor.fetchmany(100000)
            if not rows:
                break
            for row in rows:
                self.row_count += 1
                if self.row_count % 10000 == 0:
                    time.sleep(0.01)
                try:
                    measure = 1.0 if self.use_count else float(row[-1])
                    dims = row if self.use_count else row[:-1]
                    for mask in product((True, False), repeat=len(dims)):
                        key = tuple(dim if use else "ALL" for dim, use in zip(dims, mask))
                        accum[key] += measure
                    tuple_count += 2 ** len(dims)
                except ValueError:
                    continue

        conn.close()
        self.last_tuple_count = tuple_count
        return accum, time.perf_counter() - start_time


    def _update_aggregates(self, accumulators, dims, measure):
        """
        Update the aggregate counts for all possible masks of a given data row.

        Args:
            accumulators (dict): The mapping of dimension tuples to measure sums.
            dims (tuple): Dimension values of the current row.
            measure (float): Measure value of the current row.
        """
        for mask in product((True, False), repeat=len(dims)):
            key = tuple(dim if use else "ALL" for dim, use in zip(dims, mask))
            accumulators[key] += measure

    def _print_results(self, accumulators):
        """
        Print the final data cube in a grid format.

        Args:
            accumulators (dict): The final mapping of all cuboids.
        """
        if self.row_count > 100:
            print(f"⚠️ Impression désactivée automatiquement : la base contient {self.row_count} lignes (> 100)")
            return

        headers = self.dim_names + [self.measure_name]
        rows = [list(k) + [v] for k, v in accumulators.items() if v >= self.iceberg_threshold]

        def sort_key(row):
            dims = row[:-1]
            count_all = sum(1 for val in dims if val == "ALL")
            return count_all, [str(val) for val in dims]

        rows.sort(key=sort_key)

        final_rows = []
        last_all_count = -1
        for row in rows:
            dims = row[:-1]
            current_all_count = dims.count("ALL")
            if current_all_count != last_all_count and final_rows:
                final_rows.append(["=" * 10] * len(headers))
            final_rows.append(row)
            last_all_count = current_all_count

        print("\n" + tabulate(final_rows, headers=headers, tablefmt="grid"))