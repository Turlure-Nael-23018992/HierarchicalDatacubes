import unittest
import os
import sys
import sqlite3
from unittest.mock import patch, MagicMock
import io

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Core.main import Main

class TestMainExtended(unittest.TestCase):
    def setUp(self):
        self.db_path = f"tmp_main_ext_{os.getpid()}.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Use columns that algorithms might expect
        c.execute("CREATE TABLE Pokemon (Geography TEXT, Time TEXT, Food TEXT, Val INTEGER)")
        c.execute("INSERT INTO Pokemon VALUES ('France', '2021', 'Fraise', 10)")
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def test_main_runs(self):
        main = Main(self.db_path, isPrinted=False)
        # Test BUC
        main.runBUC()
        # Test Star-Cubing
        main.runStarCubing()
        
    def test_main_hierarchical_runs_mocked(self):
        main = Main(self.db_path, isPrinted=False)
        
        # Patching inside Core.main to ensure it affects Main's imports
        with patch('Core.main.HierarchicalBUC'), \
             patch('Core.main.HierarchicalStarCubing'), \
             patch('Core.main.HierarchicalClosetCube'):
            
            main.runHierarchicalBUC()
            main.runHierarchicalStarCubing()
            main.runHierarchicalClosetCube()

    def test_prepare_data_3cols(self):
        db3 = f"tmp_main_3cols_{os.getpid()}.db"
        if os.path.exists(db3):
            os.remove(db3)
        conn = sqlite3.connect(db3)
        c = conn.cursor()
        c.execute("CREATE TABLE Pokemon (A TEXT, B TEXT, C TEXT)")
        c.execute("INSERT INTO Pokemon VALUES ('a1', 'b1', 'c1')")
        conn.commit()
        conn.close()
        
        main = Main(db3, isPrinted=False)
        # We need to mock dbGetter or ensure it works
        data, all_cols, dims, meas = main._prepare_data()
        self.assertEqual(meas, "COUNT")
        
        os.remove(db3)

if __name__ == '__main__':
    unittest.main()
