import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.databaseManagement.DataGenerator import *
from scripts.databaseManagement.Converter import *
from scripts.databaseManagement.processAlgo import *

"""nbTuples = 5
nbAttributes = 3
dbGenerator = DataGenerator(f"..//..//DB/aurelien_db_C{nbAttributes}_R{nbTuples}.db")
dbGenerator.generate_db_hierarchy(nbTuples, nbAttributes)

dbGenerator.generate_coded_db_dimensionJoueur(db_name="dimensionJoueur.db")
dbTest = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\dimensionJoueur.db")
data_dictJoueur = dbTest.toDict()
print("Dict Dimension Joueur :", data_dictJoueur)

dbGenerator.generate_coded_db_dimensionTour(db_name="dimensionTour.db")
dbTest2 = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\dimensionTour.db")
data_dictTour = dbTest2.toDict()
print("Dict Dimension Tour :", data_dictTour)

dbGenerator.generate_coded_db_dimensionSerie(db_name="dimensionSerie.db")
dbTest3 = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\dimensionSerie.db")
data_dictSerie = dbTest3.toDict()
print("Dict Dimension Serie :", data_dictSerie)

dbGenerator.generate_faitom3_from_dimensions(data_dictJoueur, data_dictTour, data_dictSerie, db_name="faitom3WithDim.db")
dbTest5 = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\faitom3WithDim.db")
data_dictFait = dbTest5.toDict()
print("Dict Dimension Faits with dim :", data_dictFait)

dbGenerator.generate_fact_table_faitom3(db_name="tableFaitNoDim.db")
dbTest4 = Converter("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\tableFaitNoDim.db")
data_dictTest4 = dbTest4.toDict()
# print("Dict Table faits :", data_dictTest4)

# dbGenerator.generate_random_coded_db_dimensionJoueur(50, db_name="RandomJoueur.db")
# dbGenerator.generate_random_coded_db_dimensionTour(50, db_name="RandomTour.db")
# dbGenerator.generate_random_coded_db_dimensionSerie(db_name="RandomSerie.db")"""

processor = ProcessAlgo("C:\\Users\\aure8\\Documents\\Cours\\CESI\\A4\\StageRecherche\\git\\HierarchicalDatacubes-Repo\\scripts\\databaseManagement\\dbToTest")

# processor.runBUC(False)
# processor.runStarCubing(False)
# processor.runClosetCube(False)
# processor.runHierarchicalBUC(False)
# processor.runHierarchicalStarCubing(False)
processor.runHierarchicalClosetCube(False)

dataGenerator = DataGenerator()
# dataGenerator.generatePokemonFactTable(True)
# dataGenerator.generate_generic_random_db(3, 2500000)
# dataGenerator.generate_hierarchical_facts_db(100000000)

processor.plot_execution_times_from_json("timings.json", "..\\output\\tikZ")
# processor.generate_execution_graphs_from_summary("timings.json", "..\\output\\tikZ")