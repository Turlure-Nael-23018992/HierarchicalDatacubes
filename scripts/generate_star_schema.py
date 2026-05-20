import argparse
import os
import re
import sqlite3


def sanitize_name(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "", str(name))


def sql_ident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def tex_escape(text) -> str:
    text = str(text)
    return text.replace("_", r"\_")


def load_table(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table = cursor.fetchone()

    if table is None:
        conn.close()
        raise ValueError(f"Aucune table trouvée dans {db_path}")

    table_name = table[0]

    cursor.execute(f"PRAGMA table_info({sql_ident(table_name)});")
    cols = [row[1] for row in cursor.fetchall()]

    cursor.execute(f"SELECT * FROM {sql_ident(table_name)};")
    rows = cursor.fetchall()

    conn.close()

    if not rows:
        raise ValueError(f"La table {table_name} est vide")

    return table_name, cols, rows


def build_star_schema(db_path: str, output_db: str = None, dim_names=None, measure_name="COUNT"):
    table_name, cols, rows = load_table(db_path)

    if cols[0].lower() in ("id", "rowid", "row_id"):
        cols = cols[1:]
        rows = [row[1:] for row in rows]

    if len(cols) == 3:
        cols = cols + [measure_name]
        rows = [tuple(row) + (1,) for row in rows]
    elif len(cols) != 4:
        raise ValueError("La table doit contenir 3 dimensions + mesure ou 3 dimensions seulement.")

    dims = dim_names[:3] if dim_names else cols[:3]

    if len(dims) < 3:
        raise ValueError("Il faut fournir au moins 3 noms de dimensions.")

    measure_col = cols[3]
    base_name = os.path.splitext(os.path.basename(db_path))[0]
    fact_table = f"Fact_{sanitize_name(base_name)}"

    dim_tables = []
    dim_lookups = []

    for idx, dim in enumerate(dims, start=1):
        values = sorted({row[idx - 1] for row in rows})
        table = f"D_{sanitize_name(dim)}"
        key = f"Id{sanitize_name(dim)}"

        dim_tables.append((table, key, dim, values))
        dim_lookups.append({value: i + 1 for i, value in enumerate(values)})

    fact_cols = ["RowId"] + [dt[1] for dt in dim_tables] + [measure_col]

    if output_db:
        if os.path.exists(output_db):
            os.remove(output_db)

        conn = sqlite3.connect(output_db)
        c = conn.cursor()

        for table, key, dim, values in dim_tables:
            c.execute(f"DROP TABLE IF EXISTS {sql_ident(table)}")
            c.execute(
                f"CREATE TABLE {sql_ident(table)} "
                f"({sql_ident(key)} INTEGER PRIMARY KEY, {sql_ident(dim)} TEXT)"
            )
            c.executemany(
                f"INSERT INTO {sql_ident(table)} ({sql_ident(key)}, {sql_ident(dim)}) VALUES (?, ?)",
                [(i + 1, v) for i, v in enumerate(values)]
            )

        types = ["INTEGER PRIMARY KEY"] + ["INTEGER"] * 3 + ["REAL"]

        c.execute(f"DROP TABLE IF EXISTS {sql_ident(fact_table)}")
        c.execute(
            f"CREATE TABLE {sql_ident(fact_table)} "
            f"({', '.join(f'{sql_ident(col)} {typ}' for col, typ in zip(fact_cols, types))})"
        )

        fact_rows = []

        for row_id, row in enumerate(rows, start=1):
            keys = [dim_lookups[idx][row[idx]] for idx in range(3)]
            fact_rows.append((row_id, *keys, row[3]))

        placeholders = ", ".join("?" for _ in fact_cols)

        c.executemany(
            f"INSERT INTO {sql_ident(fact_table)} VALUES ({placeholders})",
            fact_rows
        )

        conn.commit()
        conn.close()

    return fact_table, dim_tables, fact_cols


def generate_star_schema_tikz(output_tex: str, fact_table: str, dim_tables, fact_cols):
    def format_table_name(name: str) -> str:
        parts = name.split("_", 1)
        if len(parts) == 2:
            return f"\\texttt{{{parts[0]}\\textsubscript{{{parts[1]}}}}}"
        return f"\\texttt{{{name}}}"

    def table_node(name, cols, x, y, style):
        node_id = sanitize_name(name)
        lines = [
            f"\\node[{style}] ({node_id}) at ({x},{y}) {{",
        ]

        if style == "star fact":
            lines.append(r"\begin{tabular}{c}")
            lines.append(r"\toprule")
            lines.append(f"{format_table_name(name)} \\\\")
            lines.append(r"\midrule")
            if cols:
                lines.append(f"\\texttt{{{tex_escape(cols[0])}}} \\\\")
                lines.append(r"\midrule")
                for col in cols[1:-1]:
                    lines.append(f"\\texttt{{{tex_escape(col)}}} \\\\")
                if len(cols) > 2:
                    lines.append(r"\midrule")
                lines.append(f"\\texttt{{{tex_escape(cols[-1])}}} \\\\")
            lines.append(r"\bottomrule")
            lines.append(r"\end{tabular}};")
        else:
            lines.append(r"\begin{tabular}{c}")
            lines.append(r"\toprule")
            lines.append(f"{format_table_name(name)} \\\\")
            lines.append(r"\midrule")
            if cols:
                lines.append(f"\\texttt{{{tex_escape(cols[0])}}} \\\\")
                if len(cols) > 1:
                    lines.append(r"\midrule")
                    for col in cols[1:]:
                        lines.append(f"\\texttt{{{tex_escape(col)}}} \\\\")
            lines.append(r"\bottomrule")
            lines.append(r"\end{tabular}};")

        return lines

    lines = [
        r"\documentclass[tikz,border=10pt]{standalone}",
        r"\usepackage{tikz}",
        r"\usetikzlibrary{arrows.meta, positioning}",
        r"\usepackage{booktabs}",
        r"\begin{document}",
        r"\begin{tikzpicture}[every node/.style={font=\small}]",
        r"  \tikzset{",
        r"    star table/.style={draw=none, fill=none, inner sep=7pt, align=center, font=\small\ttfamily},",
        r"    star fact/.style={star table},",
        r"    star dim/.style={star table},",
        r"    star line/.style={line width=0.6pt, shorten >=2pt, shorten <=2pt},",
        r"  }"
    ]

    lines += table_node(fact_table, fact_cols, 0, 0, "star fact")

    offsets = [(-7, 4), (7, 4), (0, -5.5)]

    for (table, key, dim, _), (dx, dy) in zip(dim_tables, offsets):
        dim_cols = [key, dim]
        lines += table_node(table, dim_cols, dx, dy, "star dim")

        if dx < 0 and dy > 0:
            lines.append(
                f"\\draw[star line] ({sanitize_name(table)}.east) -- ({sanitize_name(fact_table)}.west);"
            )
        elif dx > 0 and dy > 0:
            lines.append(
                f"\\draw[star line] ({sanitize_name(table)}.west) -- ({sanitize_name(fact_table)}.east);"
            )
        else:
            lines.append(
                f"\\draw[star line] ({sanitize_name(table)}.north) -- ({sanitize_name(fact_table)}.south);"
            )

    lines += [
        r"\end{tikzpicture}",
        r"\end{document}"
    ]

    with open(output_tex, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_tex


def main():
    parser = argparse.ArgumentParser(
        description="Génère un schéma en étoile et une table de faits à partir d'une base SQLite."
    )

    parser.add_argument("db_path", help="Chemin vers la base SQLite à utiliser")
    parser.add_argument("--output-db", default="star_schema_C3_R5.db")
    parser.add_argument("--output-tex", default="star_schema_C3_R5.tex")
    parser.add_argument("--dim-names", help="Noms des 3 dimensions séparés par des virgules")
    parser.add_argument("--measure-name", default="COUNT")
    parser.add_argument("--skip-db", action="store_true")

    args = parser.parse_args()

    dim_names = None
    if args.dim_names:
        dim_names = [name.strip() for name in args.dim_names.split(",") if name.strip()]

    output_db = None if args.skip_db else args.output_db

    fact_table, dim_tables, fact_cols = build_star_schema(
        args.db_path,
        output_db,
        dim_names=dim_names,
        measure_name=args.measure_name
    )

    tex_path = generate_star_schema_tikz(
        args.output_tex,
        fact_table,
        dim_tables,
        fact_cols
    )

    if args.skip_db:
        print("✅ Diagramme généré sans recréer de base de données.")
    else:
        print(f"✅ Base en étoile créée : {args.output_db}")

    print(f"✅ Diagramme généré : {tex_path}")


if __name__ == "__main__":
    main()