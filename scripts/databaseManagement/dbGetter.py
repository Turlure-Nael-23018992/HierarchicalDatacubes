import sqlite3

class dbGetter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def get_table_names(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in self.cursor.fetchall()]

    def get_column_names(self, table_name):
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        return [row[1] for row in self.cursor.fetchall()]

    def get_row_count(self, table_name):
        self.cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return self.cursor.fetchone()[0]

    def get_sample_row(self, table_name):
        self.cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
        return self.cursor.fetchone()

    def get_all_data(self, table_name):
        self.cursor.execute(f"SELECT * FROM {table_name};")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()