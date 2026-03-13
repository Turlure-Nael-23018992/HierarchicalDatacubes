import unittest
import os
import sqlite3
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from scripts.databaseManagement.dbGetter import dbGetter

class TestDBGetter(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_getter.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE TestTable (ID INTEGER, Name TEXT)")
        cursor.executemany("INSERT INTO TestTable VALUES (?, ?)", [(1, "A"), (2, "B")])
        conn.commit()
        conn.close()
        
        self.getter = dbGetter(self.db_path)

    def tearDown(self):
        self.getter.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_table_names(self):
        self.assertEqual(self.getter.get_table_names(), ["TestTable"])

    def test_get_column_names(self):
        self.assertEqual(self.getter.get_column_names("TestTable"), ["ID", "Name"])

    def test_get_row_count(self):
        self.assertEqual(self.getter.get_row_count("TestTable"), 2)

    def test_get_sample_row(self):
        self.assertEqual(self.getter.get_sample_row("TestTable"), (1, "A"))

    def test_get_all_data(self):
        self.assertEqual(self.getter.get_all_data("TestTable"), [(1, "A"), (2, "B")])

if __name__ == '__main__':
    unittest.main()
