import os
import json
import re
import sqlite3
import traceback
import matplotlib.pyplot as plt
import math
import time
import pandas as pd

from scripts.Algorithms.BUC import *
from scripts.Algorithms.starCubing import *
from scripts.Algorithms.closetCube import *
from scripts.Algorithms.HierarchicalBUC import *
from scripts.Algorithms.HierarchicalStarCubing import *
from scripts.Algorithms.HierarchicalClosetCube import *


def extract_row_count(filename):
    match = re.search(r'_R(\d+)', filename)
    if not match:
        print(f"⚠️ Nom de fichier non reconnu : {filename}")
    return int(match.group(1)) if match else None

def load_data_and_columns_cleaned(db_path, expected_attrib_count=3):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_name = cur.fetchone()[0]

    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = cur.fetchone()[0]

    # Chargement intelligent : 5% des données ou 1 million max
    limit_rows = total_rows
    cur.execute(f"SELECT * FROM {table_name} LIMIT {limit_rows}")
    data = cur.fetchall()

    if not data:
        print(f"⚠️ Aucune donnée chargée depuis {db_path} → données vides.")

    column_names = [desc[0] for desc in cur.description]

    if "RowId" in column_names:
        idx = column_names.index("RowId")
        column_names.pop(idx)
        data = [list(row[:idx] + row[idx + 1:]) for row in data]

    if len(column_names) == expected_attrib_count:
        column_names.append("COUNT")
        data = [list(row) + [1] for row in data]

    conn.close()
    return data, column_names


class ProcessAlgo:
    def __init__(self, folder_path, output_json="timings.json"):
        self.folder_path = folder_path
        self.output_json = output_json
        self.results = {}

    def runBUC(self, isPrinted=False):
        results = {}
        for filename in sorted(os.listdir(self.folder_path), key=extract_row_count):
            if filename.endswith(".db"):
                db_path = os.path.join(self.folder_path, filename)
                result = self._process_file_buc(db_path, filename, isPrinted)
                results[filename] = result
        self._save_results(results, key="BUC")

    def runStarCubing(self, isPrinted=False):
        results = {}
        for filename in sorted(os.listdir(self.folder_path), key=extract_row_count):
            if filename.endswith(".db"):
                db_path = os.path.join(self.folder_path, filename)
                result = self._process_file_star(db_path, filename, isPrinted)
                results[filename] = result
        self._save_results(results, key="StarCubing")

    def _process_file_buc(self, db_path, filename, isPrinted):
        try:
            buc = BUC(db_path)
            _, timer = buc.run(isPrinted=isPrinted)
            return {"success": True, "duration_seconds": round(timer, 5)}
        except Exception as e:
            print(f"Erreur pour {filename} (BUC) : {e}")
            traceback.print_exc()
            return {"success": False, "duration_seconds": None}

    def _process_file_star(self, db_path, filename, isPrinted):
        try:
            data, column_names = load_data_and_columns_cleaned(db_path)
            star = StarCubing(data, column_names, iceberg_threshold=1)
            _, timer = star.run(isPrinted=isPrinted)
            return {"success": True, "duration_seconds": round(timer, 5)}
        except Exception as e:
            print(f"Erreur pour {filename} (StarCubing) : {e}")
            traceback.print_exc()
            return {"success": False, "duration_seconds": None}

    def runClosetCube(self, isPrinted=False):
        results = {}
        # Assurez-vous que self.folder_path existe et contient des fichiers .db
        if not os.path.exists(self.folder_path):
            print(f"Le dossier '{self.folder_path}' n'existe pas.")
            return results

        for filename in sorted(os.listdir(self.folder_path), key=extract_row_count):
            if filename.endswith(".db"):
                db_path = os.path.join(self.folder_path, filename)
                result = self._process_file_closet(db_path, filename, isPrinted)
                results[filename] = result
        self._save_results(results, key="ClosetCube")

    def _process_file_closet(self, db_path, filename, isPrinted):
        try:
            data, column_names = load_data_and_columns_cleaned(db_path)

            # La mesure est toujours la dernière colonne
            measure_name = column_names[-1]

            # Instanciation de la classe ClosetCube
            # iceberg_threshold est mis à 0 pour calculer tous les cuboids fermés par défaut
            cube = ClosetCube(data, column_names, iceberg_threshold=0)

            # Définition de l'agrégation. Si la mesure est "COUNT", on agrège par "COUNT".
            # Sinon, on agrège par "SUM" par défaut (ou selon votre logique métier).
            aggregation_type = "COUNT" if measure_name == "COUNT" else "SUM"
            aggregation_dict = {measure_name: aggregation_type}

            # Appel de generate_cube et récupération des résultats et du temps d'exécution
            # Le multiprocessing est géré à l'intérieur de generate_cube
            _, duration = cube.generate_cube(
                aggregation=aggregation_dict,
                verbose=isPrinted,
                as_dataframe=False, # Retourne une liste de dicts, pas un DataFrame pour cette fonction
                write_to_file=False # Vous pouvez changer ceci si vous voulez écrire dans un fichier ici
            )

            return {"success": True, "duration_seconds": round(duration, 5)}
        except Exception as e:
            print(f"Erreur pour {filename} (ClosetCube) : {e}")
            traceback.print_exc()
            return {"success": False, "duration_seconds": None}

    def _process_file_hierarchical_buc(self, db_path, filename, isPrinted):
        try:
            # Chargement données
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query("SELECT * FROM Pokemon", conn)
            conn.close()
            df = df.dropna()

            # Ajout de la mesure COUNT si elle n'existe pas
            if "COUNT" not in df.columns:
                df["COUNT"] = 1

            rows = df[["Geography", "Time", "Food", "COUNT"]].values.tolist()
            dimensions = ["Geography", "Time", "Food", "COUNT"]

            # Hiérarchie cohérente avec les valeurs utilisées
            full_hierarchy = {
                "Geography": [
                    "France", "Île-de-France", "PACA", "Hauts-de-France", "Strasbourg", "Nanterre", "Paris",
                    "Marseille",
                    "Toulouse", "Valence", "Lyon", "Grenoble", "Italie", "Belgique", "Espagne", "Piémont", "Turin",
                    "Milan", "Wallonie", "Liège", "Bruxelles", "Rhénanie", "Sévillle", "Madrid", "Catalogne",
                    "Barcelone"
                ],
                "Time": [
                    "2021", "2022", "2023", "2024",
                    "2022-01", "2023-01", "2023-07", "2024-07", "2022-12", "2023-02",
                    "2023-01-15", "2024-07-14", "2021-12-31", "2022-04-01"
                ],
                "Food": [
                    "Fruits", "Légumes", "Céréales", "Viandes", "Produits laitiers",
                    "Fruits rouges", "Agrumes", "Légumes verts", "Tubercules", "Viandes rouges",
                    "Poissons", "Fromages", "Yaourts", "Pâtes",
                    "Fraise", "Framboise", "Orange", "Citron", "Épinard", "Brocoli",
                    "Pomme de terre", "Carotte", "Boeuf", "Poulet", "Saumon", "Thon",
                    "Camembert", "Comté", "Yaourt nature", "Yaourt aux fruits", "Spaghetti", "Penne"
                ]
            }

            h_buc = HierarchicalBUC(
                data=rows,
                dimensions=dimensions,
                aggregation={"COUNT": "SUM"},
                hierarchy=full_hierarchy
            )

            start = time.time()
            h_buc.run_flat_buc_like_cube(
                {i: row for i, row in enumerate(rows)},
                dimensions,
                {"COUNT": "SUM"},
                isPrinted=isPrinted
            )
            duration = time.time() - start

            print(f"\n⏱ Durée d'exécution BUC Hiérarchique : {duration:.5f} secondes (fichier : {filename})")
            return {"success": True, "duration_seconds": round(duration, 5)}

        except Exception as e:
            print(f"Erreur pour {filename} (HierarchicalBUC) : {e}")
            traceback.print_exc()
            return {"success": False, "duration_seconds": None}

    def runHierarchicalBUC(self, isPrinted=False):
        results = {}
        for filename in sorted(os.listdir(self.folder_path), key=extract_row_count):
            if filename.endswith(".db"):
                db_path = os.path.join(self.folder_path, filename)
                result = self._process_file_hierarchical_buc(db_path, filename, isPrinted)
                results[filename] = result
        self._save_results(results, key="HierarchicalBUC")

    def runHierarchicalStarCubing(self, isPrinted=False):
        results = {}
        for filename in sorted(os.listdir(self.folder_path), key=extract_row_count):
            if filename.endswith(".db"):
                db_path = os.path.join(self.folder_path, filename)
                try:
                    # On instancie un objet sans se servir du __init__ car run_from_db fait tout le traitement
                    star = HierarchicalStarCubing({}, [], {}, {})
                    result = star.run_from_db(db_path, isPrinted=isPrinted)
                    results[filename] = result
                except Exception as e:
                    print(f"Erreur pour {filename} (HierarchicalStarCubing) : {e}")
                    traceback.print_exc()
                    results[filename] = {"success": False, "duration_seconds": None}
        self._save_results(results, key="HierarchicalStarCubing")

    def runHierarchicalClosetCube(self, isPrinted=False):
        results = {}

        # 🔍 Lister uniquement les fichiers .db (ignorer les dossiers comme 'cosky' ou 'hierarchie')
        valid_files = [
            f for f in os.listdir(self.folder_path)
            if os.path.isfile(os.path.join(self.folder_path, f)) and f.endswith(".db")
        ]

        # 🔢 Trier par cardinalité extraite du nom
        sorted_files = sorted(valid_files, key=extract_row_count)

        for filename in sorted_files:
            db_path = os.path.join(self.folder_path, filename)

            try:
                # Chargement des données
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                table_name = cursor.fetchone()[0]

                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                conn.close()

                df = df.dropna()
                if "COUNT" not in df.columns:
                    df["COUNT"] = 1

                data = df.values.tolist()
                column_names = df.columns.tolist()

                # ⚙️ Exécution du cube fermé hiérarchique
                cube = HierarchicalClosetCube(data, column_names)
                start = time.time()
                result_rows = cube.generate_closed_cube(verbose=isPrinted)
                duration = time.time() - start

                results[filename] = {
                    "success": True,
                    "duration_seconds": round(duration, 5)
                }

                print(
                    f"⏱ Durée d'exécution HierarchicalClosetCube : {duration:.5f} secondes (lignes : {len(df)}, tuples : {len(result_rows)})")

            except Exception as e:
                print(f"❌ Erreur pour {filename} (HierarchicalClosetCube) : {e}")
                traceback.print_exc()
                results[filename] = {"success": False, "duration_seconds": None}

        self._save_results(results, key="HierarchicalClosetCube")

    def _save_results(self, new_results: dict, key: str):
        if os.path.exists(self.output_json):
            with open(self.output_json, "r") as f:
                existing = json.load(f)
        else:
            existing = {}

        if key not in existing:
            existing[key] = {}

        for filename, result in new_results.items():
            prev = existing[key].get(filename)
            if prev:
                if prev["success"] and result["success"]:
                    if result["duration_seconds"] < prev["duration_seconds"]:
                        existing[key][filename] = result
                elif result["success"]:
                    existing[key][filename] = result
                elif prev["success"]:
                    existing[key][filename] = prev
                else:
                    existing[key][filename] = result
            else:
                existing[key][filename] = result

        with open(self.output_json, "w") as f:
            json.dump(existing, f, indent=4)

        print(f"Résultats {key} enregistrés dans {self.output_json}")

    def plot_execution_times_from_json(self, json_path, output_folder):
        with open(json_path, "r") as f:
            data = json.load(f)

        # Définition des groupes d'algorithmes et paramètres de sortie
        algo_groups = [
            ("BUC + SC + Cl (sans H)",
             ["BUC", "StarCubing", "ClosetCube"], "Buc_SC_Cl_noH.tex", "LinX", "LogY"),
            ("BUC + SC + Cl (avec H)",
             ["HierarchicalBUC", "HierarchicalStarCubing", "HierarchicalClosetCube"],
             "Buc_SC_Cl_withH.tex", "LinX", "LogY"),
            ("BUC vs HierarchicalBUC",
             ["BUC", "HierarchicalBUC"], "BUC_vs_HBUC.tex", "LinX", "LinY"),
            ("SC vs HierarchicalSC",
             ["StarCubing", "HierarchicalStarCubing"], "SC_vs_HSC.tex", "LinX", "LinY"),
            ("Cl vs HierarchicalCl",
             ["ClosetCube", "HierarchicalClosetCube"], "Cl_vs_HCl.tex", "LinX", "LinY"),
        ]

        def extract_size(name):
            match = re.search(r'_R(\d+)', name)
            return int(match.group(1)) if match else None

        for title, algos, filename, scaleX, scaleY in algo_groups:
            all_points = {}

            for algo in algos:
                print(f"→ Groupe: {title}, algo demandé: {algo}, existe dans JSON ? {algo in data}")  # DEBUG
                if algo not in data:
                    continue
                for db_name, stats in data[algo].items():
                    size = extract_size(db_name)
                    t = stats.get("duration_seconds")
                    if size is not None and stats.get("success") and t is not None:
                        all_points.setdefault(algo, []).append((size, t))

            # Construction du graphe même si vide (pour vérifier visuellement)
            tex_path = os.path.join(output_folder, filename)
            with open(tex_path, "w") as f:
                f.write(r"\documentclass[tikz,border=10pt]{standalone}" + "\n")
                f.write(r"\usepackage{tikz,pgfplots}" + "\n")
                f.write(r"\pgfplotsset{compat=1.18}" + "\n")
                f.write(r"\usepackage{xcolor}" + "\n")
                f.write(r"\begin{document}" + "\n")
                f.write(r"\begin{tikzpicture}" + "\n")
                f.write(r"\begin{axis}[" + "\n")
                f.write(f"title={{{title}}},\n")
                f.write("xlabel={Cardinality}, ylabel={Response time (s)},\n")

                # Échelles
                if scaleX == "LogX":
                    f.write("xmode=log, log basis x=10,\n")
                if scaleY == "LogY":
                    f.write("ymode=log, log basis y=10,\n")

                f.write("xmin=1000, xmax=100000000,\n")
                if scaleY == "LinY":
                    f.write("ymin=0,\n ymax=1500,\n")

                f.write("scaled x ticks=false, scaled y ticks=false,\n")
                f.write("xtick={1000,10000,100000,1000000,10000000,100000000},\n")
                f.write("xticklabels={1K,10K,100K,1M,10M,100M},\n")
                f.write("xticklabel style={font=\\small},\n")

                if scaleY == "LogY":
                    f.write("ytick={0.001,0.01,0.1,1,10,100,1000},\n")
                    f.write("yticklabels={$10^{-3}$,$10^{-2}$,$10^{-1}$,$10^{0}$,$10^{1}$,$10^{2}$,$10^{3}$},\n")
                else:
                    f.write("ytick={0,200,400,600,800,1000,1200,1400},\n")

                f.write("yticklabel style={font=\\small},\n")
                f.write("grid=major,\n")
                f.write("legend style={font=\\small, at={(0.5,-0.15)}, anchor=north, legend columns=-1},\n")
                f.write("tick align=outside,\n")
                f.write("]\n")

                colors = ["skyblue", "brightmaroon", "SQLCodeGreen"]
                markers = ["*", "o", "square*"]
                for i, algo in enumerate(all_points):
                    pts = sorted(all_points[algo], key=lambda x: x[0])
                    color = colors[i % len(colors)]
                    mark = markers[i % len(markers)]
                    f.write(
                        f"\\addplot[color={color}, mark={mark}, mark options={{solid}}, line width=1.2pt] coordinates {{%\n")
                    for size, time in pts:
                        f.write(f"  ({size},{time}) ")
                    f.write("};\n")
                    f.write(f"\\addlegendentry{{{algo}}}\n")

                f.write(r"\end{axis}" + "\n")
                f.write(r"\end{tikzpicture}" + "\n")
                f.write(r"\end{document}" + "\n")

            print(f"✅ Graphe généré : {filename}")

    def generate_execution_graphs_from_summary(self, json_path: str, output_folder: str):
        """
        Génère des graphes LaTeX de temps d'exécution à partir d’un fichier JSON de performance.

        :param json_path: chemin vers le fichier JSON contenant les données de performance.
        :param output_folder: dossier de sortie pour les fichiers .tex générés.
        """
        os.makedirs(output_folder, exist_ok=True)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        algo_colors = {
            "BUC": "blue",
            "StarCubing": "green",
            "ClosetCube": "orange",
            "HierarchicalBUC": "red",
            "HierarchicalStarCubing": "purple",
            "HierarchicalClosetCube": "brown"
        }

        graph_configs = [
            {
                "title": "Execution Time: BUC vs StarCubing vs ClosetCube",
                "algos": ["BUC", "StarCubing", "ClosetCube"],
                "filename": "BUC_StarCubing_ClosetCube.tex"
            },
            {
                "title": "Execution Time: HierarchicalBUC vs HierarchicalStarCubing vs HierarchicalClosetCube",
                "algos": ["HierarchicalBUC", "HierarchicalStarCubing", "HierarchicalClosetCube"],
                "filename": "HierarchicalBUC_Star_Closet.tex"
            },
            {
                "title": "Execution Time: BUC vs HierarchicalBUC",
                "algos": ["BUC", "HierarchicalBUC"],
                "filename": "BUC_vs_HierarchicalBUC.tex"
            },
            {
                "title": "Execution Time: StarCubing vs HierarchicalStarCubing",
                "algos": ["StarCubing", "HierarchicalStarCubing"],
                "filename": "StarCubing_vs_Hierarchical.tex"
            },
            {
                "title": "Execution Time: ClosetCube vs HierarchicalClosetCube",
                "algos": ["ClosetCube", "HierarchicalClosetCube"],
                "filename": "Closet_vs_HierarchicalCloset.tex"
            }
        ]

        def extract_size(name):
            match = re.search(r'_R(\d+)', name)
            return int(match.group(1)) if match else None

        for config in graph_configs:
            plots = []
            for algo in config["algos"]:
                if algo not in data:
                    continue

                x_vals, y_vals = [], []
                for db_name, stats in data[algo].items():
                    size = extract_size(db_name)
                    if size is not None and stats["success"] and stats["duration_seconds"] is not None:
                        x_vals.append(size)
                        y_vals.append(stats["duration_seconds"])

                if x_vals:
                    x_sorted, y_sorted = zip(*sorted(zip(x_vals, y_vals)))
                    color = algo_colors.get(algo, "black")
                    plot_line = (
                            f"\\addplot[color={color}, mark=*] coordinates {{"
                            + " ".join(f"({x},{y})" for x, y in zip(x_sorted, y_sorted))
                            + "};\n"
                              f"\\addlegendentry{{{algo}}}"
                    )
                    plots.append(plot_line)

            if not plots:
                continue

            tex_lines = [
                            "\\documentclass{standalone}",
                            "\\usepackage{pgfplots}",
                            "\\pgfplotsset{compat=1.18}",
                            "\\begin{document}",
                            "\\begin{tikzpicture}[scale=1.5]",
                            "\\begin{axis}[",
                            "    width=12cm, height=8cm,",
                            "    xlabel={\\textbf{Database size (rows)}},",
                            "    ylabel={\\textbf{Execution time (seconds)}},",
                            "    xmode=log,",
                            "    ymode=linear,",
                            "    grid=major,",
                            "    legend style={font=\\small, at={(0.03,0.97)}, anchor=north west},",
                            "    tick label style={font=\\small},",
                            "    label style={font=\\bfseries\\small},",
                            "    title style={font=\\bfseries\\large},",
                            f"    title={{{config['title']}}}",
                            "]"
                        ] + plots + [
                            "\\end{axis}",
                            "\\end{tikzpicture}",
                            "\\end{document}"
                        ]

            with open(os.path.join(output_folder, config["filename"]), "w", encoding="utf-8") as f:
                f.write("\n".join(tex_lines))

            print(f"✅ Graph generated: {config['filename']}")