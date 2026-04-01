"""
Unit tests for HierarchicalCompleteCube.

Test strategies:
  1. Micro-dataset with manually computed expected values
  2. Cross-validation with HierarchicalLevelUpCube (real DB)
  3. Internal consistency: parent = sum(children), ALL = sum(roots)
  4. Brute-force reference comparison (independent implementation)
"""

import sys
import os
import unittest
from collections import defaultdict
from itertools import product as iterproduct

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.Algorithms.HierarchicalCompleteCube import HierarchicalCompleteCube
from scripts.Algorithms.HierarchicalLevelUpCube import HierarchicalLevelUpCube


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def results_to_map(results):
    """Convert list of (d1, d2, ..., measure) tuples to dict {dims: measure}."""
    return {tuple(r[:-1]): r[-1] for r in results}


ALL = "ALL"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_micro_data():
    """4-row micro-dataset with a single time leaf."""
    time_leaf = "2023-01-01"
    columns = ["id", "Geography", "Time", "Food", "COUNT"]
    data = [
        (0, "Paris",     time_leaf, "Fraise",  1.0),
        (1, "Paris",     time_leaf, "Orange",  1.0),
        (2, "Nanterre",  time_leaf, "Fraise",  1.0),
        (3, "Marseille", time_leaf, "Orange",  1.0),
    ]
    return data, columns, time_leaf


def _make_extended_data():
    """7-row dataset for consistency checks."""
    time_leaf = "2023-01-01"
    columns = ["id", "Geography", "Time", "Food", "COUNT"]
    data = [
        (0, "Paris",     time_leaf, "Fraise",    1.0),
        (1, "Paris",     time_leaf, "Orange",    1.0),
        (2, "Nanterre",  time_leaf, "Fraise",    1.0),
        (3, "Marseille", time_leaf, "Orange",    1.0),
        (4, "Nice",      time_leaf, "Fraise",    1.0),
        (5, "Munich",    time_leaf, "Citron",    1.0),
        (6, "Barcelone", time_leaf, "Framboise", 1.0),
    ]
    return data, columns, time_leaf


def _make_bruteforce_data():
    """6-row dataset for brute-force comparison."""
    time_leaf = "2023-01-01"
    columns = ["id", "Geography", "Time", "Food", "COUNT"]
    data = [
        (0, "Paris",     time_leaf, "Fraise", 1.0),
        (1, "Paris",     time_leaf, "Orange", 1.0),
        (2, "Nanterre",  time_leaf, "Fraise", 1.0),
        (3, "Marseille", time_leaf, "Orange", 1.0),
        (4, "Nice",      time_leaf, "Fraise", 1.0),
        (5, "Munich",    time_leaf, "Citron", 1.0),
    ]
    return data, columns, time_leaf


def _build_inv_maps(hierarchy, dim_names):
    """Build child->parent maps for each dimension."""
    inv_maps = {}
    for dim_name in dim_names:
        inv_maps[dim_name] = {
            v: k
            for k, vs in hierarchy.get(dim_name, {}).items()
            for v in vs
        }
    return inv_maps


def _get_all_ancestors(val, dim_name, inv_maps):
    """Return [val, parent, grandparent, ..., root]."""
    result = [val]
    inv = inv_maps.get(dim_name, {})
    current = val
    while current in inv:
        current = inv[current]
        result.append(current)
    return result


# ===========================================================================
# TEST 1 -- Micro-dataset with known expected values
# ===========================================================================

class TestMicroDataset(unittest.TestCase):
    """Verify HCC output against hand-calculated values on a tiny dataset."""

    @classmethod
    def setUpClass(cls):
        data, columns, cls.time_leaf = _make_micro_data()
        hcc = HierarchicalCompleteCube(data, columns, skip_first_col=True)
        results = hcc.generate_cube()
        cls.cube = results_to_map(results)
        cls.t = cls.time_leaf

    # -- Leaf cells ----------------------------------------------------------

    def test_leaf_paris_fraise(self):
        self.assertEqual(self.cube[("Paris", self.t, "Fraise")], 1.0)

    def test_leaf_paris_orange(self):
        self.assertEqual(self.cube[("Paris", self.t, "Orange")], 1.0)

    def test_leaf_nanterre_fraise(self):
        self.assertEqual(self.cube[("Nanterre", self.t, "Fraise")], 1.0)

    def test_leaf_marseille_orange(self):
        self.assertEqual(self.cube[("Marseille", self.t, "Orange")], 1.0)

    # -- Geography roll-ups --------------------------------------------------

    def test_geo_idf_fraise(self):
        """Île-de-France = Paris + Nanterre for Fraise."""
        self.assertEqual(self.cube[("Île-de-France", self.t, "Fraise")], 2.0)

    def test_geo_idf_orange(self):
        """Île-de-France = Paris only for Orange."""
        self.assertEqual(self.cube[("Île-de-France", self.t, "Orange")], 1.0)

    def test_geo_paca_orange(self):
        self.assertEqual(self.cube[("PACA", self.t, "Orange")], 1.0)

    def test_geo_france_fraise(self):
        """France = IDF(2) for Fraise (PACA has none)."""
        self.assertEqual(self.cube[("France", self.t, "Fraise")], 2.0)

    def test_geo_france_orange(self):
        """France = IDF(1) + PACA(1) for Orange."""
        self.assertEqual(self.cube[("France", self.t, "Orange")], 2.0)

    def test_geo_europe_fraise(self):
        self.assertEqual(self.cube[("Europe", self.t, "Fraise")], 2.0)

    def test_geo_europe_orange(self):
        self.assertEqual(self.cube[("Europe", self.t, "Orange")], 2.0)

    # -- Food roll-ups -------------------------------------------------------

    def test_food_paris_fruits_rouges(self):
        self.assertEqual(self.cube[("Paris", self.t, "Fruits rouges")], 1.0)

    def test_food_paris_agrumes(self):
        self.assertEqual(self.cube[("Paris", self.t, "Agrumes")], 1.0)

    def test_food_paris_fruits(self):
        """Paris/Fruits = Fraise(1) + Orange(1) = 2."""
        self.assertEqual(self.cube[("Paris", self.t, "Fruits")], 2.0)

    # -- Combined roll-ups ---------------------------------------------------

    def test_combined_europe_fruits(self):
        """Europe/Fruits = all 4 rows."""
        self.assertEqual(self.cube[("Europe", self.t, "Fruits")], 4.0)

    def test_combined_france_fruits(self):
        self.assertEqual(self.cube[("France", self.t, "Fruits")], 4.0)

    def test_combined_idf_fruits(self):
        """IDF/Fruits = Paris(2) + Nanterre(1) = 3."""
        self.assertEqual(self.cube[("Île-de-France", self.t, "Fruits")], 3.0)

    # -- ALL projections -----------------------------------------------------

    def test_all_geo_fraise(self):
        self.assertEqual(self.cube[(ALL, self.t, "Fraise")], 2.0)

    def test_all_geo_orange(self):
        self.assertEqual(self.cube[(ALL, self.t, "Orange")], 2.0)

    def test_all_geo_fruits(self):
        self.assertEqual(self.cube[(ALL, self.t, "Fruits")], 4.0)

    def test_europe_all_time_fraise(self):
        self.assertEqual(self.cube[("Europe", ALL, "Fraise")], 2.0)

    def test_all_all_all(self):
        """Grand total = 4 rows."""
        self.assertEqual(self.cube[(ALL, ALL, ALL)], 4.0)

    # -- Time roll-ups -------------------------------------------------------

    def test_time_rollup_month(self):
        """2023-01-01 -> 2023-01."""
        self.assertEqual(self.cube[("Paris", "2023-01", "Fraise")], 1.0)

    def test_time_rollup_year(self):
        """2023-01-01 -> 2023-01 -> 2023."""
        self.assertEqual(self.cube[("Paris", "2023", "Fraise")], 1.0)

    def test_time_rollup_combined(self):
        self.assertEqual(self.cube[("Europe", "2023", "Fruits")], 4.0)


# ===========================================================================
# TEST 2 -- Cross-validation with HierarchicalLevelUpCube (real DB)
# ===========================================================================

class TestCrossValidation(unittest.TestCase):
    """
    Every cell from LevelUpCube (closed cube) must exist in HCC with the
    same value, since the complete cube is a superset of the closed cube.
    """

    @classmethod
    def setUpClass(cls):
        db_dir = os.path.join(project_root, "DB")
        cls.skip = False
        if not os.path.isdir(db_dir):
            cls.skip = True
            return

        dbs = [f for f in os.listdir(db_dir)
               if f.endswith(".db") and "hierarchie" in f]
        if not dbs:
            cls.skip = True
            return

        db_path = os.path.join(db_dir, dbs[0])
        cls.db_name = dbs[0]

        from scripts.databaseManagement.dbGetter import dbGetter
        dbGet = dbGetter(db_path)
        tableName = dbGet.get_table_names()[0]
        allColumns = dbGet.get_column_names(tableName)
        raw_data = dbGet.get_all_data(tableName)
        dbGet.close()

        has_measure = len(allColumns) > 3
        if not has_measure:
            columns = allColumns + ["COUNT"]
            data = [row + (1.0,) for row in raw_data]
        else:
            columns = allColumns
            data = raw_data

        hcc = HierarchicalCompleteCube(data, columns, skip_first_col=False)
        cls.hcc_map = results_to_map(hcc.generate_cube())

        luc = HierarchicalLevelUpCube(data, columns, skip_first_col=False)
        cls.luc_map = results_to_map(luc.generate_closed_cube())

    def setUp(self):
        if self.skip:
            self.skipTest("No hierarchical DB found in DB/")

    def test_all_closed_cells_present_in_hcc(self):
        """Every LevelUpCube cell must exist in HCC."""
        missing = [k for k in self.luc_map if k not in self.hcc_map]
        self.assertEqual(len(missing), 0,
                         f"{len(missing)} closed cells missing from HCC: "
                         f"{missing[:5]}")

    def test_all_closed_cells_values_match(self):
        """Values of common cells must match."""
        mismatches = {
            k: (self.hcc_map[k], v)
            for k, v in self.luc_map.items()
            if k in self.hcc_map and abs(self.hcc_map[k] - v) > 0.001
        }
        self.assertEqual(len(mismatches), 0,
                         f"{len(mismatches)} value mismatches: "
                         f"{dict(list(mismatches.items())[:5])}")

    def test_hcc_superset_of_closed(self):
        """HCC (non-ALL cells) must be a superset of closed cube."""
        hcc_non_all = {k for k in self.hcc_map if ALL not in k}
        self.assertTrue(hcc_non_all >= set(self.luc_map.keys()))

    def test_hcc_has_more_cells(self):
        """Full cube should be strictly larger than the closed cube."""
        self.assertGreater(len(self.hcc_map), len(self.luc_map))


# ===========================================================================
# TEST 3 -- Internal consistency: parent = sum(children)
# ===========================================================================

class TestInternalConsistency(unittest.TestCase):
    """Verify hierarchical aggregation integrity."""

    @classmethod
    def setUpClass(cls):
        data, columns, cls.time_leaf = _make_extended_data()
        cls.hcc = HierarchicalCompleteCube(data, columns, skip_first_col=True)
        results = cls.hcc.generate_cube()
        cls.cube = results_to_map(results)
        cls.n_rows = len(data)

    def test_parent_equals_sum_of_children(self):
        """For every parent in the hierarchy, value = sum(children values)."""
        cube = self.cube
        hierarchy = self.hcc.hierarchy
        dim_cols = self.hcc.dim_cols

        errors = []
        for dim_idx, dim_name in enumerate(dim_cols):
            dim_hier = hierarchy.get(dim_name, {})
            for parent, children in dim_hier.items():
                parent_keys = [k for k in cube
                               if k[dim_idx] == parent and ALL not in k]
                for pk in parent_keys:
                    child_sum = sum(
                        cube[pk[:dim_idx] + (c,) + pk[dim_idx + 1:]]
                        for c in children
                        if pk[:dim_idx] + (c,) + pk[dim_idx + 1:] in cube
                    )
                    child_count = sum(
                        1 for c in children
                        if pk[:dim_idx] + (c,) + pk[dim_idx + 1:] in cube
                    )
                    if child_count > 0 and abs(cube[pk] - child_sum) > 0.001:
                        errors.append(
                            f"{dim_name}: {parent} at {pk}: "
                            f"parent={cube[pk]}, sum(children)={child_sum}"
                        )

        self.assertEqual(len(errors), 0,
                         f"{len(errors)} parent/children mismatches:\n" +
                         "\n".join(errors[:10]))

    def test_all_geo_equals_sum_of_roots(self):
        """(ALL, T, F) must equal sum of root Geography values for (T, F)."""
        cube = self.cube
        inv_map = self.hcc._inv_maps.get("Geography", {})

        # Root geo values = present in cube but have no parent
        geo_roots = {k[0] for k in cube
                     if ALL not in k and k[0] not in inv_map}

        errors = []
        time_food_keys = {(k[1], k[2]) for k in cube if ALL not in k}
        for t, f in time_food_keys:
            expected = sum(cube.get((g, t, f), 0) for g in geo_roots)
            actual = cube.get((ALL, t, f), 0)
            if expected > 0 and abs(actual - expected) > 0.001:
                errors.append(f"(ALL, {t}, {f}): expected={expected}, got={actual}")

        self.assertEqual(len(errors), 0,
                         f"ALL projection errors:\n" + "\n".join(errors[:10]))

    def test_grand_total(self):
        """(ALL, ALL, ALL) must equal total number of rows."""
        self.assertAlmostEqual(
            self.cube[(ALL, ALL, ALL)], self.n_rows, places=3
        )


# ===========================================================================
# TEST 4 -- Brute-force reference comparison
# ===========================================================================

class TestBruteForceReference(unittest.TestCase):
    """
    Independent brute-force implementation: for each row, for each subset
    of dimensions to collapse to ALL, cross-product the ancestor chains of
    kept dimensions with ALL for collapsed dimensions.
    Compare cell-by-cell with HCC.
    """

    @classmethod
    def setUpClass(cls):
        data, columns, _ = _make_bruteforce_data()
        dim_names = ["Geography", "Time", "Food"]
        hierarchy = HierarchicalCompleteCube.STATIC_HIERARCHY
        inv_maps = _build_inv_maps(hierarchy, dim_names)

        # -- Brute-force cube --
        bf_cube = defaultdict(float)
        for row in data:
            dims = [row[1], row[2], row[3]]
            measure = row[4]
            chains = [_get_all_ancestors(dims[i], dim_names[i], inv_maps)
                      for i in range(3)]

            for mask in iterproduct([False, True], repeat=3):
                masked_chains = [
                    [ALL] if mask[i] else chains[i]
                    for i in range(3)
                ]
                for combo in iterproduct(*masked_chains):
                    bf_cube[combo] += measure

        cls.bf_cube = dict(bf_cube)

        # -- HCC cube --
        hcc = HierarchicalCompleteCube(data, columns, skip_first_col=True)
        cls.hcc_map = results_to_map(hcc.generate_cube())

    def test_same_number_of_cells(self):
        self.assertEqual(len(self.bf_cube), len(self.hcc_map))

    def test_no_missing_cells_in_hcc(self):
        """All brute-force cells must be present in HCC."""
        missing = [k for k in self.bf_cube if k not in self.hcc_map]
        self.assertEqual(len(missing), 0,
                         f"{len(missing)} cells in brute-force but not HCC: "
                         f"{missing[:5]}")

    def test_no_extra_cells_in_hcc(self):
        """HCC must not contain cells absent from brute-force."""
        extra = [k for k in self.hcc_map if k not in self.bf_cube]
        self.assertEqual(len(extra), 0,
                         f"{len(extra)} extra cells in HCC: {extra[:5]}")

    def test_all_values_match(self):
        """Every common cell must have the same value."""
        mismatches = {
            k: (self.hcc_map[k], self.bf_cube[k])
            for k in self.bf_cube
            if k in self.hcc_map and abs(self.hcc_map[k] - self.bf_cube[k]) > 0.001
        }
        self.assertEqual(len(mismatches), 0,
                         f"{len(mismatches)} value mismatches: "
                         f"{dict(list(mismatches.items())[:5])}")


# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
