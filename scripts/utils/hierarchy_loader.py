def get_default_hierarchy():
    return {
        "Geography": {
            "ALL": ["Europe", "Amérique", "Asie"],
            "Europe": ["France", "Allemagne", "Espagne", "Italie", "Belgique"],

            # Pays → Régions
            "France": ["Île-de-France", "PACA", "Hauts-de-France"],
            "Allemagne": ["Bavière", "Rhénanie"],
            "Espagne": ["Catalogne", "Andalousie"],
            "Italie": ["Lombardie", "Piémont"],
            "Belgique": ["Wallonie"],

            # Régions → Villes
            "Île-de-France": ["Paris", "Nanterre", "Versailles", "Boulogne-Billancourt", "Saint-Denis"],
            "PACA": ["Marseille", "Nice", "Toulon", "Avignon", "Aix-en-Provence"],
            "Hauts-de-France": ["Lille", "Amiens", "Roubaix", "Tourcoing", "Dunkerque"],
            "Bavière": ["Munich", "Nuremberg", "Augsbourg", "Würzburg", "Rosenheim"],
            "Rhénanie": ["Francfort", "Hambourg", "Strasbourg", "Mayence", "Trèves"],
            "Catalogne": ["Barcelone", "Girona", "Lleida", "Tarragone", "Manresa"],
            "Andalousie": ["Séville", "Grenade", "Cordoue", "Málaga", "Almería"],
            "Lombardie": ["Milan", "Bergame", "Brescia", "Côme", "Pavie"],
            "Piémont": ["Turin", "Alessandria", "Asti", "Cuneo", "Novare"],
            "Wallonie": ["Liège", "Namur", "Charleroi", "Mons", "La Louvière"]
        },

        "Time": {
            "ALL": ["2021", "2022", "2023", "2024"],
            "2021": ["2021-12", "2021-05"],
            "2022": ["2022-01", "2022-12", "2022-07", "2022-04"],
            "2023": ["2023-01", "2023-02", "2023-07", "2023-08", "2023-12", "2023-05", "2023-11"],
            "2024": ["2024-03", "2024-06", "2024-07"],

            # Mois → Jours
            "2021-05": ["2021-05-01"],
            "2021-12": ["2021-12-31"],
            "2022-01": ["2022-01-01"],
            "2022-04": ["2022-04-01"],
            "2022-07": ["2022-07-04"],
            "2022-12": ["2022-12-24", "2022-12-31"],
            "2023-01": ["2023-01-01", "2023-01-15"],
            "2023-02": ["2023-02-01", "2023-02-14"],
            "2023-05": ["2023-05-08"],
            "2023-07": ["2023-07-01"],
            "2023-08": ["2023-08-01", "2023-08-15"],
            "2023-11": ["2023-11-11"],
            "2023-12": ["2023-12-25"],
            "2024-03": ["2024-03-08"],
            "2024-06": ["2024-06-30"],
            "2024-07": ["2024-07-01", "2024-07-14", "2024-07-31"]
        },

        "Food": {
            "ALL": ["Fruits", "Légumes", "Viandes", "Produits laitiers", "Céréales"],
            "Fruits": ["Fruits rouges", "Agrumes"],
            "Légumes": ["Légumes verts", "Tubercules"],
            "Viandes": ["Viandes rouges", "Poissons"],
            "Produits laitiers": ["Fromages", "Yaourts"],
            "Céréales": ["Pâtes"],

            # Type → Produits
            "Fruits rouges": ["Fraise", "Framboise"],
            "Agrumes": ["Orange", "Citron"],
            "Légumes verts": ["Épinard", "Brocoli"],
            "Tubercules": ["Pomme de terre", "Carotte"],
            "Viandes rouges": ["Boeuf", "Poulet"],
            "Poissons": ["Saumon", "Thon"],
            "Fromages": ["Camembert", "Comté"],
            "Yaourts": ["Yaourt nature", "Yaourt aux fruits"],
            "Pâtes": ["Spaghetti", "Penne"]
        }
    }
