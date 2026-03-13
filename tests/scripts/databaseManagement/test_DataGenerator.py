import unittest
import os
import sqlite3
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.databaseManagement.DataGenerator import DataGenerator

class TestDataGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = DataGenerator()
        self.db_files = []

    def tearDown(self):
        for f in self.db_files:
            if os.path.exists(f):
                os.remove(f)

    def _track_file(self, filename):
        if filename not in self.db_files:
            self.db_files.append(filename)
        return filename

    def test_generate_db_hierarchy_3_cols(self):
        db_name = self._track_file("test_hierarchy_3.db")
        gen = DataGenerator(db_name)
        gen.generate_db_hierarchy(nb_lignes=10, nb_colonnes=3)
        
        self.assertTrue(os.path.exists(db_name))
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Pokemon")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 10)
        conn.close()

    def test_generate_random_coded_db_dimensionTour(self):
        db_name = self._track_file("test_tour.db")
        self.generator.generate_random_coded_db_dimensionTour(nb_lignes=5, db_name=db_name)
        
        self.assertTrue(os.path.exists(db_name))
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Pokemon")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 5)
        conn.close()

    def test_generatePokemonFactTable(self):
        # This creates Pokemon.db by default
        db_name = self._track_file("Pokemon.db")
        self.generator.generatePokemonFactTable(isDetailed=True)
        
        self.assertTrue(os.path.exists(db_name))
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Pokemon")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0)
        conn.close()

    def test_generate_random_coded_db_dimensionJoueur(self):
        db_name = self._track_file("test_joueur_random.db")
        self.generator.generate_random_coded_db_dimensionJoueur(nb_lignes=5, db_name=db_name)
        self.assertTrue(os.path.exists(db_name))

    def test_generate_random_coded_db_dimensionSerie(self):
        db_name = self._track_file("test_serie_random.db")
        self.generator.generate_random_coded_db_dimensionSerie(db_name=db_name, nb_series=2)
        self.assertTrue(os.path.exists(db_name))

    def test_generate_coded_db_dimensionJoueur(self):
        db_name = self._track_file("test_joueur_coded.db")
        self.generator.generate_coded_db_dimensionJoueur(db_name=db_name)
        self.assertTrue(os.path.exists(db_name))

    def test_generate_coded_db_dimensionTour(self):
        db_name = self._track_file("test_tour_coded.db")
        self.generator.generate_coded_db_dimensionTour(db_name=db_name)
        self.assertTrue(os.path.exists(db_name))

    def test_generate_coded_db_dimensionSerie(self):
        db_name = self._track_file("test_serie_coded.db")
        self.generator.generate_coded_db_dimensionSerie(db_name=db_name)
        self.assertTrue(os.path.exists(db_name))

    def test_generate_faitom3_from_dimensions(self):
        db_j = self._track_file("dim_j.db")
        db_t = self._track_file("dim_t.db")
        db_s = self._track_file("dim_s.db")
        db_f = self._track_file("fait_dim.db")
        
        self.generator.generate_coded_db_dimensionJoueur(db_name=db_j)
        self.generator.generate_coded_db_dimensionTour(db_name=db_t)
        self.generator.generate_coded_db_dimensionSerie(db_name=db_s)
        
        # We need to get the dicts first
        from scripts.databaseManagement.Converter import Converter
        dict_j = Converter(db_j).toDict()
        dict_t = Converter(db_t).toDict()
        dict_s = Converter(db_s).toDict()
        
        self.generator.generate_faitom3_from_dimensions(dict_j, dict_t, dict_s, db_name=db_f)
        self.assertTrue(os.path.exists(db_f))

    def test_generate_fact_table_faitom3(self):
        db_name = self._track_file("test_faitom3.db")
        self.generator.generate_fact_table_faitom3(db_name=db_name)
        self.assertTrue(os.path.exists(db_name))

    def test_generate_real_dbs(self):
        # Testing multiple 'real-ish' coded db generations
        f1 = self._track_file("real_j.db")
        f2 = self._track_file("real_t.db")
        f3 = self._track_file("real_s.db")
        
        self.generator.generate_random_coded_db_dimensionJoueur(nb_lignes=5, db_name=f1)
        self.generator.generate_random_coded_db_dimensionTour(nb_lignes=5, db_name=f2)
        self.generator.generate_random_coded_db_dimensionSerie(nb_series=1, db_name=f3)
        
        for f in [f1, f2, f3]:
            self.assertTrue(os.path.exists(f))

if __name__ == '__main__':
    unittest.main()
