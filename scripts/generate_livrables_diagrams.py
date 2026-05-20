import argparse
import os

from scripts.Visualisation.cubeTikZ import cubeTikz
from scripts.generate_star_schema import build_star_schema, generate_star_schema_tikz
from scripts.databaseManagement.dbGetter import dbGetter


def load_db_rows(db_path):
    getter = dbGetter(db_path)
    try:
        tables = getter.get_table_names()
        if not tables:
            raise ValueError(f"Aucune table trouvée dans {db_path}")
        table = tables[0]
        rows = getter.get_all_data(table)
        cols = getter.get_column_names(table)
    finally:
        getter.close()

    if not rows:
        raise ValueError(f"La base {db_path} est vide")

    if cols[0].lower() in ("id", "rowid", "row_id"):
        cols = cols[1:]
        rows = [tuple(row[1:]) for row in rows]

    if len(cols) == 3:
        cols = cols + ["COUNT"]
        rows = [tuple(row) + (1,) for row in rows]
    elif len(cols) != 4:
        raise ValueError(
            f"Le script ne gère que les tables à 3 dimensions + mesure ou 3 dimensions. "
            f"Colonne(s) trouvée(s) : {len(cols)} dans {db_path}"
        )

    return cols, rows


def generate_cube_tikz_for_db(db_path, output_dir, dim_names=None, measure_name="SUM(Q)"):
    cols, rows = load_db_rows(db_path)
    basename = os.path.splitext(os.path.basename(db_path))[0]
    output_path = os.path.join(output_dir, f"{basename}_diagrammeTikz_cube.tex")

    visualizer = cubeTikz(rows)
    if dim_names:
        if len(dim_names) < 3:
            raise ValueError("Il faut fournir au moins 3 noms de dimensions.")
        export_names = dim_names[:3]
    else:
        export_names = cols[:3]

    visualizer.exportCubeToTikZ(export_names, filepath=output_path, measure_name=measure_name)
    return output_path


def generate_star_schema_for_db(db_path, output_dir, dim_names=None, measure_name="COUNT"):
    basename = os.path.splitext(os.path.basename(db_path))[0]
    output_path = os.path.join(output_dir, f"{basename}_star_schema.tex")

    fact_table, dim_tables, fact_cols = build_star_schema(
        db_path,
        output_db=None,
        dim_names=dim_names,
        measure_name=measure_name
    )
    generate_star_schema_tikz(
        output_path,
        fact_table,
        dim_tables,
        fact_cols
    )
    return output_path


def generate_diagrams_for_db(db_path, output_dir, dim_names=None, measure_name="COUNT", style="both"):
    output_paths = []
    if style in ("cube", "both"):
        output_paths.append(generate_cube_tikz_for_db(db_path, output_dir, dim_names=dim_names, measure_name=measure_name))
    if style in ("star", "both"):
        output_paths.append(generate_star_schema_for_db(db_path, output_dir, dim_names=dim_names, measure_name=measure_name))
    return output_paths


def generate_multidimensional_space_for_db(db_path, output_dir, hierarchy, dim_names):
    import sqlite3
    from itertools import product

    basename = os.path.splitext(os.path.basename(db_path))[0]
    output_path = os.path.join(output_dir, f"{basename}_multidimensional_space.tex")

    # 1. Load leaf rows from database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    if not tables:
        raise ValueError(f"Aucune table trouvée dans {db_path}")
    table_name = tables[0][0]

    cursor.execute(f"SELECT * FROM {table_name}")
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    # 2. Build child-to-parent mapping for each dimension
    inv_maps = {}
    for dim in dim_names:
        h = hierarchy.get(dim, {})
        inv_maps[dim] = {child: parent for parent, children in h.items() for child in children}

    def get_ancestors(val, dim):
        inv_map = inv_maps[dim]
        ancestors = []
        curr = val
        while curr in inv_map:
            curr = inv_map[curr]
            ancestors.append(curr)
        return ancestors

    # 3. For each row in the DB, generate all its hierarchical coordinates
    all_cells = set()
    for row in rows:
        dim_values = []
        for dim in dim_names:
            if dim in cols:
                idx = cols.index(dim)
                val = row[idx]
                ancestors = get_ancestors(val, dim)
                mapped_ancestors = []
                for anc in ancestors:
                    if anc == "ALL":
                        mapped_ancestors.append(f"ALL_{dim[0].upper()}")
                    else:
                        mapped_ancestors.append(anc)
                vals = [val] + mapped_ancestors
                if f"ALL_{dim[0].upper()}" not in vals:
                    vals.append(f"ALL_{dim[0].upper()}")
                dim_values.append(vals)
            else:
                dim_values.append([f"ALL_{dim[0].upper()}"])

        for cell in product(*dim_values):
            all_cells.add(cell)

    cells_list = sorted(list(all_cells))

    # Curate selected rows to present a beautiful, concise table matching the thesis style
    selected_rows = []

    # Group 0: No ALL values (Base / Intermediate cells)
    group_0 = [c for c in cells_list if not any(str(val).startswith("ALL_") for val in c)]
    selected_rows.extend(group_0[:5])
    if len(group_0) > 5:
        selected_rows.append("...")

    # Group 1: Exactly 1 ALL value
    group_1 = [c for c in cells_list if sum(str(val).startswith("ALL_") for val in c) == 1]
    for all_idx in range(3):
        sub = [c for c in group_1 if str(c[all_idx]).startswith("ALL_")]
        if sub:
            selected_rows.extend(sub[:2])
            if len(sub) > 2:
                selected_rows.append("...")

    # Group 2: Exactly 2 ALL values
    group_2 = [c for c in cells_list if sum(str(val).startswith("ALL_") for val in c) == 2]
    for not_all_idx in range(3):
        sub = [c for c in group_2 if not str(c[not_all_idx]).startswith("ALL_")]
        if sub:
            selected_rows.extend(sub[:2])
            if len(sub) > 2:
                selected_rows.append("...")

    # Group 3: All 3 are ALL values (Apex Cell)
    group_3 = [c for c in cells_list if sum(str(val).startswith("ALL_") for val in c) == 3]
    selected_rows.extend(group_3)

    # Bottom empty cell
    selected_rows.append("empty")

    # 4. Format LaTeX
    short_dims = [f"Id{d[0]}" for d in dim_names]

    latex_lines = [
        r"\documentclass{article}",
        r"\usepackage{booktabs}",
        r"\usepackage{amsmath}",
        r"\usepackage{amssymb}",
        r"\usepackage[margin=1in]{geometry}",
        r"\begin{document}",
        r"\begin{table}[htbp]",
        r"\centering",
        f"\\caption{{Multidimensional space of the data warehouse {basename.replace('_', ' ')}}}",
        r"\label{tab:multidimensional_space}",
        r"\vspace{0.5em}",
        r"\begin{tabular}{c|" + "c" * len(dim_names) + "}",
        r"\toprule",
        r"\texttt{RowId} & " + " & ".join(f"\\texttt{{{sd}}}" for sd in short_dims) + r" \\",
        r"\midrule"
    ]

    def latex_escape_val(val):
        if val == "empty":
            return r"\emptyset"
        if str(val).startswith("ALL_"):
            dim_char = val.split("_")[1]
            return f"\\textit{{ALL}}_{{\\text{{{dim_char}}}}}"

        val_escaped = str(val).replace("_", r"\_")

        if "-" in val_escaped:
            parts = val_escaped.split("-")
            prefix = parts[0][0]
            rest = parts[0][1:]
            sub = "-".join(parts[1:])
            # Handle cases like "2022-Q1" or "2022-01" nicely
            if prefix.isdigit():
                return f"${parts[0]}_{{\\text{{{sub}}}}}$"
            return f"${prefix}_{{{rest}-{sub}}}$"
        elif len(val_escaped) > 1 and val_escaped[0].isalpha() and val_escaped[1:].isdigit():
            return f"${val_escaped[0]}_{{{val_escaped[1:]}}}$"
        else:
            return f"\\textit{{{val_escaped}}}"

    row_idx = 1
    for r in selected_rows:
        if r == "...":
            latex_lines.append(r"\dots & " + " & ".join([r"\dots"] * len(dim_names)) + r" \\")
        elif r == "empty":
            latex_lines.append(f"{row_idx} & " + " & ".join([r"\emptyset"] * len(dim_names)) + r" \\")
            row_idx += 1
        else:
            escaped_vals = [latex_escape_val(v) for v in r]
            latex_lines.append(f"{row_idx} & " + " & ".join(escaped_vals) + r" \\")
            row_idx += 1

    latex_lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"\end{document}"
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_lines))

    return output_path


def generate_hasse_diagram_for_db(db_path, output_dir, hierarchy, dim_names):
    import os
    basename = os.path.splitext(os.path.basename(db_path))[0]
    output_path = os.path.join(output_dir, f"{basename}_hasse_diagram.tex")

    is_medical = "medical" in basename.lower()

    # Determine labels for both domains (curated 6 nodes for L3 and L2 to avoid overlap)
    if is_medical:
        l3_nodes = [
            (r"\text{Pa}", r"22\text{-}01", r"\text{GP}"),
            (r"\text{Pa}", r"22\text{-}Q1", r"\text{GP}"),
            (r"\text{IdF}", r"22\text{-}01", r"\text{GP}"),
            (r"\text{Fr}", r"22\text{-}01", r"\text{GP}"),
            (r"\text{Ve}", r"22\text{-}01", r"\text{GP}"),
            (r"\text{Pa}", r"22\text{-}02", r"\text{GP}")
        ]
        l2_nodes = [
            (r"\text{Pa}", r"22\text{-}01", r"*"),
            (r"\text{Pa}", r"22\text{-}Q1", r"*"),
            (r"\text{IdF}", r"22\text{-}01", r"*"),
            (r"\text{Fr}", r"22\text{-}01", r"*"),
            (r"\text{Pa}", r"*", r"\text{GP}"),
            (r"*", r"22\text{-}01", r"\text{GP}")
        ]
        l1_nodes = [
            (r"\text{Pa}", r"*", r"*"),
            (r"\text{IdF}", r"*", r"*"),
            (r"\text{Fr}", r"*", r"*"),
            (r"*", r"22\text{-}01", r"*"),
            (r"*", r"*", r"\text{GP}")
        ]
    else:
        l3_nodes = [
            (r"\text{Pa}", r"22\text{-}01", r"\text{PLn}"),
            (r"\text{Pa}", r"22\text{-}Q1", r"\text{PLn}"),
            (r"\text{IdF}", r"22\text{-}01", r"\text{PLn}"),
            (r"\text{Fr}", r"22\text{-}01", r"\text{PLn}"),
            (r"\text{Ve}", r"22\text{-}01", r"\text{PLn}"),
            (r"\text{Pa}", r"22\text{-}02", r"\text{PLn}")
        ]
        l2_nodes = [
            (r"\text{Pa}", r"22\text{-}01", r"*"),
            (r"\text{Pa}", r"22\text{-}Q1", r"*"),
            (r"\text{IdF}", r"22\text{-}01", r"*"),
            (r"\text{Fr}", r"22\text{-}01", r"*"),
            (r"\text{Pa}", r"*", r"\text{PLn}"),
            (r"*", r"22\text{-}01", r"\text{PLn}")
        ]
        l1_nodes = [
            (r"\text{Pa}", r"*", r"*"),
            (r"\text{IdF}", r"*", r"*"),
            (r"\text{Fr}", r"*", r"*"),
            (r"*", r"22\text{-}01", r"*"),
            (r"*", r"*", r"\text{PLn}")
        ]

    # Generate TikZ nodes and edges
    # We will lay out the nodes horizontally centered.
    # Level 4: empty set
    # Level 3: l3_nodes (6 nodes)
    # Level 2: l2_nodes (6 nodes)
    # Level 1: l1_nodes (5 nodes)
    # Level 0: apex set

    tikz_lines = [
        r"\documentclass{article}",
        r"\usepackage{tikz}",
        r"\usepackage{amssymb}",
        r"\usepackage{amsmath}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usetikzlibrary{arrows.meta}",
        r"\begin{document}",
        r"\begin{figure}[htbp]",
        r"\centering",
        r"\begin{tikzpicture}[> =stealth, xscale=0.6, yscale=0.6,",
        r"  node_style/.style={inner sep=2pt, font=\scriptsize},",
        r"  arrow_style/.style={->, draw=black!70, line width=0.5pt}",
        r"]",
        r"",
        r"  % --- LEVEL 4 (Top: Empty set) ---",
        r"  \node[node_style] (L4) at (0, 6) {$(\emptyset, \emptyset, \emptyset)$};",
        r""
    ]

    # L3 nodes positioning (spaced horizontally to ensure no overlapping)
    x_coords_l3 = [-4.5, -2.7, -0.9, 0.9, 2.7, 4.5]
    tikz_lines.append("  % --- LEVEL 3 (Specific cells) ---")
    for i, node in enumerate(l3_nodes):
        label = f"({node[0]}, {node[1]}, {node[2]})"
        tikz_lines.append(f"  \\node[node_style] (L3_{i}) at ({x_coords_l3[i]}, 4.5) {{{label}}};")
    tikz_lines.append(r"  \node[node_style] (L3_dots) at (5.5, 4.5) {$\dots$};")
    tikz_lines.append("")

    # L2 nodes positioning
    x_coords_l2 = [-4.5, -2.7, -0.9, 0.9, 2.7, 4.5]
    tikz_lines.append("  % --- LEVEL 2 (One star) ---")
    for i, node in enumerate(l2_nodes):
        label = f"({node[0]}, {node[1]}, {node[2]})"
        tikz_lines.append(f"  \\node[node_style] (L2_{i}) at ({x_coords_l2[i]}, 3.0) {{{label}}};")
    tikz_lines.append(r"  \node[node_style] (L2_dots) at (5.5, 3.0) {$\dots$};")
    tikz_lines.append("")

    # L1 nodes positioning
    x_coords_l1 = [-3.6, -1.8, 0.0, 1.8, 3.6]
    tikz_lines.append("  % --- LEVEL 1 (Two stars) ---")
    for i, node in enumerate(l1_nodes):
        label = f"({node[0]}, {node[1]}, {node[2]})"
        tikz_lines.append(f"  \\node[node_style] (L1_{i}) at ({x_coords_l1[i]}, 1.5) {{{label}}};")
    tikz_lines.append(r"  \node[node_style] (L1_dots) at (4.5, 1.5) {$\dots$};")
    tikz_lines.append("")

    # L0 node positioning
    tikz_lines.append("  % --- LEVEL 0 (Bottom: Apex) ---")
    tikz_lines.append(r"  \node[node_style] (L0) at (0, 0) {$(*, *, *)$};")
    tikz_lines.append(r"  \node[node_style] (L0_dots) at (1.0, 0) {$\dots$};")
    tikz_lines.append("")

    # Arrows between Level 4 and Level 3
    tikz_lines.append("  % --- ARROWS L4 -> L3 ---")
    for i in range(len(l3_nodes)):
        tikz_lines.append(f"  \\draw[arrow_style] (L4) -- (L3_{i});")
    tikz_lines.append("  \\draw[arrow_style] (L4) -- (L3_dots);")
    tikz_lines.append("")

    # Arrows between Level 3 and Level 2
    # L3_0 (Pa, 22-01, PLn) -> L2_0 (Pa, 22-01, *), L2_4 (Pa, *, PLn), L2_5 (*, 22-01, PLn)
    # L3_1 (Pa, 22-Q1, PLn) -> L2_1 (Pa, 22-Q1, *), L2_4 (Pa, *, PLn)
    # L3_2 (IdF, 22-01, PLn)-> L2_2 (IdF, 22-01, *), L2_5 (*, 22-01, PLn)
    # L3_3 (Fr, 22-01, PLn) -> L2_3 (Fr, 22-01, *), L2_5 (*, 22-01, PLn)
    # L3_4 (Ve, 22-01, PLn) -> L2_5 (*, 22-01, PLn)
    # L3_5 (Pa, 22-02, PLn) -> L2_4 (Pa, *, PLn)
    tikz_lines.append("  % --- ARROWS L3 -> L2 ---")
    connections_l3_l2 = [
        (0, 0), (0, 4), (0, 5),
        (1, 1), (1, 4),
        (2, 2), (2, 5),
        (3, 3), (3, 5),
        (4, 5),
        (5, 4)
    ]
    for src, dst in connections_l3_l2:
        tikz_lines.append(f"  \\draw[arrow_style] (L3_{src}) -- (L2_{dst});")
    tikz_lines.append("")

    # Arrows between Level 2 and Level 1
    # L2_0 (Pa, 22-01, *)   -> L1_0 (Pa, *, *), L1_3 (*, 22-01, *)
    # L2_1 (Pa, 22-Q1, *)   -> L1_0 (Pa, *, *)
    # L2_2 (IdF, 22-01, *)  -> L1_1 (IdF, *, *), L1_3 (*, 22-01, *)
    # L2_3 (Fr, 22-01, *)   -> L1_2 (Fr, *, *), L1_3 (*, 22-01, *)
    # L2_4 (Pa, *, PLn)     -> L1_0 (Pa, *, *), L1_4 (*, *, PLn)
    # L2_5 (*, 22-01, PLn)  -> L1_3 (*, 22-01, *), L1_4 (*, *, PLn)
    tikz_lines.append("  % --- ARROWS L2 -> L1 ---")
    connections_l2_l1 = [
        (0, 0), (0, 3),
        (1, 0),
        (2, 1), (2, 3),
        (3, 2), (3, 3),
        (4, 0), (4, 4),
        (5, 3), (5, 4)
    ]
    for src, dst in connections_l2_l1:
        tikz_lines.append(f"  \\draw[arrow_style] (L2_{src}) -- (L1_{dst});")
    tikz_lines.append("")

    # Arrows between Level 1 and Level 0
    tikz_lines.append("  % --- ARROWS L1 -> L0 ---")
    for i in range(len(l1_nodes)):
        tikz_lines.append(f"  \\draw[arrow_style] (L1_{i}) -- (L0);")
    tikz_lines.append("  \\draw[arrow_style] (L1_dots) -- (L0);")
    tikz_lines.append("")

    # Dashed triangles representing missing paths
    tikz_lines.append("  % --- DASHED TRIANGLES & EXTRA DOTS (matches paper style) ---")
    # For L3 nodes: L3_1, L3_3, L3_5
    dashed_l3 = [1, 3, 5]
    for idx in dashed_l3:
        tikz_lines.extend([
            f"  \\draw[dashed, ->, draw=black!45] (L3_{idx}) -- ++(-0.2,-0.45);",
            f"  \\draw[dashed, ->, draw=black!45] (L3_{idx}) -- ++(0.2,-0.45);",
            f"  \\draw[dotted, thick, draw=black!45] (L3_{idx}) ++(-0.15,-0.36) -- ++(0.3,0);"
        ])

    # For L2 nodes: L2_1, L2_3, L2_5
    dashed_l2 = [1, 3, 5]
    for idx in dashed_l2:
        tikz_lines.extend([
            f"  \\draw[dashed, ->, draw=black!45] (L2_{idx}) -- ++(-0.2,-0.45);",
            f"  \\draw[dashed, ->, draw=black!45] (L2_{idx}) -- ++(0.2,-0.45);",
            f"  \\draw[dotted, thick, draw=black!45] (L2_{idx}) ++(-0.15,-0.36) -- ++(0.3,0);"
        ])

    # For L1 nodes: L1_1, L1_3
    dashed_l1 = [1, 3]
    for idx in dashed_l1:
        tikz_lines.extend([
            f"  \\draw[dashed, ->, draw=black!45] (L1_{idx}) -- ++(-0.2,-0.45);",
            f"  \\draw[dashed, ->, draw=black!45] (L1_{idx}) -- ++(0.2,-0.45);",
            f"  \\draw[dotted, thick, draw=black!45] (L1_{idx}) ++(-0.15,-0.36) -- ++(0.3,0);"
        ])

    tikz_lines.extend([
        r"\end{tikzpicture}",
        f"\\caption{{Hasse diagram of the hierarchical cube lattice of {basename.replace('_', ' ')}}}",
        r"\label{fig:hasse_diagram}",
        r"\end{figure}",
        r"\end{document}"
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(tikz_lines))

    return output_path


def find_db_files(path):
    if os.path.isdir(path):
        return [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".db")]
    if os.path.isfile(path) and path.endswith(".db"):
        return [path]
    raise FileNotFoundError(f"{path} n'existe pas ou n'est pas une base .db")


def main():
    parser = argparse.ArgumentParser(
        description="Génère des diagrammes TikZ de cube de données et/ou des schémas en étoile."
    )
    parser.add_argument(
        "path",
        help="Chemin vers un fichier .db ou un dossier contenant des .db"
    )
    parser.add_argument(
        "--output",
        default="scripts/output/tikZ",
        help="Dossier de sortie pour les fichiers .tex"
    )
    parser.add_argument(
        "--dim-names",
        help=(
            "Noms des dimensions séparés par des virgules. "
            "Exemple : --dim-names Geography,Time,Product"
        )
    )
    parser.add_argument(
        "--measure-name",
        default="COUNT",
        help="Nom de la mesure utilisé dans les en-têtes du diagramme TikZ."
    )
    parser.add_argument(
        "--style",
        choices=["cube", "star", "both"],
        default="both",
        help="Type de diagramme à générer : cube, star ou both."
    )
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    dim_names = None
    if args.dim_names:
        dim_names = [name.strip() for name in args.dim_names.split(",") if name.strip()]

    db_files = find_db_files(args.path)
    if not db_files:
        raise SystemExit("Aucun fichier .db trouvé à traiter.")

    for db_file in db_files:
        try:
            tex_paths = generate_diagrams_for_db(
                db_file,
                args.output,
                dim_names=dim_names,
                measure_name=args.measure_name,
                style=args.style
            )
            for tex_path in tex_paths:
                print(f"✅ Diagramme généré : {tex_path}")
        except Exception as exc:
            print(f"❌ Échec pour {db_file} : {exc}")


if __name__ == "__main__":
    main()
