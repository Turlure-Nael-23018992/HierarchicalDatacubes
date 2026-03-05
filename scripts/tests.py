import sys
import os

# Ajout de la racine du projet au sys.path pour que les imports 'scripts.xyz' fonctionnent
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.Algorithms.BUC import *
from scripts.Algorithms.HierarchicalBUC import *
from scripts.Algorithms.starCubing import *
from scripts.Algorithms.HierarchicalStarCubing import *
from scripts.Algorithms.HierarchicalClosetCube import *
from scripts.databaseManagement.Converter import *
from scripts.databaseManagement.dbGetter import *
from scripts.Visualisation.cubeTikZ import *
from scripts.databaseManagement.DataGenerator import *


import sqlite3
import os

data = {
        1: ("Féticheur", "Vitesse", "Bastion", 400),
        2: ("Féticheur", "Vitesse", "Marche", 100),
        3: ("Sorcière", "Chance", "Marche", 100),
        4: ("Sorcière", "Vitesse", "Bastion", 300),
        5: ("Croisé", "Chance", "Bastion", 200)
    }

hierarchy = {
    "Ville": "Departement",
    "Departement": "Region",
    "Region": None,
    "Jour": "Mois",
    "Mois": "Annee",
    "Annee": None,
    "NomPokemon": "Type",
    "Type": "Generation",
    "Generation": None
}

is_printed = True

#Hierarchical BUC

dbPath = os.path.join(project_root, "DB", "hierarchie_db_C3_R10.db")

hBUC = HierarchicalBUC()
hBUC.run_buc_from_simple_hierarchical_db(dbPath,isPrinted=is_printed)

#Hierarchical Star Cubing

hStarCubing = HierarchicalStarCubing({}, [], {"COUNT": "SUM"}, {})
hStarCubing.run_from_db(dbPath, isPrinted=is_printed)

#Hierarchical ClosetCube

HClosetCube = HierarchicalClosetCube({}, [], {"COUNT": "SUM"}, skip_first_col=False)
HClosetCube.generate_closed_cube()
