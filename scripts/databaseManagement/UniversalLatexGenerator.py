import math
import json
import os
import re

class UniversalLatexGenerator:
    def __init__(self, output_path=None):
        self.colors = ["skyblue", "cyan", "brightmaroon", "SQLCodeGreen", "SQLcodegray"]
        self.output_path = output_path

    def get_rgb_value(self, color_name):
        color_map = {
            "brightmaroon": ("195,33,72", "RGB"),
            "cyan": ("0,255,255", "RGB"),
            "skyblue": ("135,206,235", "RGB"),
            "SQLCodeGreen": ("0,100,0", "RGB"),
            "SQLcodegray": ("127,127,127", "RGB"),
        }
        return color_map.get(color_name, ("0,0,0", "RGB"))

    def round_to_axis(self, value):
        if value <= 0:
            return 10
        magnitude = 10 ** (len(str(int(value))) - 1)
        return ((int(value) // magnitude) + 1) * magnitude

    def format_tick_label(self, value):
        if value <= 0:
            return "$0$"
        exponent = int(math.log10(value)) if value > 0 else 0
        base = int(value / (10 ** exponent)) if exponent > 0 else int(value)
        return f"${base} \\times 10^{{{exponent}}}$" if exponent >= 3 else f"${int(value)}$"

    def generate_graphs_from_json(self, json_path, output_folder):
        """
        Maintains compatibility with the UI to generate default sets of graphs.
        """
        with open(json_path, "r") as f:
            raw_data = json.load(f)

        def extract_cardinality(name):
            match = re.search(r"_R(\d+)", name)
            return int(match.group(1)) if match else None

        algo_groups = [
            ("BUC_SC_Cl_noH.tex", ["BUC", "StarCubing", "ClosetCube"]),
            ("BUC_SC_Cl_withH.tex", ["HierarchicalBUC", "HierarchicalStarCubing", "HierarchicalClosetCube"]),
            ("BUC_vs_HBUC.tex", ["BUC", "HierarchicalBUC"]),
            ("SC_vs_HSC.tex", ["StarCubing", "HierarchicalStarCubing"]),
            ("Cl_vs_HCl.tex", ["ClosetCube", "HierarchicalClosetCube"]),
        ]

        for filename, algos in algo_groups:
            timeDicts = []
            maxCard = 0
            maxTime = 0

            for algo in algos:
                d = {}
                for db_name, stats in raw_data.get(algo, {}).items():
                    if not stats.get("success", False): continue
                    card = extract_cardinality(db_name)
                    time = stats.get("duration_seconds", None)
                    if card and time is not None:
                        # Wrap time in list to match old generate_latex expectations (1 attribute case)
                        d[card] = [time]
                        maxCard = max(maxCard, card)
                        maxTime = max(maxTime, time)
                timeDicts.append(d)

            if not any(timeDicts): continue

            self.output_path = os.path.join(output_folder, filename)
            # Use fixed attributes=[3] as default for these auto-generated reports
            self.generate_latex(timeDicts, [maxCard], [maxTime], algos, attributes=[3])

    def generate_latex(self, timeDicts, maxRowsList, maxTimeList, algos, attributes=[3],
                       scaleX=300, scaleY=300, scaleType="LinX/LinY"):
        """
        The user's preferred TikZ-based manual drawing logic.
        """
        is_log_x = "LogX" in scaleType
        is_log_y = "LogY" in scaleType

        lines = [
            r"\documentclass[tikz, border=10pt]{standalone}",
            r"\usepackage{tikz}",
            r"\usetikzlibrary{arrows.meta, shapes, positioning}",
            r"\usepackage{xcolor}",
            r"\begin{document}"
        ]

        # Define Colors
        for i, color in enumerate(self.colors[:len(algos)]):
            rgb, mode = self.get_rgb_value(color)
            lines.append(f"\\definecolor{{{color}}}{{{mode}}}{{{rgb}}}")
            lines.append(
                f"\\tikzset{{small{color}node/.style={{circle, fill={color}, draw=black, line width=0.5pt, "
                f"minimum size=4pt, inner sep=0pt}}}}"
            )

        for i, attr in enumerate(attributes):
            maxRows = maxRowsList[i]
            # Use provided maxTime or round it
            rawMaxTime = maxTimeList[i]
            maxTimeVal = self.round_to_axis(rawMaxTime)
            
            ratioX = scaleX / math.log(maxRows + 1) if is_log_x else scaleX / maxRows
            ratioY = (scaleY * 0.8) / math.log(maxTimeVal + 1) if is_log_y else (scaleY * 0.8) / maxTimeVal

            graph = [f"% Graph for {attr} attributes", r"\begin{tikzpicture}[line join=bevel]"]

            # Axes
            graph.append(f"\\draw[-stealth] (0pt, 0pt) -- ({scaleX + 20}pt, 0pt) node[anchor=north west, yshift=15pt] {{Cardinality}};")
            graph.append(f"\\draw[-stealth] (0pt, 0pt) -- (0pt, {scaleY}pt) node[anchor=south] {{Response time (s)}};")

            # X-axis ticks
            graph.append("        \\foreach \\x/\\xtext in {")
            for s in range(6):
                frac = s / 5
                if is_log_x:
                    log_val = math.log(maxRows + 1) * frac
                    raw_val = int(math.exp(log_val)) - 1
                    pos = int(log_val * ratioX)
                else:
                    raw_val = int(maxRows * frac)
                    pos = int(scaleX * frac)
                label = self.format_tick_label(raw_val)
                graph.append(f"            {pos}pt/{label},")
            graph[-1] = graph[-1].rstrip(",") + "} {"
            graph.append("            \\draw (\\x, 2pt) -- (\\x, -2pt) node[below] {\\xtext\\strut};")
            graph.append("        }")

            # Y-axis ticks
            graph.append("        \\foreach \\y/\\ytext in {")
            for s in range(6):
                frac = s / 5
                if is_log_y:
                    log_val = math.log(maxTimeVal + 1) * frac
                    raw_val = int(math.exp(log_val)) - 1
                    pos = int(log_val * ratioY)
                else:
                    raw_val = maxTimeVal * frac
                    pos = int((scaleY * 0.8) * frac)
                label = self.format_tick_label(raw_val)
                graph.append(f"            {pos}pt/{label},")
            graph[-1] = graph[-1].rstrip(",") + "} {"
            graph.append("            \\draw (2pt, \\y) -- (-2pt, \\y) node[left] {\\ytext\\strut};")
            graph.append("        }")

            # Lines and points
            for j, timeDict in enumerate(timeDicts):
                color = self.colors[j % len(self.colors)]
                line = f"        \\draw[{color}, line width=1.5pt]"
                points = []
                # Sort keys to ensure lines connect properly
                sorted_keys = sorted(timeDict.keys(), key=lambda x: int(x))
                
                point_count = 0
                for k in sorted_keys:
                    val = timeDict[k]
                    # Handle both single float and list of floats (for multiple attributes)
                    if isinstance(val, (list, tuple)):
                        y_raw = val[i] if i < len(val) else None
                    else:
                        y_raw = val if i == 0 else None
                    
                    if y_raw is None or not isinstance(y_raw, (int, float)):
                        continue
                    
                    xval = math.log(int(k) + 1) if is_log_x else int(k)
                    yval = math.log(y_raw + 1) if is_log_y else y_raw
                    x = int(round(xval * ratioX))
                    y = int(round(yval * ratioY))
                    
                    if point_count == 0:
                        line += f" ({x}pt, {y}pt)"
                    else:
                        line += f" -- ({x}pt, {y}pt)"
                    
                    points.append(f"        \\filldraw[color=black, fill={color}] ({x}pt, {y}pt) circle (2pt);")
                    point_count += 1

                if point_count > 0:
                    graph.append(line + ";")
                    graph.extend(points)

            # Legend
            if algos:
                graph.append(r"        \matrix [left=0.5cm of current bounding box.north east, anchor=north east] at (current bounding box.north east) {")
                for j, algo in enumerate(algos):
                    color = self.colors[j % len(self.colors)]
                    name = str(algo).replace("_", " ")
                    graph.append(f"            \\node [small{color}node, label=right:{name} with {attr} attributes] {{}}; \\\\")
                graph.append(r"        };")
            
            graph.append(r"\end{tikzpicture}")
            if i < len(attributes) - 1:
                graph.append(r"\clearpage")
            lines.extend(graph)

        lines.append(r"\end{document}")

        with open(self.output_path, "w") as f:
            f.write("\n".join(lines))
        
        print(f"✅ Graphe généré : {self.output_path}")


if __name__ == "__main__":
    gen = UniversalLatexGenerator()
    gen.generate_graphs_from_json(
        json_path="timings.json",
        output_folder="../output"
    )