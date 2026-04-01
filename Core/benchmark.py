import sys
import os
import sqlite3
import json
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.Algorithms.BUC import *
from scripts.Algorithms.HierarchicalBUC import *
from scripts.Algorithms.starCubing import *
from scripts.Algorithms.HierarchicalStarCubing import *
from scripts.Algorithms.OptimizedHierarchicalStarCubing import *
from scripts.utils.hierarchy_loader import *
from scripts.Algorithms.closetCube import *
from scripts.Algorithms.HierarchicalClosetCube import *
from scripts.Algorithms.HierarchicalLevelUpCube import *
from scripts.Algorithms.HierarchicalCompleteCube import *
from scripts.databaseManagement.Converter import *
from scripts.databaseManagement.dbGetter import *
#from scripts.Visualisation.cubeTikZ import *
from scripts.databaseManagement.DataGenerator import *
from Core.main import Main

ALGO = {
    "BUC": BUC,
    "HierarchicalBUC": HierarchicalBUC,
    "StarCubing": StarCubing,
    "HierarchicalStarCubing": HierarchicalStarCubing,
    "ClosetCube": ClosetCube,
    "HierarchicalClosetCube": HierarchicalClosetCube,
    "HierarchicalLevelUpCube": HierarchicalLevelUpCube,
    "HierarchicalCompleteCube": HierarchicalCompleteCube,
    "OptimizedHierarchicalStarCubing": OptimizedHierarchicalStarCubing
}

COLS = [3]
ROWS = [10, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000, 2000000, 5000000] #

class Benchmark:
    def __init__(self, algo_name, isPrinted=False):
        self.isPrinted = isPrinted
        self.algo_name = algo_name
        self.algo = ALGO[algo_name]
        self.times = {}
        self.output_file = os.path.join(project_root, "Assets", "ExecutionTime", algo_name, "c3.json")

    def run(self):
        for col in COLS:
            for row in ROWS:
                fp = os.path.join(project_root, "DB", f"hierarchie_db_C3_R{row}.db")
                if not os.path.exists(fp):
                    continue
                
                main = Main(fp, isPrinted=self.isPrinted)
                if self.algo == BUC:
                    main.runBUC()
                elif self.algo == HierarchicalBUC:
                    main.runHierarchicalBUC()
                elif self.algo == StarCubing:
                    main.runStarCubing()
                elif self.algo == HierarchicalStarCubing:
                    main.runHierarchicalStarCubing()
                elif self.algo == ClosetCube:
                    main.runClosetCube()
                elif self.algo == HierarchicalClosetCube:
                    main.runHierarchicalClosetCube()
                elif self.algo == HierarchicalLevelUpCube:
                    main.runHierarchicalLevelUpCube()
                elif self.algo == HierarchicalCompleteCube:
                    main.runHierarchicalCompleteCube()
                elif self.algo == OptimizedHierarchicalStarCubing:
                    main.runOptimizedHierarchicalStarCubing()
                
                self.times[row] = [main.time]
                print(f"Row {row}: {main.time}s")
                self.save_single_result(row, main.time)

    def save_single_result(self, row, time_val):
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        config_path = os.path.join(project_root, "nael-config.json")
        server_config = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                server_config = json.load(f)

        combined_times = {}
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    combined_times = old_data.get("time_data", old_data)
                    if not isinstance(combined_times, dict):
                        combined_times = {}
            except Exception:
                pass

        str_row = str(row)
        new_time = time_val[0] if isinstance(time_val, list) else time_val
        
        should_write = False
        if str_row in combined_times:
            existing_val = combined_times[str_row]
            existing_time = existing_val[0] if isinstance(existing_val, list) else existing_val
            
            if new_time < existing_time:
                combined_times[str_row] = [new_time]
                should_write = True
                print(f"Updated {str_row} with faster time: {new_time}s")
        else:
            combined_times[str_row] = [new_time]
            should_write = True
            print(f"Added new result for {str_row}: {new_time}s")

        if should_write:
            max_rows = max([int(r) for r in combined_times.keys()]) if combined_times else 0
            max_time = max([t[0] if isinstance(t, list) else t for t in combined_times.values()]) if combined_times else 0

            data = {
                "time_data": combined_times,
                "max_rows": max_rows,
                "max_time": max_time,
                "server_config": server_config
            }

            temp_file = self.output_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            if os.path.exists(self.output_file):
                os.remove(self.output_file)
            os.rename(temp_file, self.output_file)
            print(f"Results persisted to {self.output_file}")


if __name__ == "__main__":
    p = False
    benchmark = Benchmark("OptimizedHierarchicalStarCubing", isPrinted=p)
    benchmark.run()
