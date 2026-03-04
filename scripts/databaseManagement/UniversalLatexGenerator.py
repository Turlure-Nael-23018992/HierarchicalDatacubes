import math
import json
import os
import re


class UniversalLatexGenerator:
    def __init__(self, output_path=None):
        self.colors = ["blue", "cyan", "red", "orange", "green"]
        self.markers = ["*", "o", "square*", "x", "+"]
        self.output_path = output_path

    def generate_graphs_from_json(self, json_path, output_folder):
        """
        Charge les données depuis un fichier JSON et génère des graphes LaTeX
        pour différentes configurations d'algorithmes.
        """
        with open(json_path, "r") as f:
            raw_data = json.load(f)

        def extract_cardinality(name):
            """Extrait la cardinalité du nom de la base de données."""
            match = re.search(r"_R(\d+)", name)
            return int(match.group(1)) if match else None

        # Paramètres communs pour tous les graphes (conformément à BUC_vs_HBUC)
        common_plot_options = {
            "y_mode": "LinY",
            "custom_ylim": (0, 2000),
            "custom_yticks": [0, 399, 800, 1199, 1599, 2000],
            "add_y_custom_trafo": True,
            "y_trafo_power": 0.43,
            "y_trafo_epsilon": 1e-9,
            "add_xlabel_suffix": False, # Désactiver la notation scientifique pour l'axe X
            "xlabel_offset": -0.1 # Décalage pour l'étiquette "Cardinality"
        }

        # Définition des groupes d'algorithmes et de leurs options de traçage
        # Chaque tuple contient (nom_fichier_latex, liste_algos, dictionnaire_options)
        algo_groups = [
            ("BUC_SC_Cl_noH.tex", ["BUC", "StarCubing", "ClosetCube"], {
                **common_plot_options, # Appliquer les options communes
                "x_mode": "LogX",
                "custom_xticks": [1000, 10000, 100000, 1000000, 5000000, 10000000, 50000000, 100000000],
                "title": "Performance of BUC, StarCubing, and ClosetCube (No Hierarchy)" # Titre générique
            }),
            ("BUC_SC_Cl_withH.tex", ["HierarchicalBUC", "HierarchicalStarCubing", "HierarchicalClosetCube"], {
                **common_plot_options, # Appliquer les options communes
                "x_mode": "LogX",
                "custom_xticks": [1000, 10000, 100000, 1000000, 5000000, 10000000, 50000000, 100000000],
                "title": "Performance of Hierarchical BUC, StarCubing, and ClosetCube" # Titre générique
            }),
            # Configuration pour le graphique BUC_vs_HBUC.tex (déjà aligné avec common_plot_options)
            ("BUC_vs_HBUC.tex", ["BUC", "HierarchicalBUC"], {
                **common_plot_options, # Appliquer les options communes
                "x_mode": "LogX",
                "custom_xticks": [1000, 10000, 100000, 1000000, 5000000, 10000000, 50000000, 100000000],
                "title": "Performance of BUC vs Hierarchical BUC" # Titre spécifique
            }),
            ("SC_vs_HSC.tex", ["StarCubing", "HierarchicalStarCubing"], {
                **common_plot_options, # Appliquer les options communes
                "x_mode": "LogX",
                "custom_xticks": [1000, 10000, 100000, 1000000, 5000000, 10000000, 50000000, 100000000],
                "title": "Performance of StarCubing vs Hierarchical StarCubing" # Titre générique
            }),
            ("Cl_vs_HCl.tex", ["ClosetCube", "HierarchicalClosetCube"], {
                **common_plot_options, # Appliquer les options communes
                "x_mode": "LogX",
                "custom_xticks": [1000, 10000, 100000, 1000000, 5000000, 10000000, 50000000, 100000000],
                "title": "Performance of ClosetCube vs Hierarchical ClosetCube" # Titre générique
            }),
            # CoSky_RankSky_Example.tex garde son x_mode LinX et ses xticks spécifiques
            ("CoSky_RankSky_Example.tex", ["CoSky_SQL_query", "CoSky_algorithm", "RankSky"], {
                "y_mode": "LinY",
                "x_mode": "LinX", # Reste linéaire car les valeurs sont mieux adaptées pour ça
                "custom_ylim": (0, 2200), # Légèrement différent en Y pour s'adapter à ses données
                "custom_yticks": [0, 400, 800, 1200, 1600, 2000],
                "custom_xticks": [0, 40000, 80000, 120000, 160000, 200000],
                "add_xlabel_suffix": False,
                "add_y_custom_trafo": False, # Pas de transformation Y pour ce graphe
                "title": "CoSky and RankSky Performance (3 attributes)",
                "xlabel_offset": -0.15
            }),
        ]

        for filename, algos, plot_options in algo_groups:
            timeDicts = []
            maxCard = 0

            for algo in algos:
                d = {}
                for db_name, stats in raw_data.get(algo, {}).items():
                    if not stats.get("success", False):
                        continue
                    card = extract_cardinality(db_name)
                    time = stats.get("duration_seconds", None)
                    if card and time is not None:
                        d[card] = time
                        maxCard = max(maxCard, card)
                timeDicts.append(d)

            self.output_path = os.path.join(output_folder, filename)
            self.generate_latex(
                timeDicts,
                algos,
                max_cardinality_for_x_lim=maxCard,
                **plot_options
            )

    def generate_latex(self, timeDicts, algos, y_mode="LinY", x_mode="LogX",
                       custom_ylim=None, custom_yticks=None, custom_xticks=None,
                       max_cardinality_for_x_lim=None, add_xlabel_suffix=False,
                       add_y_custom_trafo=False, y_trafo_power=0.43, y_trafo_epsilon=1e-9,
                       title=None, xlabel_offset=-0.1): # Ajout de xlabel_offset comme paramètre
        """
        Génère le code LaTeX pour un graphique PGFPlots.
        """
        is_log_y = y_mode == "LogY"
        is_log_x = x_mode == "LogX"

        lines = [
            r"\documentclass{standalone}",
            r"\usepackage{pgfplots}",
            r"\pgfplotsset{compat=1.18}",
            r"\usepackage{xcolor}",
            r"\begin{document}",
            r"\begin{tikzpicture}",
            r"\begin{axis}[",
            r"xlabel={Cardinality},",
            r"ylabel={Response time (s)},",
        ]

        # Ajout du titre du graphique s'il est fourni
        if title:
            lines.append(f"title={{{title}}},")
            lines.append(r"title style={yshift=0.7em},")

        # Gérer la transformation de l'axe Y si activée
        if add_y_custom_trafo:
            lines.append(r"ymode=linear,")
            y_min_for_trafo = custom_ylim[0] if custom_ylim else 0
            y_max_for_trafo = custom_ylim[1] if custom_ylim else 2000

            inv_y_trafo_power = 1 / y_trafo_power

            lines.append(
                f"y coord trafo/.code={{ \\pgfmathparse{{ (max(#1, {y_trafo_epsilon})/{y_max_for_trafo})^{y_trafo_power} }} \\pgfmathresult }},")
            lines.append(
                f"y coord inv trafo/.code={{ \\pgfmathparse{{ (max(#1, {y_trafo_epsilon})^{inv_y_trafo_power}) * {y_max_for_trafo} }} \\pgfmathresult }},")

            lines.append(f"ymin={y_min_for_trafo}, ymax={y_max_for_trafo},")

            lines.append(r"y label style={at={(axis description cs:-0.1,0.5)},anchor=center},")
            lines.append(r"yticklabel style={/pgf/number format/fixed, /pgf/number format/precision=0},")

            if custom_yticks:
                yticks_str = ",".join(str(y) for y in custom_yticks)
                lines.append(f"ytick={{ {yticks_str} }},")
                lines.append(r"minor y tick num=0,")
        else:  # Si pas de transformation custom, utiliser le ymode standard
            lines.append(f"ymode={'log' if is_log_y else 'linear'},")
            if custom_ylim:
                lines.append(f"ymin={custom_ylim[0]}, ymax={custom_ylim[1]},")
            if custom_yticks:
                yticks_str = ",".join(str(y) for y in custom_yticks)
                lines.append(f"ytick={{ {yticks_str} }},")
                lines.append(r"minor y tick num=0,")

        # Gestion de l'axe X
        if is_log_x:
            lines.append(r"xmode=log, log basis x=10,")
            if custom_xticks:
                xticks_str = ",".join(str(x) for x in custom_xticks)
                lines.append(f"xtick={{ {xticks_str} }},")
                if custom_xticks and custom_xticks[-1] > max_cardinality_for_x_lim:
                     lines.append(f"xmax={custom_xticks[-1] * 1.1},")
                elif max_cardinality_for_x_lim is not None:
                     lines.append(f"xmax={math.ceil(max_cardinality_for_x_lim * 1.1)},")

            lines.append(r"xticklabel style={/pgf/number format/sci, /pgf/number format/sci zerofill, /pgf/number format/precision=0},")
            lines.append(f"x label style={{at={{(axis description cs:0.5,{xlabel_offset})}},anchor=north}},")

        else: # xmode=linear
            lines.append(r"xmode=linear,")
            lines.append(r"xmin=0,")
            if max_cardinality_for_x_lim is not None and not custom_xticks:
                lines.append(f"xmax={math.ceil(max_cardinality_for_x_lim * 1.1)},")

            if custom_xticks:
                xticks_str = ",".join(str(x) for x in custom_xticks)
                lines.append(f"xtick={{ {xticks_str} }},")
                if custom_xticks and custom_xticks[-1] > max_cardinality_for_x_lim:
                     lines.append(f"xmax={custom_xticks[-1] * 1.05},")

            if add_xlabel_suffix:
                lines.append(r"scaled x ticks=base 10:7,")
                lines.append(r"/pgfplots/xtick scale=10^7,")
                lines.append(r"xticklabel style={/pgf/number format/fixed, /pgf/number format/precision=1},")
                lines.append(f"x label style={{at={{(axis description cs:0.5,{xlabel_offset})}},anchor=north}},")
            else:
                lines.append(r"xticklabel style={/pgf/number format/fixed, /pgf/number format/1000 sep=\,},")
                lines.append(f"x label style={{at={{(axis description cs:0.5,{xlabel_offset})}},anchor=north}},")


        lines.append(r"width=14cm, height=12cm,")
        lines.append(r"grid=major,")
        lines.append(r"legend style={at={(0.5,-0.2)}, anchor=north, legend columns=-1},")
        lines.append(r"tick align=outside,")

        lines.append(r"]")

        for i, data in enumerate(timeDicts):
            color = self.colors[i % len(self.colors)]
            mark = self.markers[i % len(self.markers)]
            coords = " ".join(f"({k},{v})" for k, v in sorted(data.items()))
            lines.append(f"\\addplot[color={color}, mark={mark}] coordinates {{{coords}}};")
            lines.append(f"\\addlegendentry{{{algos[i]}}}")

        lines += [
            r"\end{axis}",
            r"\end{tikzpicture}",
            r"\end{document}"
        ]

        with open(self.output_path, "w") as f:
            f.write("\n".join(lines))

        print(f"✅ Graphe généré : {self.output_path}")


if __name__ == "__main__":
    gen = UniversalLatexGenerator()
    gen.generate_graphs_from_json(
        json_path="timings.json",
        output_folder="../output"
    )