import sys
import os
import sqlite3
import json
import time

# Ajout de la racine du projet au sys.path pour que les imports 'scripts.xyz' fonctionnent
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.Algorithms.BUC import *
from scripts.Algorithms.HierarchicalBUC import *
from scripts.Algorithms.starCubing import *
from scripts.Algorithms.HierarchicalStarCubing import *
from scripts.Algorithms.closetCube import *
from scripts.Algorithms.HierarchicalClosetCube import *
from scripts.databaseManagement.Converter import *
from scripts.databaseManagement.dbGetter import *
#from scripts.Visualisation.cubeTikZ import *
from scripts.databaseManagement.DataGenerator import *
from main import Main

ALGO = {
    "BUC": BUC,
    "HierarchicalBUC": HierarchicalBUC,
    "StarCubing": StarCubing,
    "HierarchicalStarCubing": HierarchicalStarCubing,
    "ClosetCube": ClosetCube,
    "HierarchicalClosetCube": HierarchicalClosetCube
}

COLS = [3]
ROWS = [10, 100, 500, 50000, 1000000 ] #

class Benchmark:
    def __init__(self, algo_name, isPrinted=False):
        self.isPrinted = isPrinted
        self.algo_name = algo_name
        self.algo = ALGO[algo_name]
        self.times = {}
        self.output_file = f"Assets/ExecutionTime/{algo_name}/c3.json"

    def run(self):
        for col in COLS:
            for row in ROWS:
                DataGenerator().generate_hierarchical_facts_db(row)
                self.fp = f"DB/hierarchie_db_C3_R{row}.db"
                if self.algo == BUC:
                    main = Main(self.fp, isPrinted=self.isPrinted)
                    main.runBUC()
                elif self.algo == HierarchicalBUC:
                    main = Main(self.fp, isPrinted=self.isPrinted)
                    main.runHierarchicalBUC()
                elif self.algo == StarCubing:
                    main = Main(self.fp, isPrinted=self.isPrinted)
                    main.runStarCubing()
                elif self.algo == HierarchicalStarCubing:
                    main = Main(self.fp, isPrinted=self.isPrinted)
                    main.runHierarchicalStarCubing()
                elif self.algo == ClosetCube:
                    main = Main(self.fp, isPrinted=self.isPrinted)
                    main.runClosetCube()
                elif self.algo == HierarchicalClosetCube:
                    main = Main(self.fp, isPrinted=self.isPrinted)
                    main.runFastHierarchicalClosetCube()
                self.times[row] = [main.time]
                print(f"Row {row}: {main.time}s")
                self.write_times()

    def write_times(self):
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        config_path = "nael-config.json"
        server_config = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                server_config = json.load(f)

        data = {
            "time_data": self.times,
            "max_rows": max(self.times.keys()) if self.times else 0,
            "max_time": max(t[0] for t in self.times.values()) if self.times else 0,
            "server_config": server_config
        }

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Results written to {self.output_file}")


if __name__ == "__main__":
    p = False
    '''benchmark = Benchmark("BUC", isPrinted=p)
    benchmark.run()
    benchmark = Benchmark("StarCubing", isPrinted=p)
    benchmark.run()
    benchmark = Benchmark("ClosetCube", isPrinted=p)
    benchmark.run()'''
    '''benchmark = Benchmark("HierarchicalStarCubing", isPrinted=p)
    benchmark.run()
    benchmark = Benchmark("HierarchicalBUC", isPrinted=p)
    benchmark.run()'''
    benchmark = Benchmark("HierarchicalClosetCube", isPrinted=p)
    benchmark.run()
