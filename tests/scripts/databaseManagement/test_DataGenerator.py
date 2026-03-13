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

if __name__ == '__main__':
    unittest.main()
