"""
merge_timings.py
----------------
Fusionne les fichiers JSON de benchmarks (un par algorithme) stockés dans
Assets/ExecutionTime/<AlgoName>/c3.json vers un fichier temporaire unique
au format attendu par UniversalLatexGenerator.

Format source (c3.json) :
{
    "time_data": {
        "<cardinality>": [<time_seconds>, ...]
    },
    ...
}

Format cible (timings_merged.json) :
{
    "<AlgoName>": {
        "<AlgoName>_R<cardinality>": {
            "success": true,
            "duration_seconds": <moyenne des temps>
        }
    }
}
"""

import json
import os
import tempfile

# Chemin vers le dossier contenant les sous-dossiers par algorithme
EXECUTION_TIME_DIR = os.path.join(
    os.path.dirname(__file__),  # scripts/databaseManagement/
    "..", "..",                  # remonte à la racine du projet
    "Assets", "ExecutionTime"
)


def merge_timings(execution_time_dir: str = EXECUTION_TIME_DIR,
                  output_path: str = None) -> str:
    """
    Parcourt chaque sous-dossier d'algorithme, lit son c3.json,
    et construit le dictionnaire fusionné.

    Parameters
    ----------
    execution_time_dir : str
        Chemin vers le dossier Assets/ExecutionTime
    output_path : str | None
        Chemin de sortie. Si None, un fichier temporaire est créé.

    Returns
    -------
    str
        Chemin vers le fichier JSON fusionné.
    """
    merged = {}

    execution_time_dir = os.path.abspath(execution_time_dir)

    for algo_name in sorted(os.listdir(execution_time_dir)):
        algo_dir = os.path.join(execution_time_dir, algo_name)
        json_path = os.path.join(algo_dir, "c3.json")

        if not os.path.isdir(algo_dir) or not os.path.isfile(json_path):
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        time_data = data.get("time_data", {})
        algo_dict = {}

        for cardinality_str, times in time_data.items():
            if not times:
                continue
            avg_time = sum(times) / len(times)
            db_key = f"{algo_name}_R{cardinality_str}"
            algo_dict[db_key] = {
                "success": True,
                "duration_seconds": avg_time
            }

        if algo_dict:
            merged[algo_name] = algo_dict
            print(f"  ✅ {algo_name} : {len(algo_dict)} point(s) chargé(s)")
        else:
            print(f"  ⚠️  {algo_name} : aucune donnée valide")

    # Écriture dans le fichier de sortie
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix="_timings_merged.json",
            delete=False, encoding="utf-8"
        )
        output_path = tmp.name
        json.dump(merged, tmp, indent=2, ensure_ascii=False)
        tmp.close()
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Fichier fusionné : {output_path}")
    return output_path


if __name__ == "__main__":
    import sys

    # Optionnel : passer un chemin de sortie en argument
    out = sys.argv[1] if len(sys.argv) > 1 else None
    merged_path = merge_timings(output_path=out)

    # Lancer directement la génération LaTeX après la fusion
    try:
        from UniversalLatexGenerator import UniversalLatexGenerator

        output_folder = os.path.join(
            os.path.dirname(__file__), "..", "output"
        )
        os.makedirs(output_folder, exist_ok=True)

        gen = UniversalLatexGenerator()
        gen.generate_graphs_from_json(
            json_path=merged_path,
            output_folder=output_folder
        )
        print(f"Graphes LaTeX générés dans : {os.path.abspath(output_folder)}")
    except Exception as e:
        print(f"Génération LaTeX ignorée : {e}")
