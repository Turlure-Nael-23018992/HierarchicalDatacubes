import sys
import os
import sqlite3

# Ajout de la racine du projet au sys.path pour que les imports 'scripts.xyz' fonctionnent
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.Algorithms.BUC import BUC
from scripts.Algorithms.HierarchicalBUC import HierarchicalBUC
from scripts.Algorithms.starCubing import StarCubing
from scripts.Algorithms.HierarchicalStarCubing import HierarchicalStarCubing
from scripts.Algorithms.OptimizedHierarchicalStarCubing import OptimizedHierarchicalStarCubing
from scripts.utils.hierarchy_loader import get_default_hierarchy
from scripts.Algorithms.closetCube import ClosetCube
from scripts.Algorithms.HierarchicalClosetCube import HierarchicalClosetCube
from scripts.Algorithms.HierarchicalLevelUpCube import HierarchicalLevelUpCube
from scripts.Algorithms.HierarchicalCompleteCube import HierarchicalCompleteCube
from scripts.databaseManagement.Converter import Converter
from scripts.databaseManagement.dbGetter import dbGetter
#from scripts.Visualisation.cubeTikZ import *
from scripts.databaseManagement.DataGenerator import DataGenerator


class Main():

    def __init__(self, fp, isPrinted=False):
        self.fp = fp
        self.isPrinted = isPrinted
        self.time = 0

    def _prepare_data(self):
        dbGet = dbGetter(self.fp)
        tableName = dbGet.get_table_names()[0]
        allColumns = dbGet.get_column_names(tableName)
        
        # Filtrer RowId
        dims = [col for col in allColumns if col.lower() not in ("rowid", "id", "row_id")]
        data = dbGet.get_all_data(tableName)
        
        # On suppose que si on a 3 colonnes, ce sont Geography, Time, Food (ou Col_A, B, C)
        # Et qu'on veut compter les lignes.
        if len(dims) == 3:
            measure_name = "COUNT"
            # on garde les 3 comme dimensions et on ajoute 1.0 comme mesure
            # data est une liste de tuples. On veut (dim1, dim2, dim3, 1.0)
            # MAIS attention aux index dans les tuples originaux (qui ont RowId en 0)
            
            # On recrée les tuples sans RowId et avec 1.0 à la fin
            new_data = []
            for row in data:
                # row est (id, d1, d2, d3)
                new_row = tuple(row[i] for i in range(len(allColumns)) if allColumns[i] in dims) + (1.0,)
                new_data.append(new_row)
            
            dbGet.close()
            return new_data, dims + [measure_name], dims, measure_name
        else:
            # S'il y a plus de colonnes, on prend la dernière comme mesure
            measure_name = dims[-1]
            dim_names = dims[:-1]
            new_data = []
            for row in data:
                new_row = tuple(row[i] for i in range(len(allColumns)) if allColumns[i] in dims)
                new_data.append(new_row)
            
            dbGet.close()
            return new_data, dims, dim_names, measure_name

    def runBUC(self):
        # BUC a déjà sa propre logique de chargement mais on peut forcer la cohérence
        self.BUC = BUC(self.fp)
        results, elapsed = self.BUC.run(isPrinted=self.isPrinted)
        self.time = elapsed
        return results

    def runHierarchicalBUC(self):
        self.hBUC = HierarchicalBUC()
        results = self.hBUC.run_buc_from_simple_hierarchical_db(self.fp,isPrinted=self.isPrinted)
        self.time = self.hBUC.time
        return results

    def runStarCubing(self):
        data, all_cols, dims, measure = self._prepare_data()
        self.starCubing = StarCubing(data, all_cols)
        results, elapsed = self.starCubing.run(aggregation={measure: "SUM"})
        if self.isPrinted:
            self.starCubing.export_star_tree_like_structure(aggregation={measure: "SUM"})
        self.time = elapsed
        return results

    def runHierarchicalStarCubing(self):
        self.hStartCubing = HierarchicalStarCubing({}, [], {"COUNT": "SUM"}, {})
        results = self.hStartCubing.run_from_db(self.fp, isPrinted=self.isPrinted)
        self.time = self.hStartCubing.time
        return results

    def runOptimizedHierarchicalStarCubing(self):
        data, all_cols, dims, measure = self._prepare_data()
        hier = get_default_hierarchy()
        # Filter hierarchies to only include dimensions present in the data
        relevant_hier = {d: hier[d] for d in dims if d in hier}
        
        # Convert data list to dict for compatibility
        data_dict = {i: row for i, row in enumerate(data)}
        
        self.optHStar = OptimizedHierarchicalStarCubing(
            data_dict, all_cols, {measure: "SUM"}, relevant_hier
        )
        results = self.optHStar.run(isPrinted=self.isPrinted)
        self.time = self.optHStar.time
        return results

    def runClosetCube(self):
        data, all_cols, dims, measure = self._prepare_data()
        self.closetCube = ClosetCube(data, all_cols)
        results, exec_time = self.closetCube.generate_cube(aggregation={measure: "SUM"})
        if self.isPrinted:
            self.closetCube.export_closet_cube_structure(results)
        self.time = exec_time
        return results

    def runHierarchicalClosetCube(self):
        data, all_cols, dims, measure = self._prepare_data()
        self.hClosetCube = HierarchicalClosetCube(data, all_cols, skip_first_col=False)
        results = self.hClosetCube.generate_closed_cube(verbose=self.isPrinted)
        self.time = self.hClosetCube.time
        return results

    def runHierarchicalLevelUpCube(self):
        data, all_cols, dims, measure = self._prepare_data()
        self.hLevelUpCube = HierarchicalLevelUpCube(data, all_cols, skip_first_col=False)
        results = self.hLevelUpCube.generate_closed_cube(verbose=self.isPrinted)
        self.time = self.hLevelUpCube.time
        return results

    def runHierarchicalCompleteCube(self):
        data, all_cols, dims, measure = self._prepare_data()
        self.hCompleteCube = HierarchicalCompleteCube(data, all_cols, skip_first_col=False)
        results = self.hCompleteCube.generate_cube(verbose=self.isPrinted)
        self.time = self.hCompleteCube.time
        return results

def print_menu():
    print("\n" + "="*50)
    print("       HIERARCHICAL DATACUBES - MENU")
    print("="*50)
    print("1. BUC (Base Plate)")
    print("2. Star-Cubing (Base Plate)")
    print("3. ClosetCube (Base Plate)")
    print("4. Hierarchical BUC (Base Hiérarchique)")
    print("5. Hierarchical Star-Cubing (Base Hiérarchique)")
    print("9. Optimized Hierarchical Star-Cubing (NOUVEAU)")
    print("6. Hierarchical ClosetCube (Base Hiérarchique)")
    print("7. Hierarchical LevelUpCube (Base Hiérarchique - NOUVEAU)")
    print("8. Hierarchical CompleteCube (Base Hiérarchique - COMPLET)")
    print("0. Quitter")
    print("-" * 50)

if __name__ == "__main__":
    db_flat = os.path.join(project_root, "DB", "cosky_db_C3_R10.db")
    db_hier = os.path.join(project_root, "DB", "hierarchie_db_C3_R10.db")

    while True:
        print_menu()
        choice = input("Choisissez un algorithme à exécuter (0-6) : ").strip()
        
        if choice == '0':
            print("Au revoir !")
            break
            
        if choice in ['1', '2', '3']:
            main = Main(db_flat, isPrinted=True)
            if choice == '1': main.runBUC()
            elif choice == '2': main.runStarCubing()
            elif choice == '3': main.runClosetCube()
        elif choice in ['4', '5', '6', '7', '8', '9']:
            main = Main(db_hier, isPrinted=True)
            if choice == '4': main.runHierarchicalBUC()
            elif choice == '5': main.runHierarchicalStarCubing()
            elif choice == '6': main.runHierarchicalClosetCube()
            elif choice == '7': main.runHierarchicalLevelUpCube()
            elif choice == '8': main.runHierarchicalCompleteCube()
            elif choice == '9': main.runOptimizedHierarchicalStarCubing()
        else:
            print("Option invalide, veuillez choisir entre 0 et 9.")
            continue

        input("\nAppuyez sur Entrée pour revenir au menu...")