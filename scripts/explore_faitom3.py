import sqlite3

db_path = "scripts/databaseManagement/faitom3WithDim.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

for table in tables:
    tname = table[0]
    cursor.execute(f"PRAGMA table_info({tname});")
    cols = cursor.fetchall()
    print(f"\nTable {tname} columns:")
    for col in cols:
        print(f"  - {col[1]} ({col[2]})")

    cursor.execute(f"SELECT * FROM {tname} LIMIT 10;")
    rows = cursor.fetchall()
    print(f"Table {tname} sample rows (first 10):")
    for r in rows:
        print("  ", r)

conn.close()
