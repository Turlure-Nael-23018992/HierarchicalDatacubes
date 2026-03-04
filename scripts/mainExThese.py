from scripts.Algorithms.BUC import *
from scripts.Algorithms.HierarchicalStarCubing import HierarchicalStarCubing
from scripts.Algorithms.starCubing import *
from scripts.Algorithms.HierarchicalBUC import *
from scripts.Algorithms.closetCube import ClosetCube
from scripts.Algorithms.HierarchicalClosetCube import HierarchicalClosetCube

from scripts.databaseManagement.Converter import *

import os


data = {
        1: ("Féticheur", "Vitesse", "Bastion", 400),
        2: ("Féticheur", "Vitesse", "Marche", 100),
        3: ("Sorcière", "Chance", "Marche", 100),
        4: ("Sorcière", "Vitesse", "Bastion", 300),
        5: ("Croisé", "Chance", "Bastion", 200)
    }

# SUM = Somme ; AVG = Moyenne ; MIN = Minimum ; MAX = Maximum ; COUNT = Nombre de tuples
aggregation = {
        "SUM(Q)": "SUM"
    }

columns = ["T", "P", "E", "SUM(Q)"]

#################### BUC ####################
buc = BUC(data, columns)
# res_buc = buc.export_buc_tree_like_structure(aggregation=aggregation, group_by_subtables=False, show_all_as_one_table=False)

#################### StarCubing ####################
star = StarCubing(data, dimensions=columns, iceberg_threshold=0)
# star.export_star_tree_like_structure(aggregation=aggregation, group_by_subtables=False, show_all_as_one_table=False)

#################### ClosetCube ####################
# closetCube = ClosetCube(data, columns)
# closetCube.generate_cube(aggregation, verbose=False)

dbPath = "C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\faitom3WithDim.db"
db = Converter(dbPath)
data_dict = db.toDict()

dimensions = ["IdJ", "IdT", "IdS", "Temps", "Durée", "Nombre", "Score", "Forme"]
aggregation = {
    "Temps": "AVG",
    "Durée": "AVG",
    "Nombre": "AVG",
    "Score": "AVG",
    "Forme": "AVG"
}
hierarchy = {
    "IdJ": ["IdT", "IdS"],
    "IdT": ["IdS"],
    "IdS": []
}

#################### BUC hiérarchie ####################
hierarchicalBUC = HierarchicalBUC(data_dict, dimensions, aggregation, hierarchy)
# hierarchicalBUC.run_flat_buc_like_cube(data_dict, dimensions, aggregation, group_by_subtables=False, show_all_as_one_table=False)
# hierarchicalBUC.run_buc_from_db_with_hierarchy("databaseManagement\\TableFaitsExempleThese.db", "Pokemon", True)
hierarchicalBUC.run_buc_from_simple_hierarchical_db("databaseManagement\\dbToTest\\hierarchie\\hierarchie_db_C3_R1000.db")


#################### StarCubing hiérarchie ####################
hierarchicalStarCubing = HierarchicalStarCubing(data_dict, dimensions, aggregation, hierarchy)
hierarchicalStarCubing.run_flat_star_cubing(isPrinted=False)

#################### ClosetCube hiérarchie ####################
hierarchicalClosetCube = HierarchicalClosetCube(data_dict, dimensions, aggregation, hierarchy)
hierarchicalClosetCube.generate_closed_cube(verbose=False)