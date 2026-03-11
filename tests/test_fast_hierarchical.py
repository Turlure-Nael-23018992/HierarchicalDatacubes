import sys
import random

from scripts.Algorithms.HierarchicalClosetCube import HierarchicalClosetCube
from scripts.Algorithms.FastHierarchicalClosetCube import FastHierarchicalClosetCube

# Generate dummy data valid in the STATIC_HIERARCHY
data = [
    [1, "Paris",      "2023-01-01", "Pomme de terre", 10,  5],
    [2, "Marseille",  "2023-02-01", "Carotte",        15,  8],
    [3, "Nanterre",   "2023-01-01", "Fraise",         5,   2],
    [4, "Nice",       "2023-01-01", "Orange",         8,   4],
    [5, "Paris",      "2023-01-15", "Framboise",      10,  5]
]

for i in range(1000):
   geog = random.choice(["Paris", "Marseille", "Nice", "Lille", "Munich", "Barcelone"])
   time_val = random.choice(["2021-05-01", "2022-01-01", "2023-01-15", "2024-03-08", "2024-07-31"])
   food = random.choice(["Fraise", "Framboise", "Orange", "Citron", "Épinard", "Brocoli"])
   data.append([i+10, geog, time_val, food, random.randint(1, 20), random.randint(1, 10)])

columns = ["ID", "Geography", "Time", "Food", "Sales", "Profit"]

print("Running Old HierarchicalClosetCube...")
old_algo = HierarchicalClosetCube(data, columns, iceberg_threshold=0, skip_first_col=True)
old_result = old_algo.generate_closed_cube(aggregation_dict={"Sales": "SUM", "Profit": "SUM"})
print(f"Old length: {len(old_result)}, Time: {old_algo.time:.4f}s")

print("Running Fast HierarchicalClosetCube...")
new_algo = FastHierarchicalClosetCube(data, columns, iceberg_threshold=0, skip_first_col=True)
new_result = new_algo.generate_closed_cube(aggregation_dict={"Sales": "SUM", "Profit": "SUM"})
print(f"New length: {len(new_result)}, Time: {new_algo.time:.4f}s")

old_set = set(old_result)
new_set = set(new_result)

print("-----", old_set, "\n-----", new_set)
if old_set == new_set:
    print("\nSUCCESS: The results are EXACTLY identical.")
else:
    print("\nERROR: Differences found.")
    print(f"In old but not new: {len(old_set - new_set)}")
    print(f"In new but not old: {len(new_set - old_set)}")
