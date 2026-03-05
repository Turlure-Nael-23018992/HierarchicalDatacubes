import sqlite3
import random
import os
import re
from datetime import datetime
from itertools import product

class DataGenerator:

    def __init__(self, db_name="simple_generated.db"):
        self.db_name = db_name

    def generate_random_coded_db_dimensionJoueur(self, nb_lignes: int, db_name="dplayer_random_coded.db"):
        if os.path.exists(db_name):
            os.remove(db_name)

        headers = ["IdJoueur", "P", "R", "V", "A", "S", "N", "L", "J", "Localisation"]

        valid_values = {
            "P": [1],
            "R": [2, 9],
            "V": [3, 10],
            "A": [4, 11],
            "S": [5, 12, 16],
            "N": [6, 13, 17],
            "L": [7, 14, 18],
            "J": [8, 15, 19],
        }

        label_map = {
            "P": {1: "France"},
            "R": {2: "IDF", 9: "PACA"},
            "V": {3: "Paris", 10: "Marseille"},
            "A": {4: "92.88.91.80", 11: "139.124.242.125"},
            "S": {5: "Windows", 12: "Linux", 16: "Mac OS"},
            "N": {6: "Chrome", 13: "Opera", 17: "Firefox"},
            "L": {7: "fr", 14: "en", 18: "es"},
            "J": {8: "J₁", 15: "J₂", 19: "J₃"},
        }

        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        c.execute(f"""
            CREATE TABLE Pokemon (
                IdJoueur INTEGER,
                P INTEGER,
                R INTEGER,
                V INTEGER,
                A INTEGER,
                S INTEGER,
                N INTEGER,
                L INTEGER,
                J INTEGER,
                Localisation TEXT
            )
        """)

        keys = ["P", "R", "V", "A", "S", "N", "L", "J"]

        for i in range(1, nb_lignes + 1):
            row = [i]
            stop = False
            last_key = None
            last_val = None

            for key in keys:
                if stop or random.random() < 0.15:
                    row.append(None)
                    stop = True
                else:
                    val = random.choice(valid_values[key])
                    row.append(val)
                    last_key = key
                    last_val = val

            localisation = label_map.get(last_key, {}).get(last_val) if last_key else None
            row.append(localisation)

            placeholders = ", ".join("?" * len(row))
            c.execute(f"INSERT INTO Pokemon ({', '.join(headers)}) VALUES ({placeholders})", row)

        conn.commit()
        conn.close()
        print(f"✅ Base '{db_name}' générée avec succès avec {nb_lignes} lignes.")

    def generate_random_coded_db_dimensionTour(self, nb_lignes: int, db_name="dtour_coded.db"):
        if os.path.exists(db_name):
            os.remove(db_name)

        headers = ["IdTour", "Partie", "Manche", "Phase"]
        data = []
        current_id = 1
        partie_id = 1
        manche_id = 1

        while len(data) < nb_lignes:
            nb_manches = random.randint(1, 4)  # Entre 1 et 4 manches par partie
            for i in range(nb_manches):
                if len(data) >= nb_lignes:
                    break
                phase = f"P{partie_id}" if i == 0 else f"P{partie_id}-{i}"
                data.append([current_id, partie_id, manche_id, phase])
                current_id += 1
                manche_id += 1
            partie_id += 1

        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute(f"""
            CREATE TABLE Pokemon (
                {', '.join(f"{col} TEXT" if col == "Phase" else f"{col} INTEGER" for col in headers)}
            )
        """)
        for row in data:
            placeholders = ", ".join("?" * len(row))
            c.execute(f"INSERT INTO Pokemon ({', '.join(headers)}) VALUES ({placeholders})", row)

        conn.commit()
        conn.close()
        print(f"✅ {len(data)} lignes générées dans '{db_name}'.")

    def generate_random_coded_db_dimensionSerie(self, db_name="dserie_random_coded.db", nb_series=1, max_coups_per_serie=5, max_assoc_per_coup=5):
        if os.path.exists(db_name):
            os.remove(db_name)

        couleurs = ["rouge", "vert", "bleu"]
        tailles = ["3", "4", "5"]

        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        c.execute("""
                  CREATE TABLE Pokemon
                  (
                      IdSerie     INTEGER,
                      Coup        INTEGER,
                      Combinaison INTEGER,
                      Association TEXT,
                      Couleur     TEXT,
                      Taille      TEXT
                  )
                  """)

        id_serie = 1
        coup_num = 1
        combinaison_id = 2  # commence à 2 comme dans l'image

        for s in range(nb_series):
            nb_coups = random.randint(1, max_coups_per_serie)
            logical_coup_index = 1  # A1, A2, ...
            for _ in range(nb_coups):
                nb_assoc = random.randint(1, max_assoc_per_coup)

                for i in range(nb_assoc):
                    association = f"A{logical_coup_index}" if i == 0 else f"A{logical_coup_index}-{i}"
                    couleur = random.choice(couleurs)
                    taille = random.choice(tailles)

                    c.execute("""
                              INSERT INTO Pokemon (IdSerie, Coup, Combinaison, Association, Couleur, Taille)
                              VALUES (?, ?, ?, ?, ?, ?)
                              """, (id_serie, coup_num, id_serie, association, couleur, taille))

                    id_serie += 1
                    combinaison_id += 1

                coup_num += 1  # incrément de 1 à chaque nouveau coup
                logical_coup_index += 1

        conn.commit()
        conn.close()
        print(f"✅ Base '{db_name}' générée avec succès avec {id_serie - 1} lignes.")

    def generate_coded_db_dimensionJoueur(self, db_name="dimensionJoueur.db"):
        if os.path.exists(db_name):
            os.remove(db_name)

        # Dictionnaires de correspondance (selon image fournie)
        correspondances = {
            "P": {1: "France"},
            "R": {2: "IDF", 9: "PACA"},
            "V": {3: "Paris", 10: "Marseille"},
            "A": {4: "92.88.91.80", 11: "139.124.242.125"},
            "S": {5: "Windows", 12: "Linux", 16: "Mac OS"},
            "N": {6: "Chrome", 13: "Opera", 17: "Firefox"},
            "L": {7: "fr", 14: "en", 18: "es"},
            "J": {8: "J₁", 15: "J₂", 19: "J₃"}
        }

        coded_data = [
            [1, 1, None, None, None, None, None, None, None],
            [2, 1, 2, None, None, None, None, None, None],
            [3, 1, 2, 3, None, None, None, None, None],
            [4, 1, 2, 3, 4, None, None, None, None],
            [5, 1, 2, 3, 4, 5, None, None, None],
            [6, 1, 2, 3, 4, 5, 6, None, None],
            [7, 1, 2, 3, 4, 5, 6, 7, None],
            [8, 1, 2, 3, 4, 5, 6, 7, 8],
            [9, 1, 9, None, None, None, None, None, None],
            [10, 1, 9, 10, None, None, None, None, None],
            [11, 1, 9, 10, 11, None, None, None, None],
            [12, 1, 9, 10, 11, 12, None, None, None],
            [13, 1, 9, 10, 11, 12, 13, None, None],
            [14, 1, 9, 10, 11, 12, 13, 14, None],
            [15, 1, 9, 10, 11, 12, 13, 14, 15],
            [16, 1, 9, 10, 11, 16, None, None, None],
            [17, 1, 9, 10, 11, 16, 17, None, None],
            [18, 1, 9, 10, 11, 16, 17, 18, None],
            [19, 1, 9, 10, 11, 16, 17, 18, 19],
        ]

        headers = ["IdJoueur", "P", "R", "V", "A", "S", "N", "L", "J", "Localisation"]

        # Génération de la colonne Localisation selon la dernière valeur renseignée
        rows_with_localisation = []
        keys = ["P", "R", "V", "A", "S", "N", "L", "J"]
        for row in coded_data:
            localisation = "N/A"
            for i in reversed(range(1, len(row))):
                if row[i] is not None:
                    code = row[i]
                    key = keys[i - 1]
                    localisation = correspondances.get(key, {}).get(code, "N/A")
                    break
            rows_with_localisation.append(row + [localisation])

        # Création BDD
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        c.execute(f"""
            CREATE TABLE Pokemon (
                IdJoueur INTEGER,
                P INTEGER,
                R INTEGER,
                V INTEGER,
                A INTEGER,
                S INTEGER,
                N INTEGER,
                L INTEGER,
                J INTEGER,
                Localisation TEXT
            )
        """)

        for row in rows_with_localisation:
            c.execute(
                f"INSERT INTO Pokemon ({', '.join(headers)}) VALUES ({', '.join('?' * len(headers))})",
                row
            )

        conn.commit()
        conn.close()
        print(f"✅ Table '{db_name}' générée avec succès.")

    def generate_coded_db_dimensionTour(self, db_name="dtour_coded.db"):
        # Supprimer l'ancienne base si elle existe
        if os.path.exists(db_name):
            os.remove(db_name)

        # Données codées extraites de l’image (tableau 5.2)
        coded_data = [
            [1, 1, 1, "P₁"],
            [2, 1, 2, "P₁₋₁"],
            [3, 1, 3, "P₁₋₂"],
            [4, 4, 4, "P₂"],
            [5, 4, 5, "P₂₋₁"],
            [6, 4, 6, "P₂₋₂"],
            [7, 4, 7, "P₂₋₃"],
            [8, 8, 8, "P₃"],
            [9, 8, 9, "P₃₋₁"],
            [10, 8, 10, "P₃₋₂"],
            [11, 8, 11, "P₃₋₃"]
        ]

        headers = ["IdTour", "Partie", "Manche", "Phase"]

        # Connexion SQLite
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # Création de la table
        c.execute(f"""
            CREATE TABLE Pokemon (
                {', '.join(f"{col} TEXT" if col == "Phase" else f"{col} INTEGER" for col in headers)}
            )
        """)

        # Insertion des données
        for row in coded_data:
            placeholders = ", ".join("?" * len(row))
            c.execute(f"INSERT INTO Pokemon ({', '.join(headers)}) VALUES ({placeholders})", row)

        conn.commit()
        conn.close()
        print(f"✅ Table '{db_name}' générée avec succès avec {len(coded_data)}.")

    def generate_coded_db_dimensionSerie(self, db_name="dserie_coded.db"):
        if os.path.exists(db_name):
            os.remove(db_name)

        # Données codées exactement comme sur le tableau de l'image
        coded_data = [
            # IdSérie, Coup, Combinaison, Association, Couleur, Taille
            [1, 1, None, "A₁", None, None],
            [2, 1, 2, "A₁₋₁", "rouge", 3],
            [3, 1, 3, "A₁₋₂", "bleu", 3],
            [4, 4, None, "A₂", None, None],
            [5, 4, 5, "A₂₋₁", "vert", 4],
            [6, 4, 6, "A₂₋₂", "jaune", 3],
            [7, 4, 7, "A₂₋₃", "rouge", 3],
            [8, 4, 8, "A₂₋₄", "bleu", 3],
            [9, 4, 9, "A₂₋₅", "jaune", 3],
            [10, 4, 10, "A₂₋₆", "vert", 4],
            [11, 11, None, "A₃", None, None],
            [12, 11, 12, "A₃₋₁", "vert", 3],
            [13, 11, 13, "A₃₋₂", "rouge", 3],
            [14, 11, 14, "A₃₋₃", "rouge", 4],
            [15, 11, 15, "A₃₋₄", "vert", 3],
            [16, 11, 16, "A₃₋₅", "jaune", 4],
            [17, 11, 17, "A₃₋₆", "jaune", 3],
            [18, 11, 18, "A₃₋₇", "jaune", 3],
            [19, 19, None, "A₄", None, None],
            [20, 19, 20, "A₄₋₁", "vert", 3],
            [21, 21, None, "A₅", None, None],
            [22, 21, 22, "A₅₋₁", "rouge", 3],
            [23, 23, None, "A₆", None, None],
            [24, 23, 24, "A₆₋₁", "vert", 5],
            [25, 25, None, "A₇", None, None],
            [26, 25, 26, "A₇₋₁", "jaune", 3],
            [27, 25, 27, "A₇₋₂", "jaune", 3],
            [28, 25, 28, "A₇₋₃", "rouge", 3],
            [29, 25, 29, "A₇₋₄", "rouge", 3],
            [30, 25, 30, "A₇₋₅", "jaune", 4],
            [31, 25, 31, "A₇₋₆", "rouge", 4],
            [32, 25, 32, "A₇₋₇", "vert", 3],
            [33, 25, 33, "A₇₋₈", "jaune", 3],
            [34, 25, 34, "A₇₋₉", "jaune", 3],
            [35, 25, 35, "A₇₋₁₀", "vert", 3],
            [36, 25, 36, "A₇₋₁₁", "vert", 4],
            [37, 25, 37, "A₇₋₁₂", "bleu", 3],
        ]

        headers = ["IdSerie", "Coup", "Combinaison", "Association", "Couleur", "Taille"]

        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # Création de la table
        c.execute(f"""
            CREATE TABLE Pokemon (
                IdSerie INTEGER,
                Coup INTEGER,
                Combinaison INTEGER,
                Association TEXT,
                Couleur TEXT,
                Taille INTEGER
            )
        """)

        for row in coded_data:
            placeholders = ", ".join("?" for _ in row)
            c.execute(f"INSERT INTO Pokemon ({', '.join(headers)}) VALUES ({placeholders})", row)

        conn.commit()
        conn.close()
        print(f"✅ Table '{db_name}' générée avec succès avec {len(coded_data)} lignes.")

    def generate_faitom3_from_dimensions(self, dict_joueur, dict_tour, dict_serie, db_name="faitom3_from_dims.db"):
        # 1. Supprimer l'ancien fichier si besoin
        if os.path.exists(db_name):
            os.remove(db_name)

        # 2. Ouvrir la connexion
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # 3. Créer la table
        c.execute("""
                  CREATE TABLE Pokemon
                  (
                      RowId  INTEGER,
                      IdJ    TEXT,
                      IdT    TEXT,
                      IdS    TEXT,
                      Temps  REAL,
                      Durée  REAL,
                      Nombre REAL,
                      Score  INTEGER,
                      Forme  REAL
                  )
                  """)

        # 4. Identifier dynamiquement les IDs par leur nom
        def find_key_by_label(d, label_idx, target_value):
            for k, v in d.items():
                if v[label_idx] == target_value:
                    return k
            raise ValueError(f"{target_value} not found")

        # Joueurs
        idj1 = find_key_by_label(dict_joueur, -1, "J₁")
        fr = find_key_by_label(dict_joueur, -1, "fr")
        idj2 = find_key_by_label(dict_joueur, -1, "J₂")
        idj3 = find_key_by_label(dict_joueur, -1, "J₃")

        # Tours
        idt1 = find_key_by_label(dict_tour, -1, "P₁")
        idt2 = find_key_by_label(dict_tour, -1, "P₂")
        idt3 = find_key_by_label(dict_tour, -1, "P₃")

        # Séries
        ids1 = find_key_by_label(dict_serie, 2, "A₁")
        ids2 = find_key_by_label(dict_serie, 2, "A₂")
        ids3 = find_key_by_label(dict_serie, 2, "A₃")
        ids4 = find_key_by_label(dict_serie, 2, "A₄")
        ids5 = find_key_by_label(dict_serie, 2, "A₅")
        ids6 = find_key_by_label(dict_serie, 2, "A₆")
        ids7 = find_key_by_label(dict_serie, 2, "A₇")

        # 5. Contenu du tableau à insérer
        facts = [
            (1, idj1, idt1, ids1, 6.32, 2.85, 3.5, 700, 0.5),
            (2, fr, idt1, ids2, 18.9, 1.95, 3.83, 2300, 0.5),
            (3, idj2, idt2, ids3, 26.39, 1.7, 3.43, 2400, 0.71),
            (4, idj2, idt2, ids4, 4.1, 2.07, 3.0, 300, 0.5),
            (5, idj2, idt2, ids5, 7.38, 3.68, 3.0, 600, 0.5),
            (6, idj3, idt3, ids6, 2.14, 2.15, 3.0, 300, 1.0),
            (7, idj3, idt3, ids7, 56.04, 2.25, 3.17, 3800, 0.5),
        ]

        # 6. Insérer dans la BDD
        for row_id, idj, idt, ids, temps, duree, nombre, score, forme in facts:
            c.execute("""
                      INSERT INTO Pokemon (RowId, IdJ, IdT, IdS, Temps, Durée, Nombre, Score, Forme)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                      """, (
                          row_id,
                          dict_joueur[idj][-1],
                          dict_tour[idt][-1],
                          dict_serie[ids][2],
                          temps,
                          duree,
                          nombre,
                          score,
                          forme
                      ))

        conn.commit()
        conn.close()
        print(f"✅ Table des faits '{db_name}' générée à partir des dimensions.")


    def generate_fact_table_faitom3(self, db_name="faitom3.db"):
        if os.path.exists(db_name):
            os.remove(db_name)

        # Connexion
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # Création table
        c.execute("""
                  CREATE TABLE Pokemon
                  (
                      RowId  INTEGER PRIMARY KEY,
                      IdJ    TEXT,
                      IdT    TEXT,
                      IdS    TEXT,
                      Temps  REAL,
                      Duree  REAL,
                      Nombre REAL,
                      Score  INTEGER,
                      Forme  REAL
                  )
                  """)

        # Données en dur issues du tableau
        data = [
            (1, "J1", "P1", "A1", 6.32, 2.85, 3.5, 700, 0.5),
            (2, "J1", "P1", "A2", 18.9, 1.95, 3.83, 2300, 0.5),
            (3, "J2", "P2", "A3", 26.39, 1.7, 3.43, 2400, 0.71),
            (4, "J2", "P2", "A4", 4.1, 2.07, 3, 300, 0.5),
            (5, "J2", "P2", "A5", 7.38, 3.68, 3.68, 600, 0.5),
            (6, "J3", "P3", "A6", 2.14, 2.15, 3, 300, 1),
            (7, "J3", "P3", "A7", 56.04, 2.25, 3.17, 3800, 0.5),
        ]

        c.executemany("""
                      INSERT INTO Pokemon (RowId, IdJ, IdT, IdS, Temps, Duree, Nombre, Score, Forme)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                      """, data)

        conn.commit()
        conn.close()
        print(f"✅ Table 'FaitOM3' créée avec {len(data)} lignes dans '{db_name}'.")

    def generate_dplayer_real_db(self, nb_lignes: int, db_name="dplayer_real.db"):
        if os.path.exists(db_name):
            os.remove(db_name)

        # Hiérarchie simulée
        hierarchy = {
            "France": {
                "PACA": ["Marseille", "Nice", "Fréjus"],
                "IDF": ["Paris", "Boulogne", "Nanterre"]
            },
            "Japon": {
                "Kanto": ["Tokyo", "Yokohama"],
                "Kansai": ["Osaka", "Kyoto"]
            },
            "USA": {
                "California": ["Los Angeles", "San Francisco"],
                "Texas": ["Dallas", "Houston"]
            }
        }

        systems = ["Windows", "Linux", "macOS"]
        browsers = ["Chrome", "Firefox", "Edge", "Safari"]
        languages = ["fr", "en", "jp"]

        # Connexion SQLite
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # Création de la table
        c.execute("""
                  CREATE TABLE Pokemon
                  (
                      IdJoueur   INTEGER PRIMARY KEY,
                      Pays       TEXT,
                      Region     TEXT,
                      Ville      TEXT,
                      AdresseIP  TEXT,
                      Systeme    TEXT,
                      Navigateur TEXT,
                      Langue     TEXT
                  )
                  """)

        for i in range(1, nb_lignes + 1):
            pays = random.choice(list(hierarchy.keys()))
            region = random.choice(list(hierarchy[pays].keys()))
            ville = random.choice(hierarchy[pays][region])
            ip = f"{random.randint(10, 250)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
            systeme = random.choice(systems)
            navigateur = random.choice(browsers)
            langue = random.choice(languages)

            row = (i, pays, region, ville, ip, systeme, navigateur, langue)
            c.execute("INSERT INTO Pokemon VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row)

        conn.commit()
        conn.close()
        print(f"✅ Base '{db_name}' générée avec {nb_lignes} lignes.")

    def generate_db_hierarchy(self, nb_lignes: int, nb_colonnes: int):
        if nb_colonnes not in (3, 6, 9):
            raise ValueError("Le nombre de colonnes doit être 3, 6 ou 9")

        if os.path.exists(self.db_name):
            os.remove(self.db_name)

        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()

        if nb_colonnes == 3:
            columns = ["Region", "Departement", "Ville"]
        elif nb_colonnes == 6:
            columns = ["Region", "Departement", "Ville", "Annee", "Mois", "Jour"]
        else:
            columns = ["Region", "Departement", "Ville", "Annee", "Mois", "Jour", "Generation", "Type", "NomPokemon"]

        columns_sql = ", ".join([f"{col} TEXT" for col in columns])
        c.execute(f"CREATE TABLE Pokemon (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_sql})")

        # Hiérarchie géographique
        regions = {
            "Ile-de-France": ["75", "92", "93"],
            "Bretagne": ["29", "56"],
            "PACA": ["13", "83"]
        }
        villes = {
            "75": ["Paris"],
            "92": ["Nanterre", "Boulogne"],
            "93": ["Montreuil", "Rosny"],
            "29": ["Brest", "Morlaix"],
            "56": ["Lorient", "Pontivy"],
            "13": ["Marseille", "Aubagne"],
            "83": ["Toulon", "Hyeres"]
        }

        # Dates
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 5, current_year + 1)]
        months = [str(m).zfill(2) for m in range(1, 13)]
        days = [str(d).zfill(2) for d in range(1, 29)]

        # Hiérarchie Pokémon à remplir
        generations = {
            "G1": {
                "Feu": ["Salameche", "Ponyta"],
                "Eau": ["Carapuce", "Magicarpe"],
                "Plante": ["Bulbizarre", "Chetiflor"]
            },
            "G2": {
                "Feu": ["Hericendre", "Limagma"],
                "Eau": ["Kaiminus", "Marill"],
                "Plante": ["Germinion", "Joliflor"]
            },
            "G3": {
                "Feu": ["Poussifeu", "Chartor"],
                "Eau": ["Gobou", "Wailmer"],
                "Plante": ["Arcko", "Cacnea"]
            }
        }

        for _ in range(nb_lignes):
            row = []

            # Géographique
            region = random.choice(list(regions.keys()))
            departement = random.choice(regions[region])
            ville = random.choice(villes[departement])
            row.extend([region, departement, ville])

            # Date
            if nb_colonnes >= 6:
                annee = random.choice(years)
                mois = random.choice(months)
                jour = random.choice(days)
                row.extend([annee, mois, jour])

            # Pokémon
            if nb_colonnes == 9:
                generation = random.choice(list(generations.keys()))
                type_poke = random.choice(list(generations[generation].keys()))
                nom_poke = random.choice(generations[generation][type_poke])
                row.extend([generation, type_poke, nom_poke])

            placeholders = ", ".join("?" * len(row))
            c.execute(f"INSERT INTO Pokemon ({', '.join(columns)}) VALUES ({placeholders})", row)

        conn.commit()
        conn.close()
        print(f"DB '{self.db_name}' créée avec {nb_lignes} lignes et {nb_colonnes} colonnes dans la table 'Pokemon'.")

    def generatePokemonFactTable(self, isDetailed=False):
        import os, sqlite3, random

        correspondanceDimJoueur = {
            1: "France", 2: "IDF", 3: "Paris", 4: "92.88.91.80", 5: "Windows",
            6: "Chrome", 7: "fr", 8: "J1", 9: "PACA", 10: "Marseille",
            11: "139.124.242.125", 12: "Linux", 13: "Opera", 14: "en",
            15: "J2", 16: "Mac OS", 17: "Firefox", 18: "es", 19: "J3"
        }

        correspondanceDimTour = {
            1: "S1", 2: "S1-1", 3: "S1-2", 4: "S2", 5: "S2-1", 6: "S2-2",
            7: "S2-3", 8: "S3", 9: "S3-1", 10: "S3-2", 11: "S3-3"
        }

        correspondanceDimSerie = {
            1: ("A1", None, None), 2: ("A1-1", "red", 3), 3: ("A1-2", "blue", 3),
            4: ("A2", None, None), 5: ("A2-1", "green", 4), 6: ("A2-2", "yellow", 3),
            7: ("A2-3", "red", 3), 8: ("A2-4", "blue", 3), 9: ("A2-5", "yellow", 3),
            10: ("A2-6", "green", 4), 11: ("A3", None, None), 12: ("A3-1", "green", 3),
            13: ("A3-2", "red", 3), 14: ("A3-3", "red", 4), 15: ("A3-4", "green", 3),
            16: ("A3-5", "yellow", 3), 17: ("A3-6", "yellow", 3), 18: ("A3-7", "yellow", 3),
            19: ("A4", None, None), 20: ("A4-1", "green", 3), 21: ("A5", None, None),
            22: ("A5-1", "red", 3), 23: ("A6", None, None), 24: ("A6-1", "green", 5),
            25: ("A7", None, None), 26: ("A7-1", "yellow", 3), 27: ("A7-2", "yellow", 3),
            28: ("A7-3", "red", 3), 29: ("A7-4", "red", 3), 30: ("A7-5", "yellow", 3),
            31: ("A7-6", "red", 4), 32: ("A7-7", "green", 3), 33: ("A7-8", "yellow", 3),
            34: ("A7-9", "yellow", 3), 35: ("A7-10", "green", 4), 36: ("A7-11", "green", 4),
            37: ("A7-12", "blue", 3)
        }

        hierarchy_paths = {
            8: [1, 2, 3, 4, 5, 6, 7, 8],
            15: [1, 9, 10, 11, 12, 13, 14, 15],
            19: [1, 9, 10, 11, 16, 17, 18, 19]
        }

        base_combinations = {
            8: [(1, 1), (1, 4)],
            15: [(4, 10), (4, 17), (4, 19)],
            19: [(8, 20), (8, 21)]
        }

        def get_label(id_val, dim):
            if dim == "Joueur":
                return correspondanceDimJoueur.get(id_val, f"J_{id_val}") if isDetailed else id_val
            elif dim == "Tour":
                return correspondanceDimTour.get(id_val, f"T_{id_val}") if isDetailed else id_val
            elif dim == "Serie":
                return correspondanceDimSerie.get(id_val, (f"S_{id_val}", None, None))[0] if isDetailed else id_val

        def get_sub_elements(label, label_dict):
            results = []
            for k, v in label_dict.items():
                name = v[0] if isinstance(v, tuple) else v
                if name == label or name.startswith(label + "-"):
                    results.append(k)
            return results

        def resolve_size(label, serie_dict):
            for k, (name, _, size) in serie_dict.items():
                if name == label:
                    if size is not None:
                        return size
                    for sk, (sublabel, _, ssize) in serie_dict.items():
                        if sublabel.startswith(label + "-") and ssize is not None:
                            return ssize
            return 3

        def tirage_duree():
            r = random.random()
            if r < 0.7:
                return round(random.uniform(1.0, 3.0), 2)
            elif r < 0.8:
                return round(random.uniform(0.1, 1.0), 2)
            elif r < 0.9:
                return round(random.uniform(3.0, 6.0), 2)
            else:
                return round(random.uniform(6.0, 15.0), 2)

        db_path = "Pokemon.db"
        if os.path.exists(db_path):
            os.remove(db_path)

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("DROP TABLE IF EXISTS Pokemon")
        cur.execute("""
                    CREATE TABLE Pokemon
                    (
                        IdP      TEXT,
                        IdT      TEXT,
                        IdS      TEXT,
                        Time     REAL,
                        Duration REAL,
                        Number   REAL,
                        Score    INTEGER,
                        Shape    REAL
                    )
                    """)

        rows = []
        time_per_idt = {}
        sub_idt_map = {}

        for idt, label in correspondanceDimTour.items():
            if '-' in label:
                time_per_idt[label] = round(random.uniform(1.0, 90.0), 2)
                top = label.split('-')[0]
                sub_idt_map.setdefault(top, []).append(label)

        for parent_label, children in sub_idt_map.items():
            times = [time_per_idt[c] for c in children]
            time_per_idt[parent_label] = min(times)

        duration_by_move = {}
        for k, (move, _, _) in correspondanceDimSerie.items():
            if '-' not in move:
                duration_by_move[move] = tirage_duree()

        score_by_combination = {}
        for k, (label, _, size) in correspondanceDimSerie.items():
            if size:
                score_by_combination[label] = {3: 300, 4: 500, 5: 800}.get(size, 0)

        score_by_move = {}
        for label, score in score_by_combination.items():
            move = label.split("-")[0]
            score_by_move[move] = score_by_move.get(move, 0) + score

        # ⬇️ Nouvelle étape : Shape par Move
        shape_by_move = {}
        for k, (label, _, _) in correspondanceDimSerie.items():
            if '-' not in label:
                shape_by_move[label] = random.choice([0.5, 1.0])

        for idj_final, path in hierarchy_paths.items():
            for idj in path:
                for idt_init, ids_init in base_combinations[idj_final]:
                    label_t = correspondanceDimTour[idt_init]
                    label_s = correspondanceDimSerie[ids_init][0]

                    valid_idts = get_sub_elements(label_t, correspondanceDimTour)
                    valid_idss = get_sub_elements(label_s, correspondanceDimSerie)

                    for idt in valid_idts:
                        idt_label = get_label(idt, "Tour")
                        temps = time_per_idt.get(idt_label, round(random.uniform(1.0, 90.0), 2))

                        for ids in valid_idss:
                            label_serie = correspondanceDimSerie[ids][0]
                            move = label_serie.split("-")[0]
                            duree = duration_by_move.get(move, tirage_duree())
                            nombre = resolve_size(label_serie, correspondanceDimSerie)
                            score = score_by_combination.get(label_serie, score_by_move.get(label_serie, 0))
                            forme = shape_by_move.get(move, random.choice([0.5, 1.0]))

                            rows.append((
                                get_label(idj, "Joueur"),
                                idt_label,
                                label_serie if isDetailed else ids,
                                temps,
                                duree,
                                nombre,
                                score,
                                forme
                            ))

        cur.executemany("""
                        INSERT INTO Pokemon (IdP, IdT, IdS, Time, Duration, Number, Score, Shape)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, rows)

        conn.commit()
        conn.close()

        print(f"✅ Table 'Pokemon' générée avec {len(rows)} lignes dans : {os.path.abspath(db_path)}")

    def generate_hierarchical_facts_db(self, nb_lignes: int):
        """
        Génère une base .db avec 3 colonnes hiérarchiques (Géographie, Temps, Pokémon)
        contenant des valeurs de différents niveaux hiérarchiques.

        :param nb_lignes: Nombre de lignes à insérer dans la table
        """

        db_name = f"hierarchie_db_C3_R{nb_lignes}.db"

        if os.path.exists(db_name):
            os.remove(db_name)

        geo_values = [
            # Pays
            "France", "Allemagne", "Espagne", "Italie", "Belgique",

            # Régions
            "Île-de-France", "PACA", "Hauts-de-France",
            "Bavière", "Rhénanie", "Catalogne", "Andalousie",
            "Lombardie", "Piémont", "Wallonie",

            # Villes
            "Paris", "Nanterre", "Versailles", "Boulogne-Billancourt", "Saint-Denis",
            "Marseille", "Nice", "Toulon", "Avignon", "Aix-en-Provence",
            "Lille", "Amiens", "Roubaix", "Tourcoing", "Dunkerque",

            "Munich", "Nuremberg", "Augsbourg", "Würzburg", "Rosenheim",
            "Francfort", "Hambourg", "Strasbourg", "Mayence", "Trèves",

            "Barcelone", "Girona", "Lleida", "Tarragone", "Manresa",
            "Séville", "Grenade", "Cordoue", "Málaga", "Almería",

            "Milan", "Bergame", "Brescia", "Côme", "Pavie",
            "Turin", "Alessandria", "Asti", "Cuneo", "Novare",

            "Liège", "Namur", "Charleroi", "Mons", "La Louvière"
        ]

        time_values = [
            # Années
            "2021", "2022", "2023", "2024",

            # Mois
            "2021-12", "2022-01", "2022-12", "2023-01", "2023-02", "2023-07", "2023-08", "2024-03", "2024-06",
            "2024-07",

            # Jours
            "2021-12-31", "2022-01-01", "2022-12-24", "2022-12-31", "2023-01-01", "2023-01-15",
            "2023-02-01", "2023-02-14", "2023-07-01", "2023-08-01", "2023-08-15", "2024-03-08",
            "2024-06-30", "2024-07-01", "2024-07-14", "2024-07-31", "2023-12-25", "2022-07-04", "2021-05-01",
            "2023-05-08", "2023-11-11", "2022-04-01"
        ]

        food_values = [
            # Catégories
            "Fruits", "Légumes", "Céréales", "Viandes", "Produits laitiers",

            # Types
            "Fruits rouges", "Agrumes", "Légumes verts", "Tubercules", "Viandes rouges", "Poissons", "Fromages",
            "Yaourts", "Pâtes",

            # Produits
            "Fraise", "Framboise", "Orange", "Citron", "Épinard", "Brocoli", "Pomme de terre", "Carotte",
            "Boeuf", "Poulet", "Saumon", "Thon", "Camembert", "Comté", "Yaourt nature", "Yaourt aux fruits",
            "Spaghetti", "Penne"
        ]

        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        c.execute("""
                  CREATE TABLE IF NOT EXISTS Pokemon
                  (
                      Geography
                      TEXT,
                      Time
                      TEXT,
                      Food
                      TEXT
                  )
                  """)

        for _ in range(nb_lignes):
            geo = random.choice(geo_values)
            time = random.choice(time_values)
            food = random.choice(food_values)

            c.execute("INSERT INTO Pokemon (Geography, Time, Food) VALUES (?, ?, ?)",
                      (geo, time, food))

        conn.commit()
        conn.close()
        print(f"✅ Base '{db_name}' générée avec {nb_lignes} lignes (sans mesure).")


if __name__ == "__main__":
    dg = DataGenerator()
    dg.generate_hierarchical_facts_db(10)