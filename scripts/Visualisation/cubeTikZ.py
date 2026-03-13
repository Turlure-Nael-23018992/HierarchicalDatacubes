from collections import defaultdict
import matplotlib.pyplot as plt
import os


class cubeTikz:
    def __init__(self, data):
        self.data = data

    def exportCubeToTikZ(self, colNames, filepath="cube_tikz_output.tex"):
        def is_numeric(val):
            try:
                int(val)
                return True
            except:
                return False

        if isinstance(self.data, dict):
            data = list(self.data.values())
        else:
            data = self.data

        if all(is_numeric(row[-1]) for row in data):
            datadict = {i: row[:-1] for i, row in enumerate(data)}
            measures = {i: int(row[-1]) for i, row in enumerate(data)}
        else:
            datadict = {i: d for i, d in enumerate(data)}
            measures = {i: 1 for i in datadict}

        def aggregate_rows(rows):
            agg = defaultdict(int)
            for row in rows:
                key = tuple(row[:-1])
                agg[key] += row[-1]
            return [list(k) + [v] for k, v in agg.items()]

        full_rows = aggregate_rows([list(datadict[k]) + [measures[k]] for k in datadict])
        rows_01 = aggregate_rows([[d[0], d[1], measures[k]] for k, d in datadict.items()])
        rows_02 = aggregate_rows([[d[0], d[2], measures[k]] for k, d in datadict.items()])
        rows_12 = aggregate_rows([[d[1], d[2], measures[k]] for k, d in datadict.items()])
        rows_0 = aggregate_rows([[d[0], measures[k]] for k, d in datadict.items()])
        rows_1 = aggregate_rows([[d[1], measures[k]] for k, d in datadict.items()])
        rows_2 = aggregate_rows([[d[2], measures[k]] for k, d in datadict.items()])
        total = sum(measures.values())

        table_info = [
            ("main", full_rows, [colNames[0], colNames[1], colNames[2], "SUM(Q)"], 0, 9),
            ("tp", rows_01, [colNames[0], colNames[1], "SUM(Q)"], -5, -4),
            ("te", rows_02, [colNames[0], colNames[2], "SUM(Q)"], -5, 9),
            ("pe", rows_12, [colNames[1], colNames[2], "SUM(Q)"], -5, 22),
            ("t", rows_0, [colNames[0], "SUM(Q)"], -10.5, -4),
            ("p", rows_1, [colNames[1], "SUM(Q)"], -10.5, 9),
            ("e", rows_2, [colNames[2], "SUM(Q)"], -10.5, 22),
            ("sum", [[total]], ["SUM(Q)"], -15.5, 9),
        ]

        arrows = [
            ("main", "tp"), ("main", "te"), ("main", "pe"),
            ("tp", "t"), ("tp", "p"), ("te", "t"),
            ("te", "e"), ("pe", "p"), ("pe", "e"),
            ("t", "sum"), ("p", "sum"), ("e", "sum")
        ]

        full_path = os.path.abspath(filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(r"""\documentclass[10pt]{article}
    \usepackage{tikz}
    \usetikzlibrary{arrows.meta}
    \usepackage{adjustbox}
    \usepackage{array}
    \usepackage{booktabs}
    \usepackage[landscape, margin=0.5cm]{geometry}
    \pagestyle{empty}

    \begin{document}
    \begin{center}
    \scalebox{0.7}{
    \begin{tikzpicture}[every node/.style={inner sep=0pt}]
    \newcolumntype{M}[1]{>{\centering\arraybackslash\itshape}m{#1}}
    \newcolumntype{C}[1]{>{\centering\arraybackslash}m{#1}}
    """)

            for name, rows, headers, y, x in table_info:
                nb_cols = len(headers)
                col_fmt = (
                    "@{\\hspace{0pt}}" + " ".join(["M{3.8cm}"] * (nb_cols - 1)) +
                    " !{\\vrule} C{1.5cm}@{}" if nb_cols > 1 else "@{}C{1.5cm}@{}"
                )
                width_map = {4: "0.85\\textwidth", 3: "0.53\\textwidth", 2: "0.35\\textwidth", 1: "0.23\\textwidth"}
                max_width = width_map.get(nb_cols, "0.5\\textwidth")

                f.write(
                    f"\n% {name.upper()}\n"
                    f"\\node ({name}) at ({x},{y}) {{\n"
                    f"\\begin{{adjustbox}}{{max width={max_width}}}\n"
                    f"{{\\renewcommand{{\\arraystretch}}{{1.5}}%\n"
                    f"\\begin{{tabular}}{{{col_fmt}}}\n\\toprule\n"
                )
                if nb_cols == 1:
                    f.write(f"\\textbf{{{headers[0]}}} \\\\\n\\midrule\n")
                else:
                    f.write(" & ".join(headers[:-1]) + " & \\textbf{" + headers[-1] + "} \\\\\n\\midrule\n")
                for row in rows:
                    f.write(" & ".join(map(str, row)) + r" \\" + "\n")
                f.write("\\bottomrule\n\\end{tabular}}\n\\end{adjustbox}\n};\n")

            for src, dst in arrows:
                f.write(
                    f"\\draw[->, line width=2pt, >=Latex, shorten >=2pt, shorten <=2pt] ({src}.south) -- ({dst}.north);\n")

            f.write(r"""\end{tikzpicture}
    } % ← fin de scalebox
    \end{center}
    \end{document}
    """)

        print(f"✅ Fichier TikZ exporté avec succès : {full_path}")

    def generateCube(self):
        # S'assurer que c'est une liste de tuples
        if isinstance(self.data, dict):
            data = list(self.data.values())
        else:
            data = self.data

        # Vérifie si les lignes contiennent une mesure à la fin
        def is_numeric(val):
            try:
                int(val)
                return True
            except:
                return False

        # Séparation des mesures si présentes
        if all(is_numeric(row[-1]) for row in data):
            datadict = {i: row[:-1] for i, row in enumerate(data)}
            measures = {i: int(row[-1]) for i, row in enumerate(data)}
        else:
            datadict = {i: row for i, row in enumerate(data)}
            measures = {i: 1 for i in datadict}

        def aggregate_rows(rows):
            agg = defaultdict(int)
            for row in rows:
                key = tuple(row[:-1])
                agg[key] += row[-1]
            return [list(k) + [v] for k, v in agg.items()]

        # Données agrégées
        full_rows = aggregate_rows([list(datadict[k]) + [measures[k]] for k in datadict])
        rows_type_prop = aggregate_rows([[d[0], d[1], measures[k]] for k, d in datadict.items()])
        rows_type_equip = aggregate_rows([[d[0], d[2], measures[k]] for k, d in datadict.items()])
        rows_prop_equip = aggregate_rows([[d[1], d[2], measures[k]] for k, d in datadict.items()])
        rows_type = aggregate_rows([[d[0], measures[k]] for k, d in datadict.items()])
        rows_prop = aggregate_rows([[d[1], measures[k]] for k, d in datadict.items()])
        rows_equip = aggregate_rows([[d[2], measures[k]] for k, d in datadict.items()])
        total_sum = sum(row[-1] for row in full_rows)

        # Figure
        fig, ax = plt.subplots(figsize=(15, 13))
        ax.axis('off')

        def create_table(cellText, colLabels, bbox):
            table = plt.table(
                cellText=cellText,
                colLabels=colLabels,
                cellLoc='center',
                loc='center',
                bbox=bbox,
                edges='closed'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
            for (row, col), cell in table.get_celld().items():
                if row == 0:
                    cell.set_text_props(weight='bold')
            return table

        # Création des tableaux
        table_main = create_table(full_rows, ["R", "D", "V", "SUM(Q)"], [0.35, 0.85, 0.3, 0.12])
        table_type_prop = create_table(rows_type_prop, ["R", "D", "SUM(Q)"], [0.0, 0.6, 0.3, 0.12])
        table_type_equip = create_table(rows_type_equip, ["R", "V", "SUM(Q)"], [0.35, 0.6, 0.3, 0.12])
        table_prop_equip = create_table(rows_prop_equip, ["D", "V", "SUM(Q)"], [0.7, 0.6, 0.3, 0.12])
        table_type = create_table(rows_type, ["R", "SUM(Q)"], [0.0, 0.28, 0.2, 0.12])
        table_prop = create_table(rows_prop, ["D", "SUM(Q)"], [0.4, 0.28, 0.2, 0.12])
        table_equip = create_table(rows_equip, ["V", "SUM(Q)"], [0.8, 0.28, 0.2, 0.12])
        table_sum = create_table([[total_sum]], ["SUM(Q)"], [0.4, 0.05, 0.2, 0.08])

        def draw_arrow(ax, start, end):
            ax.annotate("", xy=end, xytext=start,
                        arrowprops=dict(arrowstyle="->", lw=2))

        offset = 0.015
        draw_arrow(ax, (0.5, 0.85), (0.15, 0.6 + 0.12 + offset))
        draw_arrow(ax, (0.5, 0.85), (0.5, 0.6 + 0.12 + offset))
        draw_arrow(ax, (0.5, 0.85), (0.85, 0.6 + 0.12 + offset))
        draw_arrow(ax, (0.15, 0.6), (0.1, 0.28 + 0.12 + offset))
        draw_arrow(ax, (0.5, 0.6), (0.1, 0.28 + 0.12 + offset))
        draw_arrow(ax, (0.15, 0.6), (0.5, 0.28 + 0.12 + offset))
        draw_arrow(ax, (0.85, 0.6), (0.5, 0.28 + 0.12 + offset))
        draw_arrow(ax, (0.5, 0.6), (0.9, 0.28 + 0.12 + offset))
        draw_arrow(ax, (0.85, 0.6), (0.9, 0.28 + 0.12 + offset))
        draw_arrow(ax, (0.1, 0.28), (0.5, 0.05 + 0.08 + offset))
        draw_arrow(ax, (0.5, 0.28), (0.5, 0.05 + 0.08 + offset))
        draw_arrow(ax, (0.9, 0.28), (0.5, 0.05 + 0.08 + offset))

        plt.show()