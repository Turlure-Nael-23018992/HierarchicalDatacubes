"""
Dataset Generator for HierarchicalDatacubes
====================================================
Generates two types of SQLite databases compatible with the project:

1. FLAT DB  → for BUC, Star-Cubing, ClosetCube        (cosky_db format)
2. HIERARCHICAL DB → for H-BUC, H-StarCubing, H-ClosetCube (hierarchie_db format)

Supports two domain styles:
  - Banking
  - Medical

Usage:
    python generate_banking_datasets.py

Output files (place them in your DB/ folder):
    banking_flat_C3_R500.db
    banking_hierarchical_C3_R500.db
    medical_flat_C3_R500.db
    medical_hierarchical_C3_R500.db
"""

import argparse
import sqlite3
import random
import os

# ─────────────────────────────────────────────────────────────────────────────
# STATIC HIERARCHY — mirrors the structure expected by H-BUC / H-StarCubing
# Your project's STATIC_HIERARCHY must reference these exact values.
# Replace the one in your code or add this hierarchy alongside Geography/Time/Food.
# ─────────────────────────────────────────────────────────────────────────────

BANKING_HIERARCHY = {
    # ── Geography: Country → Region → City
    "Geography": {
        "ALL": ["France", "Germany", "Spain"],
        "France": ["Ile-de-France", "PACA", "Occitanie"],
        "Germany": ["Bavaria", "Berlin-Brandenburg"],
        "Spain": ["Catalonia", "Andalusia"],
        "Ile-de-France": ["Paris", "Versailles"],
        "PACA": ["Marseille", "Nice"],
        "Occitanie": ["Toulouse", "Montpellier"],
        "Bavaria": ["Munich", "Nuremberg"],
        "Berlin-Brandenburg": ["Berlin", "Potsdam"],
        "Catalonia": ["Barcelona", "Girona"],
        "Andalusia": ["Seville", "Malaga"],
    },

    # ── Time: Year → Quarter → Month
    "Time": {
        "ALL": ["2022", "2023", "2024"],
        "2022": ["2022-Q1", "2022-Q2", "2022-Q3", "2022-Q4"],
        "2023": ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4"],
        "2024": ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"],
        "2022-Q1": ["2022-01", "2022-02", "2022-03"],
        "2022-Q2": ["2022-04", "2022-05", "2022-06"],
        "2022-Q3": ["2022-07", "2022-08", "2022-09"],
        "2022-Q4": ["2022-10", "2022-11", "2022-12"],
        "2023-Q1": ["2023-01", "2023-02", "2023-03"],
        "2023-Q2": ["2023-04", "2023-05", "2023-06"],
        "2023-Q3": ["2023-07", "2023-08", "2023-09"],
        "2023-Q4": ["2023-10", "2023-11", "2023-12"],
        "2024-Q1": ["2024-01", "2024-02", "2024-03"],
        "2024-Q2": ["2024-04", "2024-05", "2024-06"],
        "2024-Q3": ["2024-07", "2024-08", "2024-09"],
        "2024-Q4": ["2024-10", "2024-11", "2024-12"],
    },

    # ── Product: Category → Type (replaces "Food" in your project)
    # IMPORTANT: rename "Food" column to "Product" in your DB, or keep "Food"
    # and map your banking product types to it — see note below.
    "Product": {
        "ALL": ["Loans", "Savings", "Investments"],
        "Loans": ["PersonalLoan", "MortgageLoan", "AutoLoan"],
        "Savings": ["CurrentAccount", "SavingsAccount", "TermDeposit"],
        "Investments": ["StockFund", "BondFund", "ETF"],
    },
}

# Leaf values (most specific level per dimension)
GEO_LEAVES = [
    "Paris", "Versailles", "Marseille", "Nice", "Toulouse", "Montpellier",
    "Munich", "Nuremberg", "Berlin", "Potsdam", "Barcelona", "Girona",
    "Seville", "Malaga",
]
TIME_LEAVES = [
    "2022-01", "2022-02", "2022-03", "2022-04", "2022-05", "2022-06",
    "2022-07", "2022-08", "2022-09", "2022-10", "2022-11", "2022-12",
    "2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06",
    "2023-07", "2023-08", "2023-09", "2023-10", "2023-11", "2023-12",
    "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06",
    "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
]
PRODUCT_LEAVES = [
    "PersonalLoan", "MortgageLoan", "AutoLoan",
    "CurrentAccount", "SavingsAccount", "TermDeposit",
    "StockFund", "BondFund", "ETF",
]

MEDICAL_HIERARCHY = {
    "Geography": {
        "ALL": ["France", "Germany", "Spain"],
        "France": ["Ile-de-France", "PACA", "Occitanie"],
        "Germany": ["Bavaria", "Berlin-Brandenburg"],
        "Spain": ["Catalonia", "Andalusia"],
        "Ile-de-France": ["Paris", "Versailles"],
        "PACA": ["Marseille", "Nice"],
        "Occitanie": ["Toulouse", "Montpellier"],
        "Bavaria": ["Munich", "Nuremberg"],
        "Berlin-Brandenburg": ["Berlin", "Potsdam"],
        "Catalonia": ["Barcelona", "Girona"],
        "Andalusia": ["Seville", "Malaga"],
    },
    "Time": {
        "ALL": ["2022", "2023", "2024"],
        "2022": ["2022-Q1", "2022-Q2", "2022-Q3", "2022-Q4"],
        "2023": ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4"],
        "2024": ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"],
        "2022-Q1": ["2022-01", "2022-02", "2022-03"],
        "2022-Q2": ["2022-04", "2022-05", "2022-06"],
        "2022-Q3": ["2022-07", "2022-08", "2022-09"],
        "2022-Q4": ["2022-10", "2022-11", "2022-12"],
        "2023-Q1": ["2023-01", "2023-02", "2023-03"],
        "2023-Q2": ["2023-04", "2023-05", "2023-06"],
        "2023-Q3": ["2023-07", "2023-08", "2023-09"],
        "2023-Q4": ["2023-10", "2023-11", "2023-12"],
        "2024-Q1": ["2024-01", "2024-02", "2024-03"],
        "2024-Q2": ["2024-04", "2024-05", "2024-06"],
        "2024-Q3": ["2024-07", "2024-08", "2024-09"],
        "2024-Q4": ["2024-10", "2024-11", "2024-12"],
    },
    "Service": {
        "ALL": ["Consultation", "Imaging", "Therapy"],
        "Consultation": ["GeneralPractice", "Specialist", "Telehealth"],
        "Imaging": ["XRay", "MRI", "CTScan"],
        "Therapy": ["Physiotherapy", "Radiation", "Chemotherapy"],
    },
}

MEDICAL_GEO_LEAVES = [
    "Paris", "Versailles", "Marseille", "Nice", "Toulouse", "Montpellier",
    "Munich", "Nuremberg", "Berlin", "Potsdam", "Barcelona", "Girona",
    "Seville", "Malaga",
]
MEDICAL_TIME_LEAVES = [
    "2022-01", "2022-02", "2022-03", "2022-04", "2022-05", "2022-06",
    "2022-07", "2022-08", "2022-09", "2022-10", "2022-11", "2022-12",
    "2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06",
    "2023-07", "2023-08", "2023-09", "2023-10", "2023-11", "2023-12",
    "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06",
    "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
]
MEDICAL_SERVICE_LEAVES = [
    "GeneralPractice", "Specialist", "Telehealth",
    "XRay", "MRI", "CTScan",
    "Physiotherapy", "Radiation", "Chemotherapy",
]


# ─────────────────────────────────────────────────────────────────────────────
# 1. FLAT DATABASE  (cosky_db style)
#    Columns: Dim1, Dim2, Dim3, COUNT
#    Values are integers — same as your existing cosky_db_*.db files.
#    Compatible with: BUC, Star-Cubing, ClosetCube
# ─────────────────────────────────────────────────────────────────────────────

def generate_flat_banking_db(nb_rows: int = 5, nb_cols: int = 3,
                              output_path: str = "banking_flat_C3_R5.db"):
    """
    Generates a flat SQLite DB with integer-encoded dimensions.

    Schema: Pokemon(Dim1 INT, Dim2 INT, Dim3 INT, COUNT INT)
    (Table named 'Pokemon' to match your project's expectations)

    Encoding:
        Dim1 (Geography): 1–14  (14 cities)
        Dim2 (Time):      1–36  (36 months)
        Dim3 (Product):   1–9   (9 product types)
        COUNT:            random transaction count (1–200)
    """
    conn = sqlite3.connect(output_path)
    cur = conn.cursor()

    dim_cols = ", ".join([f"Dim{i+1} INT" for i in range(nb_cols)])
    cur.execute(f"DROP TABLE IF EXISTS Pokemon")
    cur.execute(f"CREATE TABLE Pokemon ({dim_cols}, COUNT INT)")

    rows = []
    for _ in range(nb_rows):
        dims = [
            random.randint(1, 14),   # Geography (city index)
            random.randint(1, 36),   # Time (month index)
            random.randint(1, 9),    # Product (product index)
        ]
        count = random.randint(1, 200)
        rows.append(tuple(dims + [count]))

    cur.executemany(
        f"INSERT INTO Pokemon VALUES ({', '.join(['?' for _ in range(nb_cols + 1)])})",
        rows
    )
    conn.commit()
    conn.close()
    print(f"✅ Flat DB created: {output_path}  ({nb_rows} rows, {nb_cols} dims)")
    return output_path


def generate_flat_medical_db(nb_rows: int = 5, nb_cols: int = 3,
                             output_path: str = "medical_flat_C3_R5.db"):
    """
    Generates a flat SQLite DB with integer-encoded dimensions for medical data.

    Schema: Pokemon(Dim1 INT, Dim2 INT, Dim3 INT, COUNT INT)
    (Table named 'Pokemon' to match your project's expectations)

    Encoding:
        Dim1 (Geography): 1–14  (14 cities)
        Dim2 (Time):      1–36  (36 months)
        Dim3 (Service):   1–9   (9 medical service types)
        COUNT:            random patient count / encounters (1–200)
    """
    conn = sqlite3.connect(output_path)
    cur = conn.cursor()

    dim_cols = ", ".join([f"Dim{i+1} INT" for i in range(nb_cols)])
    cur.execute(f"DROP TABLE IF EXISTS Pokemon")
    cur.execute(f"CREATE TABLE Pokemon ({dim_cols}, COUNT INT)")

    rows = []
    for _ in range(nb_rows):
        dims = [
            random.randint(1, 14),   # Geography (city index)
            random.randint(1, 36),   # Time (month index)
            random.randint(1, 9),    # Service (service index)
        ]
        count = random.randint(1, 200)
        rows.append(tuple(dims + [count]))

    cur.executemany(
        f"INSERT INTO Pokemon VALUES ({', '.join(['?' for _ in range(nb_cols + 1)])})",
        rows
    )
    conn.commit()
    conn.close()
    print(f"✅ Flat DB created: {output_path}  ({nb_rows} rows, {nb_cols} dims)")
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# 2. HIERARCHICAL DATABASE  (hierarchie_db style)
#    Columns: Geography, Time, Product, COUNT
#    Values are leaf strings from the hierarchy above.
#    Compatible with: H-BUC, H-StarCubing, H-ClosetCube
#
#    ⚠️  IMPORTANT: Your project currently uses "Food" as the third column.
#    Two options:
#      A) Keep column name "Food" and map your product leaves to Food hierarchy
#         → rename PRODUCT_LEAVES to match your Food hierarchy values.
#      B) Rename the column to "Product" and add BANKING_HIERARCHY["Product"]
#         to your STATIC_HIERARCHY in HierarchicalBUC.py / HierarchicalStarCubing.py
#    Option B is recommended for clarity.
# ─────────────────────────────────────────────────────────────────────────────

def generate_hierarchical_banking_db(nb_rows: int = 500,
                                     output_path: str = "banking_hierarchical_C3_R500.db",
                                     use_food_column: bool = False):
    """
    Generates a hierarchical SQLite DB with string leaf values.

    Schema: Pokemon(Geography TEXT, Time TEXT, Product TEXT, COUNT INT)
    (or Food instead of Product if use_food_column=True)

    Set use_food_column=True if you do NOT want to modify STATIC_HIERARCHY
    in your project code — in that case the values will be mapped to
    food-compatible placeholders.
    """
    third_col = "Food" if use_food_column else "Product"

    conn = sqlite3.connect(output_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS Pokemon")
    cur.execute(f"""
        CREATE TABLE Pokemon (
            Geography TEXT,
            Time      TEXT,
            {third_col} TEXT,
            COUNT     INT
        )
    """)

    rows = []
    for _ in range(nb_rows):
        geo   = random.choice(GEO_LEAVES)
        time  = random.choice(TIME_LEAVES)
        prod  = random.choice(PRODUCT_LEAVES)
        count = random.randint(1, 500)
        rows.append((geo, time, prod, count))

    cur.executemany(
        f"INSERT INTO Pokemon VALUES (?, ?, ?, ?)",
        rows
    )
    conn.commit()
    conn.close()
    print(f"✅ Hierarchical DB created: {output_path}  ({nb_rows} rows)")
    return output_path


def generate_hierarchical_medical_db(nb_rows: int = 500,
                                    output_path: str = "medical_hierarchical_C3_R500.db",
                                    use_food_column: bool = False):
    """
    Generates a hierarchical SQLite DB with string leaf values for medical data.

    Schema: Pokemon(Geography TEXT, Time TEXT, Service TEXT, COUNT INT)
    (or Food instead of Service if use_food_column=True)
    """
    third_col = "Food" if use_food_column else "Service"

    conn = sqlite3.connect(output_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS Pokemon")
    cur.execute(f"""
        CREATE TABLE Pokemon (
            Geography TEXT,
            Time      TEXT,
            {third_col} TEXT,
            COUNT     INT
        )
    """)

    rows = []
    for _ in range(nb_rows):
        geo   = random.choice(MEDICAL_GEO_LEAVES)
        time  = random.choice(MEDICAL_TIME_LEAVES)
        service = random.choice(MEDICAL_SERVICE_LEAVES)
        count = random.randint(1, 500)
        rows.append((geo, time, service, count))

    cur.executemany(
        f"INSERT INTO Pokemon VALUES (?, ?, ?, ?)",
        rows
    )
    conn.commit()
    conn.close()
    print(f"✅ Hierarchical DB created: {output_path}  ({nb_rows} rows)")
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# 3. STATIC_HIERARCHY SNIPPET
#    Copy-paste this into your project to replace (or extend) the existing
#    STATIC_HIERARCHY dict in HierarchicalBUC.py and HierarchicalStarCubing.py
# ─────────────────────────────────────────────────────────────────────────────

STATIC_HIERARCHY_SNIPPET = '''
# ── Add this to your STATIC_HIERARCHY in HierarchicalBUC.py / HierarchicalStarCubing.py ──

STATIC_HIERARCHY = {
    "Geography": {
        "ALL": ["France", "Germany", "Spain"],
        "France": ["Ile-de-France", "PACA", "Occitanie"],
        "Germany": ["Bavaria", "Berlin-Brandenburg"],
        "Spain": ["Catalonia", "Andalusia"],
        "Ile-de-France": ["Paris", "Versailles"],
        "PACA": ["Marseille", "Nice"],
        "Occitanie": ["Toulouse", "Montpellier"],
        "Bavaria": ["Munich", "Nuremberg"],
        "Berlin-Brandenburg": ["Berlin", "Potsdam"],
        "Catalonia": ["Barcelona", "Girona"],
        "Andalusia": ["Seville", "Malaga"],
    },
    "Time": {
        "ALL": ["2022", "2023", "2024"],
        "2022": ["2022-Q1", "2022-Q2", "2022-Q3", "2022-Q4"],
        "2023": ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4"],
        "2024": ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"],
        "2022-Q1": ["2022-01", "2022-02", "2022-03"],
        "2022-Q2": ["2022-04", "2022-05", "2022-06"],
        "2022-Q3": ["2022-07", "2022-08", "2022-09"],
        "2022-Q4": ["2022-10", "2022-11", "2022-12"],
        "2023-Q1": ["2023-01", "2023-02", "2023-03"],
        "2023-Q2": ["2023-04", "2023-05", "2023-06"],
        "2023-Q3": ["2023-07", "2023-08", "2023-09"],
        "2023-Q4": ["2023-10", "2023-11", "2023-12"],
        "2024-Q1": ["2024-01", "2024-02", "2024-03"],
        "2024-Q2": ["2024-04", "2024-05", "2024-06"],
        "2024-Q3": ["2024-07", "2024-08", "2024-09"],
        "2024-Q4": ["2024-10", "2024-11", "2024-12"],
    },
    "Product": {
        "ALL": ["Loans", "Savings", "Investments"],
        "Loans": ["PersonalLoan", "MortgageLoan", "AutoLoan"],
        "Savings": ["CurrentAccount", "SavingsAccount", "TermDeposit"],
        "Investments": ["StockFund", "BondFund", "ETF"],
    },
}
'''


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate sample banking or medical SQLite datasets for HierarchicalDatacubes."
    )
    parser.add_argument("--domain", choices=["banking", "medical", "both"], default="banking",
                        help="Type of sample data to generate.")
    parser.add_argument("--rows", type=int, default=5,
                        help="Number of rows per generated DB.")
    parser.add_argument("--flat", action="store_true",
                        help="Generate flat dataset(s) only.")
    parser.add_argument("--hierarchical", action="store_true",
                        help="Generate hierarchical dataset(s) only.")
    parser.add_argument("--food-column", action="store_true",
                        help="Use Food as the third column name instead of Product/Service.")
    parser.add_argument("--output-dir", default="DB",
                        help="Output folder for generated DB files.")
    args = parser.parse_args()

    if not args.flat and not args.hierarchical:
        args.flat = args.hierarchical = True

    os.makedirs(args.output_dir, exist_ok=True)

    domains = [args.domain] if args.domain != "both" else ["banking", "medical"]
    for domain in domains:
        if args.flat:
            if domain == "banking":
                generate_flat_banking_db(
                    nb_rows=args.rows,
                    nb_cols=3,
                    output_path=os.path.join(args.output_dir, f"banking_flat_C3_R{args.rows}.db")
                )
            else:
                generate_flat_medical_db(
                    nb_rows=args.rows,
                    nb_cols=3,
                    output_path=os.path.join(args.output_dir, f"medical_flat_C3_R{args.rows}.db")
                )

        if args.hierarchical:
            if domain == "banking":
                generate_hierarchical_banking_db(
                    nb_rows=args.rows,
                    output_path=os.path.join(args.output_dir, f"banking_hierarchical_C3_R{args.rows}.db"),
                    use_food_column=args.food_column
                )
            else:
                generate_hierarchical_medical_db(
                    nb_rows=args.rows,
                    output_path=os.path.join(args.output_dir, f"medical_hierarchical_C3_R{args.rows}.db"),
                    use_food_column=args.food_column
                )

    print("" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("""
1. Copy the generated .db files into your project's DB/ folder.

2. Update STATIC_HIERARCHY in your code:
   → scripts/Algorithms/HierarchicalBUC.py
   → scripts/Algorithms/HierarchicalStarCubing.py
   → scripts/Algorithms/HierarchicalClosetCube.py
   Replace (or extend) the existing STATIC_HIERARCHY with the
   snippet printed in STATIC_HIERARCHY_SNIPPET in this file.

3. If you keep the column name "Food" (no code change), use --food-column
   and map Product/Service leaves to Food values.

4. Use flat DBs with:
       BUC(db_path="DB/banking_flat_C3_R500.db", iceberg_threshold=5)

5. Use hierarchical DBs with:
       hbuc = HierarchicalBUC()
       hbuc.run_buc_from_simple_hierarchical_db(
           "DB/banking_hierarchical_C3_R500.db",
           table_name="Pokemon",
           isPrinted=True
       )
""")
    print("STATIC_HIERARCHY to add to your code:")
    print(STATIC_HIERARCHY_SNIPPET)
