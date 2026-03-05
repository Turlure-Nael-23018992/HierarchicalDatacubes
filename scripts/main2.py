from scripts.Algorithms.BUC import *
from scripts.Algorithms.HierarchicalBUC import *
from scripts.Algorithms.starCubing import *
from scripts.Algorithms.HierarchicalStarCubing import *
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

dbPath = "C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\DB\\aurelien_db_C3_R5.db"
filename = os.path.splitext(os.path.basename(dbPath))[0]

db = Converter(dbPath)
data_dict = db.toDict()

# dbTest = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\dimensionJoueur.db")
# data_dictTest = dbTest.toDict()
# print("TEST dict :", data_dictTest)

# Connexion à la base de données
conn = sqlite3.connect(dbPath)
cursor = conn.cursor()

dbGetter1 = dbGetter(dbPath)
tableName = dbGetter1.get_table_names()[0]
columnNames = dbGetter1.get_column_names(tableName)
# print("Colonnes : ", columnNames)
nbTuples = dbGetter1.get_row_count(tableName)

# Fermer la connexion
conn.close()

# print("datadict : ", data_dict)

# Lancement de l'algo BUC

#buc = BUC(data_dict, columnNames[1:])
#res_buc = buc.run(True)

# Lancement de l'algo BUC avec gestion des hiérarchie

hierarchicalBUC = HierarchicalBUC(data_dict, columnNames[1:], hierarchy)
# res_hierarchicalBUC = hierarchicalBUC.run(True, visualize=True)

print("===========================================")

# Lancement de l'algo Star-Cubing

# cubing = StarCubing(data=data_dict, iceberg_threshold=2, skip_first_col= False)
# results = cubing.run(False)

# Lancement de l'algo Star-Cubing avec gestion des hiérarchie

hierarchicalStarCubing = HierarchicalStarCubing(data_dict, columnNames[1:], hierarchy, iceberg_threshold=0, skip_first_col=False)
# res_hierarchicalStarCubing = hierarchicalStarCubing.run(True)

# Visualisation des données
visualisation = False
if visualisation:
    output_path = os.path.join("output", "tikZ", f"{filename}_diagrammeTikz.tex")
    visualizer = cubeTikz(data_dict)
    visualizer.exportCubeToTikZ(columnNames[1:], filepath=output_path)
    visualizer.generateCube()

# PRESENTATION 20/06 exemple article

dbGenerator = DataGenerator(f"..//..//DB/aurelien_db_C0_R{nbTuples}.db")

dbGenerator.generate_coded_db_dimensionJoueur(db_name="databaseManagement\\dimensionJoueur.db")
dbTest = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\dimensionJoueur.db")
data_dictJoueur = dbTest.toDict()
print("Dict Dimension Joueur :", data_dictJoueur)

dbGenerator.generate_coded_db_dimensionTour(db_name="databaseManagement\\dimensionTour.db")
dbTest2 = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\dimensionTour.db")
data_dictTour = dbTest2.toDict()
print("Dict Dimension Tour :", data_dictTour)

dbGenerator.generate_coded_db_dimensionSerie(db_name="databaseManagement\\dimensionSerie.db")
dbTest3 = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\dimensionSerie.db")
data_dictSerie = dbTest3.toDict()
print("Dict Dimension Serie :", data_dictSerie)

dbGenerator.generate_faitom3_from_dimensions(data_dictJoueur, data_dictTour, data_dictSerie, db_name="databaseManagement\\faitom3WithDim.db")
dbTest5 = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\faitom3WithDim.db")
dbGetterTest = dbGetter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\faitom3WithDim.db")
data_dictFait = dbTest5.toDict()
print("Dict Dimension Faits with dim :", data_dictFait)

hierarchicalBUC.HierarchicalBUCexample(data_dictFait)
hierarchicalStarCubing.HierarchicalStarCubingExample(data_dictFait)