import sys
import os
import sqlite3

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
from scripts.Visualisation.cubeTikZ import *
from scripts.databaseManagement.DataGenerator import *


class Main():

    def __init__(self, fp, isPrinted=False):
        self.fp = fp
        self.isPrinted = isPrinted

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
            
            return new_data, dims + [measure_name], dims, measure_name
        else:
            # S'il y a plus de colonnes, on prend la dernière comme mesure
            measure_name = dims[-1]
            dim_names = dims[:-1]
            new_data = []
            for row in data:
                new_row = tuple(row[i] for i in range(len(allColumns)) if allColumns[i] in dims)
                new_data.append(new_row)
            return new_data, dims, dim_names, measure_name

    def runBUC(self):
        # BUC a déjà sa propre logique de chargement mais on peut forcer la cohérence
        self.BUC = BUC(self.fp)
        self.BUC.run(isPrinted=self.isPrinted)

    def runHierarchicalBUC(self):
        self.hBUC = HierarchicalBUC()
        self.hBUC.run_buc_from_simple_hierarchical_db(self.fp,isPrinted=self.isPrinted)

    def runStarCubing(self):
        data, all_cols, dims, measure = self._prepare_data()
        self.starCubing = StarCubing(data, all_cols)
        self.starCubing.run(aggregation={measure: "SUM"})
        if self.isPrinted:
            self.starCubing.export_star_tree_like_structure(aggregation={measure: "SUM"})

    def runHierarchicalStarCubing(self):
        self.hStartCubing = HierarchicalStarCubing({}, [], {"COUNT": "SUM"}, {})
        self.hStartCubing.run_from_db(self.fp, isPrinted=self.isPrinted)

    def runClosetCube(self):
        data, all_cols, dims, measure = self._prepare_data()
        self.closetCube = ClosetCube(data, all_cols)
        res, _ = self.closetCube.generate_cube(aggregation={measure: "SUM"})
        if self.isPrinted:
            self.closetCube.export_closet_cube_structure(res)

    def runHierarchicalClosetCube(self):
        data, all_cols, dims, measure = self._prepare_data()
        self.hClosetCube = HierarchicalClosetCube(data, all_cols, skip_first_col=False)
        self.hClosetCube.generate_closed_cube(verbose=self.isPrinted)

def print_menu():
    print("\n" + "="*50)
    print("       HIERARCHICAL DATACUBES - MENU")
    print("="*50)
    print("1. BUC (Base Plate)")
    print("2. Star-Cubing (Base Plate)")
    print("3. ClosetCube (Base Plate)")
    print("4. Hierarchical BUC (Base Hiérarchique)")
    print("5. Hierarchical Star-Cubing (Base Hiérarchique)")
    print("6. Hierarchical ClosetCube (Base Hiérarchique)")
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
        elif choice in ['4', '5', '6']:
            main = Main(db_hier, isPrinted=True)
            if choice == '4': main.runHierarchicalBUC()
            elif choice == '5': main.runHierarchicalStarCubing()
            elif choice == '6': main.runHierarchicalClosetCube()
        else:
            print("Option invalide, veuillez choisir entre 0 et 6.")
            continue

        input("\nAppuyez sur Entrée pour revenir au menu...")