import os
import sys

# Ensure scripts and Core are in the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.databaseManagement.UniversalLatexGenerator import UniversalLatexGenerator

class LatexMaker:
    """
    Wrapper class for UniversalLatexGenerator to provide a clean API for UI applications.
    """
    def __init__(self):
        self.generator = UniversalLatexGenerator()

    def generate_all_default_benchmarks(self, json_path, output_folder):
        """
        Generates the standard set of benchmark graphs defined in UniversalLatexGenerator.
        """
        # Ensure paths are absolute if relative paths are provided from UI
        if not os.path.isabs(json_path):
            json_path = os.path.join(project_root, json_path)
        if not os.path.isabs(output_folder):
            output_folder = os.path.join(project_root, output_folder)
            
        os.makedirs(output_folder, exist_ok=True)
        self.generator.generate_graphs_from_json(json_path, output_folder)

    def generate_custom_comparison(self, json_path, output_path, algos, title, x_mode="LinX", y_mode="LinY"):
        """
        Generates a custom comparison graph for a specific list of algorithms.
        """
        import json
        
        if not os.path.isabs(json_path):
            json_path = os.path.join(project_root, json_path)
        if not os.path.isabs(output_path):
            output_path = os.path.join(project_root, output_path)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(json_path, "r") as f:
            raw_data = json.load(f)

        time_dicts = []
        max_card = 0

        for algo in algos:
            d = {}
            # Handles both duration_seconds format from UniversalLatexGenerator logic 
            # and may need adaptation if JSON format varies (e.g. from benchmark.py directly)
            algo_data = raw_data.get(algo, {})
            
            # Check if it's the format with db names or direct row counts
            for key, val in algo_data.items():
                try:
                    # If key is numeric (like from benchmark.py)
                    card = int(key)
                    # Handle if val is a list of times or a single time
                    time = val[0] if isinstance(val, list) else val
                except ValueError:
                    # If key is a string (db name)
                    import re
                    match = re.search(r"_R(\d+)", key)
                    card = int(match.group(1)) if match else None
                    # Use duration_seconds if it's complex dict
                    time = val.get("duration_seconds") if isinstance(val, dict) else val

                if card is not None and time is not None:
                    d[card] = time
                    max_card = max(max_card, card)
            time_dicts.append(d)

        self.generator.output_path = output_path
        
        # Mapping UI modes to the generator's scaleType format
        scale_type = f"{x_mode}/{y_mode}"
        
        # New signature: (timeDicts, maxRowsList, maxTimeList, algos, attributes=[3], ...)
        self.generator.generate_latex(
            time_dicts, 
            [max_card], 
            [max(max(d.values(), default=0) for d in time_dicts if d)], 
            algos, 
            attributes=[3],
            scaleType=scale_type
        )

    def generate_single_algo_report(self, json_path, output_path, algo_name):
        """
        Generates a graph for a single algorithm.
        """
        self.generate_custom_comparison(
            json_path, 
            output_path, 
            [algo_name], 
            f"Performance of {algo_name}"
        )

if __name__ == "__main__":
    # Example usage for testing
    maker = LatexMaker()
    # Assume results are available in Assets/ExecutionTime/HierarchicalClosetCube/c3.json
    # maker.generate_single_algo_report("Assets/ExecutionTime/HierarchicalClosetCube/c3.json", "output/test.tex", "HierarchicalClosetCube")
    print("LatexMaker ready.")