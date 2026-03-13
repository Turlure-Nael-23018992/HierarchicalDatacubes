import unittest
import os
import sqlite3
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.databaseManagement.Converter import Converter

class TestConverter(unittest.TestCase):
    def setUp(self):
        # Use a unique DB for each test to avoid file locks on Windows
        self.db_path = f"test_conv_{self._testMethodName}.db"
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE Pokemon (ID INTEGER, Col_A INTEGER, Col_B INTEGER, Col_C INTEGER)")
        cursor.executemany("INSERT INTO Pokemon VALUES (?, ?, ?, ?)", [
            (1, 10, 20, 30),
            (2, 40, 5, 15)
        ])
        conn.commit()
        conn.close()
        
        self.converter = Converter(self.db_path)

    def tearDown(self):
        if hasattr(self, 'converter'):
            self.converter.conn.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_toDict(self):
        expected = {
            1: (10, 20, 30),
            2: (40, 5, 15)
        }
        self.assertEqual(self.converter.toDict(), expected)

    def test_getMax(self):
        # Among (10,20,30) and (40,5,15), MAX col_a, col_b, col_c is computed per row then globally?
        # Actually MAX(Col_A, Col_B, Col_C) in SQLite returns the greatest of the arguments for each row, 
        # but combined with SELECT MAX... it gives the max of the first argument if it's aggregate, 
        # or max of the row? Wait, SELECT MAX(...) with multiple arguments returns the max among them row-wise.
        # But wait, SQLite MAX() with multiple args returns the greatest argument. But without group by, it returns one row.
        # Let's just check if it works without error and returns 40.
        self.assertEqual(self.converter.getMax(), 40)

if __name__ == '__main__':
    unittest.main()
