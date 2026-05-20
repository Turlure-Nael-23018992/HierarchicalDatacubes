import argparse
from pathlib import Path

from temp import generation
from scripts.generate_livrables_diagrams import (
    generate_diagrams_for_db,
    generate_multidimensional_space_for_db,
    generate_hasse_diagram_for_db
)


def get_dim_names_for_db(db_name: str):
    if "banking" in db_name:
        return ["Geography", "Time", "Product"]
    if "medical" in db_name:
        return ["Geography", "Time", "Service"]
    return None


def get_hierarchy_for_db(db_name: str):
    if "banking" in db_name:
        return generation.BANKING_HIERARCHY
    if "medical" in db_name:
        return generation.MEDICAL_HIERARCHY
    return None


def generate_full_temp_pipeline(output_dir: Path, rows: int = 5, tex_output_dir: Path = None):
    """Generate all sample datasets and their TikZ LaTeX exports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if tex_output_dir is None:
        tex_output_dir = output_dir / "tex"
    tex_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating pipeline files in {output_dir.resolve()} with {rows} rows each...")

    db_paths = []
    db_paths.append(str(output_dir / f"banking_flat_C3_R{rows}.db"))
    generation.generate_flat_banking_db(
        nb_rows=rows,
        nb_cols=3,
        output_path=db_paths[-1]
    )

    db_paths.append(str(output_dir / f"banking_hierarchical_C3_R{rows}.db"))
    generation.generate_hierarchical_banking_db(
        nb_rows=rows,
        output_path=db_paths[-1],
        use_food_column=False
    )

    db_paths.append(str(output_dir / f"medical_flat_C3_R{rows}.db"))
    generation.generate_flat_medical_db(
        nb_rows=rows,
        nb_cols=3,
        output_path=db_paths[-1]
    )

    db_paths.append(str(output_dir / f"medical_hierarchical_C3_R{rows}.db"))
    generation.generate_hierarchical_medical_db(
        nb_rows=rows,
        output_path=db_paths[-1],
        use_food_column=False
    )

    print("\nGenerating LaTeX/TikZ files for all generated databases...")
    for db_path in db_paths:
        db_name = Path(db_path).stem
        dim_names = get_dim_names_for_db(db_name)
        try:
            tex_paths = generate_diagrams_for_db(
                db_path,
                str(tex_output_dir),
                dim_names=dim_names,
                measure_name="COUNT",
                style="both"
            )
            for tex_path in tex_paths:
                print(f"✅ LaTeX généré : {tex_path}")
        except Exception as exc:
            print(f"❌ Échec LaTeX pour {db_path} : {exc}")

        if "hierarchical" in db_name:
            hierarchy = get_hierarchy_for_db(db_name)
            if hierarchy and dim_names:
                try:
                    space_path = generate_multidimensional_space_for_db(
                        db_path,
                        str(tex_output_dir),
                        hierarchy,
                        dim_names
                    )
                    print(f"✅ Espace multidimensionnel LaTeX généré : {space_path}")
                except Exception as exc:
                    print(f"❌ Échec Espace multidimensionnel pour {db_path} : {exc}")

                try:
                    hasse_path = generate_hasse_diagram_for_db(
                        db_path,
                        str(tex_output_dir),
                        hierarchy,
                        dim_names
                    )
                    print(f"✅ Diagramme de Hasse LaTeX généré : {hasse_path}")
                except Exception as exc:
                    print(f"❌ Échec Diagramme de Hasse pour {db_path} : {exc}")

    print("\nAll temporary pipeline files generated successfully.")
    print("Databases:")
    for path in sorted(output_dir.glob("*.db")):
        print(f" - {path.name}")
    print("LaTeX files:")
    for path in sorted(tex_output_dir.glob("*.tex")):
        print(f" - {path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate the full temporary data pipeline files and LaTeX/TikZ exports under temp/."
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=5,
        help="Number of rows per generated DB file.",
    )
    parser.add_argument(
        "--output-dir",
        default="temp",
        help="Directory where generated DB files are written.",
    )
    parser.add_argument(
        "--tex-output-dir",
        default=None,
        help="Directory where generated LaTeX/TikZ files are written. Defaults to temp/tex.",
    )
    args = parser.parse_args()

    generate_full_temp_pipeline(
        Path(args.output_dir),
        rows=args.rows,
        tex_output_dir=Path(args.tex_output_dir) if args.tex_output_dir else None
    )
