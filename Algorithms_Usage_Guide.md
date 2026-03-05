# Algorithms Usage Guide: Hierarchical Datacubes

This guide explains how to use each algorithm in the project, including initialization, execution, and common pitfalls.

---

## Data Format Requirements

Most algorithms expect data in one of these formats:
- **List of lists**: `[[val1, val2, measure], ...]`
- **Dictionary**: `{1: (val1, val2, measure), ...}` (often converted from DB via `Converter`)
- **Pandas DataFrame**: Used primarily by `BUC` and `bruteForce`.

---

## 1. BUC (Bottom-Up Cubing)
- **File**: `BUC.py`
- **Use Case**: Flat dimensions, small to medium datasets.

```python
from scripts.Algorithms.BUC import BUC

# Initialization
# db_path: Path to .sqlite file
# iceberg_threshold: Minimum measure value to keep
buc = BUC(db_path="path/to/db.db", iceberg_threshold=10)

# Execution
# returns: (None, execution_time)
_, time_spent = buc.run(isPrinted=True)
```

---

## 2. Hierarchical BUC (H-BUC)
- **File**: `HierarchicalBUC.py`
- **Use Case**: Data with hierarchies (e.g., City -> Region).

### From Database
```python
from scripts.Algorithms.HierarchicalBUC import HierarchicalBUC

hbuc = HierarchicalBUC()
hbuc.run_buc_from_simple_hierarchical_db("path/to/db.db", table_name="Pokemon", isPrinted=True)
```

### From Dictionary (Advanced)
```python
# _run_flat_buc(data_dict, dimensions, aggregation, hierarchy, isPrinted=True)
# WARNING: Your 'aggregation' keys MUST exist in the 'dimensions' list.
hbuc._run_flat_buc(data_dict, ["Dim1", "Dim2", "Measure"], {"Measure": "SUM"}, hierarchy)
```

---

## 3. Star-Cubing
- **File**: `starCubing.py`

```python
from scripts.Algorithms.starCubing import StarCubing

# data: List of tuples/lists
# dimensions: All column names (last one is measure)
sc = StarCubing(data, ["Dim1", "Dim2", "Sales"], iceberg_threshold=5)

# run(aggregation={"Sales": "SUM"})
sc.run(isPrinted=True, aggregation={"Sales": "SUM"})
```

---

## 4. Hierarchical Star-Cubing
- **File**: `HierarchicalStarCubing.py`

```python
from scripts.Algorithms.HierarchicalStarCubing import HierarchicalStarCubing

hsc = HierarchicalStarCubing(data_dict, columnNames, {"Sales": "SUM"}, hierarchy)
hsc.run_star_cubing_with_hierarchy(isPrinted=True)
```

---

## 5. ClosetCube & Hierarchical ClosetCube
- **Files**: `closetCube.py`, `HierarchicalClosetCube.py`
- **Goal**: Generate only *closed* cuboids to reduce size.

```python
from scripts.Algorithms.closetCube import ClosetCube

cc = ClosetCube(data, ["Dim1", "Dim2", "Count"], iceberg_threshold=10)
cc.generate_cube(aggregation={"Count": "SUM"}, verbose=True)
```

---

## 6. Brute Force
- **File**: `bruteForce.py`

```python
from scripts.Algorithms.bruteForce import bruteForce
import pandas as pd

df = pd.read_csv("data.csv")
bruteForce(df) # Logic is semi-hardcoded for 'ventes' measure
```

---

## 📂 Understanding Hierarchical Data (DBs)

Hierarchical algorithms (H-BUC, H-StarCubing) require data that follows a specific logical structure.

### 1. The Hierarchy Mapping (Python)
Before processing data, the algorithms refer to a `STATIC_HIERARCHY` (often hardcoded in the class). This tells the system how to "roll up" values.

**Example Logic:**
- `Europe` → `France` → `Paris`
- `2023` → `2023-01` → `2023-01-01`

### 2. The Database Table Format
The algorithms expect a **denormalized (flat) table**. This means each row contains the most specific level of detail for each dimension.

#### ✅ GOOD Example (Valid hierarchical DB)
The columns match the hierarchy names, and values are recognized leaf nodes.

| Geography | Time | Food | COUNT |
| :--- | :--- | :--- | :--- |
| Paris | 2023-01-01 | Fraise | 10 |
| Marseille | 2023-01-01 | Boeuf | 5 |

**Why it's good:**
- **Recognition**: `Paris` is known to be in `France` (Geography).
- **Hierarchy alignment**: The algorithm knows it can calculate a total for `France` by summing `Paris` and `Marseille`.

#### ❌ BAD Example (Invalid/Incompatible)
| City | Date | Product | Sales |
| :--- | :--- | :--- | :--- |
| New York | 2023-01-01 | Pizza | 100 |

**Why it's bad:**
- **Naming mismatch**: The algorithm looks for `Geography`, not `City`.
- **Unknown values**: If `New York` is not in the `STATIC_HIERARCHY`, the algorithm doesn't know its parent region. It cannot aggregate it to a higher level.
- **Missing references**: `Pizza` might not be mapped to `Céréales` or `Légumes`.

### 3. Key Rules for Success
1. **Column Names**: Your DB headers must match the names used in the code (e.g., `Geography`, `Time`, `Food`).
2. **Value Inclusion**: Every value in your DB should ideally be a "child" in the hierarchy map.
3. **Measure Presence**: Ensure you have a numerical column for the calculation (Sum, Avg).
4. **Denormalization**: Do NOT use separate tables for levels. Use ONE table where each row is a complete "point" in the cube.

---

## 🗄️ Database Selection & Generation

Choosing the right database depends on whether your algorithm is "Flat" or "Hierarchical".

### 1. Mapping: Which DB for which Algorithm?

| Algorithm | Recommended Database | Logic Type |
| :--- | :--- | :--- |
| **BUC** / **Star-Cubing** | `cosky_db_*.db` | Flat (No hierarchy) |
| **Hierarchical BUC** | `Pokemon_fact_table.db` (or `hierarchie_db_*.db`) | Hierarchical |
| **Hierarchical Star-Cubing** | `hierarchie_db_*.db` (Geography/Time/Food) | Hierarchical |
| **ClosetCube** | `cosky_db_*.db` | Flat (Closed) |
| **Hierarchical ClosetCube**| `hierarchie_db_*.db` | Hierarchical (Closed) |

### 2. How to Generate These Databases

You can generate all necessary data using the `DataGenerator` class in `scripts/databaseManagement/DataGenerator.py`.

#### A. Generate a Generic Flat DB (for BUC/Star-Cubing)
```python
from scripts.databaseManagement.DataGenerator import DataGenerator

dg = DataGenerator()
# nb_lignes: 100, nb_colonnes: 3
dg.generate_db_hierarchy(100, 3) 
# Result: aurelien_db_C3_R100.db (Table: Pokemon)
```

#### B. Generate a Hierarchical DB (for H-BUC/H-Star)
These databases contain values that match the `Geography`, `Time`, and `Food` hierarchies defined in the code.
```python
from scripts.databaseManagement.DataGenerator import DataGenerator

dg = DataGenerator()
dg.generate_hierarchical_facts_db(1000)
# Result: hierarchie_db_C3_R1000.db (Table: Pokemon)
```

#### C. Generate the Pokémon Fact Table
```python
from scripts.databaseManagement.DataGenerator import DataGenerator

dg = DataGenerator()
dg.generatePokemonFactTable(isDetailed=True)
# Result: Pokemon_fact_table.db (Table: Pokemon)
```

### 3. Quick Reference: Where are the DBs?
- Pre-generated DBs are in the `DB/` folder.
- New DBs generated by scripts are usually created in `scripts/databaseManagement/` or the root, depending on where you run the script.

---

## 🛠 Troubleshooting: Common Errors
### `IndexError: tuple index out of range`
**Cause**: This usually happens when the number of columns in your `data` doesn't match the `dimensions` list passed to the algorithm.
**Fix**: Ensure `len(row) == len(dimensions)` for every row.

### `KeyError: "[...] not in index"`
**Cause**: The algorithm is looking for specific column names (like 'Geography') that are missing from your DB.
**Fix**: Rename your columns in the DB or ensure you are using a DB created specifically for hierarchical algorithms (like `hierarchie_db`).

