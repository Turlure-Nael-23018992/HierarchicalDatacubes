import itertools
import time

def powerset(iterable):
    """Toutes les combinaisons non vides des dimensions (brute force)"""
    s = list(iterable)
    return [combo for i in range(1, len(s)+1) for combo in itertools.combinations(s, i)]


def bruteForce(datas):
    """
    Baseline Brute Force Cubing Algorithm.

    Calculates every possible combination of dimensions (power set) and 
    performs a GROUP BY for each. Used for performance comparison only.

    Args:
        datas (DataFrame): Input data containing dimensions and measures.
    """

    # Lancement du chrono
    start_time = time.time()

    # Dimensions hiérarchiques
    dimensions = [
        ["année", "mois"],
        ["pays", "ville"]
    ]

    flat_dims = [col for group in dimensions for col in group]

    group_combinations = powerset(flat_dims)

    # Calcul de tous les group-by possibles
    results = []

    for group in group_combinations:
        grouped = datas.groupby(list(group)).agg({"ventes": "sum"}).reset_index()
        grouped["groupby_dims"] = [group] * len(grouped)
        results.append(grouped)

    # Fusion de tous les résultats
    #final_cube = pd.concat(results, ignore_index=True)

    #print(final_cube.head(10))

    print("========================")

    # Groupe par double dimensions
    #double_groupings = final_cube[final_cube['groupby_dims'].apply(lambda x: len(x) == 2)]

    #print(double_groupings.head(10))

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Durée d'exécution de l'algorithme de Brute force : {elapsed_time:.4f} secondes")