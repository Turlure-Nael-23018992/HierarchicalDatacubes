import time
from collections import defaultdict
from tabulate import tabulate
import itertools

class OptimizedHierarchicalStarCubing:
    """
    Highly Optimized Hierarchical Star-Cubing (Phase 1).
    
    Exploits hierarchies by:
    1. Pre-calculating hierarchical paths for all dimension values.
    2. Grouping raw data into unique leaf combinations first.
    3. Expanding ancestors sequentially.
    """
    def __init__(self, data_dict, dimensions, aggregation, hierarchies, iceberg_threshold=0):
        self.data = list(data_dict.values())
        self.dim_cols = [d for d in dimensions if d not in aggregation]
        self.measure_cols = list(aggregation.keys())
        self.aggregation = aggregation
        self.hierarchies = hierarchies
        self.iceberg_threshold = iceberg_threshold

        # Map child to parent for each dimension to build paths upwards
        self.child_to_parent = {}
        for dim, hierarchy in hierarchies.items():
            self.child_to_parent[dim] = {}
            for parent, children in hierarchy.items():
                for child in children:
                    self.child_to_parent[dim][child] = parent
        
        # Pre-cache hierarchy paths for efficiency
        self.path_cache = {}
        self.time = 0.0

    def _get_hierarchy_path(self, dim, value):
        cache_key = (dim, value)
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
            
        path = [value]
        curr = value
        mapping = self.child_to_parent.get(dim, {})
        while curr in mapping:
            parent = mapping[curr]
            path.append(parent)
            curr = parent
        if path[-1] != "ALL":
            path.append("ALL")
        
        res = path[::-1] # [ALL, ..., Value]
        self.path_cache[cache_key] = res
        return res

    def run(self, isPrinted=True):
        start_time = time.perf_counter()
        
        # 1. Base Aggregation (Leaf Level Grouping)
        leaf_counts = defaultdict(int)
        leaf_measures = defaultdict(lambda: defaultdict(float))
        
        for row in self.data:
            dim_vals = tuple(row[:len(self.dim_cols)])
            meas_vals = row[len(self.dim_cols):]
            
            leaf_counts[dim_vals] += 1
            for i, m_name in enumerate(self.measure_cols):
                val = meas_vals[i]
                op = self.aggregation[m_name]
                if op in ("SUM", "AVG"):
                    leaf_measures[dim_vals][m_name] += val
                elif op == "COUNT":
                    leaf_measures[dim_vals][m_name] += 1
                elif op == "MAX":
                    if m_name not in leaf_measures[dim_vals] or val > leaf_measures[dim_vals][m_name]:
                        leaf_measures[dim_vals][m_name] = val
                elif op == "MIN":
                    if m_name not in leaf_measures[dim_vals] or val < leaf_measures[dim_vals][m_name]:
                        leaf_measures[dim_vals][m_name] = val

        # 2. Sequential Expansion (Phase 1)
        final_cube = {}
        for leaf_dims, count in leaf_counts.items():
            measures = leaf_measures[leaf_dims]
            
            # Generate paths for each dimension
            paths = [self._get_hierarchy_path(self.dim_cols[i], leaf_dims[i]) for i in range(len(self.dim_cols))]
            
            # Cartesian product of ancestral paths
            for combo in itertools.product(*paths):
                if combo not in final_cube:
                    final_cube[combo] = {"count": 0, "measures": defaultdict(float)}
                
                entry = final_cube[combo]
                entry["count"] += count
                for m_name, m_val in measures.items():
                    op = self.aggregation[m_name]
                    if op in ("SUM", "AVG", "COUNT"):
                        entry["measures"][m_name] += m_val
                    elif op == "MAX":
                        if m_name not in entry["measures"] or m_val > entry["measures"][m_name]:
                            entry["measures"][m_name] = m_val
                    elif op == "MIN":
                        if m_name not in entry["measures"] or m_val < entry["measures"][m_name]:
                            entry["measures"][m_name] = m_val

        # 3. Post-process: Iceberg + Format
        results = []
        for combo, data in final_cube.items():
            if self.iceberg_threshold > 0:
                is_valid = False
                for m_name, m_val in data["measures"].items():
                    if m_val >= self.iceberg_threshold:
                        is_valid = True
                        break
                if not is_valid:
                    continue
            
            row = dict(zip(self.dim_cols, combo))
            for m_name, m_val in data["measures"].items():
                if self.aggregation[m_name] == "AVG":
                    row[m_name] = round(m_val / data["count"], 2)
                else:
                    row[m_name] = round(m_val, 2)
            results.append(row)

        self.time = time.perf_counter() - start_time
        
        if isPrinted:
            def sort_key(x):
                vals = []
                for d in self.dim_cols:
                    v = x[d]
                    if v == "ALL": vals.append("~~~")
                    else: vals.append(str(v))
                return tuple(vals)
            
            results.sort(key=sort_key)
            print(tabulate(results, headers="keys", tablefmt="grid"))
            print(f"\nDurée d'exécution Optimized Hierarchical Star-Cubing: {self.time:.5f} sec")
            
        return results

if __name__ == "__main__":
    hier = {
        "Geography": {"ALL": ["France"], "France": ["Paris", "Marseille"]},
        "Time": {"ALL": ["2023"], "2023": ["2023-01", "2023-02"]}
    }
    data = {0: ["Paris", "2023-01", 10], 1: ["Paris", "2023-02", 20], 2: ["Marseille", "2023-01", 30]}
    algo = OptimizedHierarchicalStarCubing(data, ["Geography", "Time", "Sales"], {"Sales": "SUM"}, hier)
    algo.run()
