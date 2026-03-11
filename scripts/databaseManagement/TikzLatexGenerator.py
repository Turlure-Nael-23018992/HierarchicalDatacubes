from __future__ import annotations
import json
import math
import os

_HERE             = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR  = os.path.normpath(os.path.join(_HERE, "..", "..", "Assets", "ExecutionTime"))
DEFAULT_OUT_DIR   = os.path.normpath(os.path.join(_HERE, "..", "output"))


class TikzLatexGenerator:
    """
    Generates a TikZ .tex file comparing multiple algorithms.

    Parameters
    ----------
    data_dir : str
        Directory containing algorithm sub-folders.
    title : str | None
        Title displayed above the graph. None -> no title.
    scale_x : str
        Scale of the X-axis: "lin" or "log".
    scale_y : str
        Scale of the Y-axis: "lin" or "log".
    width : int
        Width of the TikZ canvas in points.
    height : int
        Height of the TikZ canvas in points.
    only_common : bool
        If True, only keeps cardinalities common to all algorithms.
        If False, plots all available cardinalities for each curve.
    """

    DEFAULT_COLORS = [
        ("RoyalBlue",    "RGB", "65,105,225"),
        ("Crimson",      "RGB", "220,20,60"),
        ("ForestGreen",  "RGB", "34,139,34"),
        ("DarkOrange",   "RGB", "255,140,0"),
        ("Purple",       "RGB", "128,0,128"),
        ("Teal",         "RGB", "0,128,128"),
        ("SaddleBrown",  "RGB", "139,69,19"),
    ]

    MARKERS = {
        "circle":    (r"\filldraw[color=black, fill={c}] ({x}pt,{y}pt) circle (3pt);", ""),
        "square":    (r"\filldraw[color=black, fill={c}] ({x}pt,{y}pt) +(-3pt,-3pt) rectangle +(3pt,3pt);", ""),
        "triangle":  (r"\filldraw[color=black, fill={c}] ({x}pt,{y}pt) +(-3pt,-2.6pt) -- +(3pt,-2.6pt) -- +(0pt,3pt) -- cycle;", ""),
        "diamond":   (r"\filldraw[color=black, fill={c}] ({x}pt,{y}pt) +(0,-3.5pt) -- +(3.5pt,0) -- +(0,3.5pt) -- +(-3.5pt,0) -- cycle;", ""),
        "star":      (r"\node[star, star points=5, star point ratio=2.2, fill={c}, draw=black, inner sep=1.8pt] at ({x}pt,{y}pt) {{}};", r"\usetikzlibrary{shapes.geometric}"),
        "none":      ("", ""),
    }

    LINE_STYLES = {
        "solid":      "",
        "dashed":     "dashed",
        "dotted":     "dotted",
        "dashdotted": "dash dot",
    }

    def __init__(self,
                 data_dir:    str  = DEFAULT_DATA_DIR,
                 title:       str  = None,
                 scale_x:     str  = "log",
                 scale_y:     str  = "lin",
                 width:       int  = 320,
                 height:      int  = 280,
                 only_common: bool = True):
        self.data_dir    = data_dir
        self.title       = title
        self.scale_x     = scale_x.lower()
        self.scale_y     = scale_y.lower()
        self.width       = width
        self.height      = height
        self.only_common = only_common

    def _load(self, algo: str) -> dict[int, float]:
        """Loads Assets/ExecutionTime/<algo>/c3.json -> {cardinality: avg_time}."""
        path = os.path.join(self.data_dir, algo, "c3.json")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        td = {int(k): sum(v) / len(v) for k, v in raw["time_data"].items() if v}
        return td

    def load_all(self, algos: list[str]) -> list[dict[int, float]]:
        """Loads data for each algorithm and normalizes bounds if requested."""
        dicts = []
        for algo in algos:
            try:
                td = self._load(algo)
                dicts.append(td)
                print(f"  ✅ {algo}: {len(td)} point(s) loaded")
            except FileNotFoundError as e:
                print(f"  ❌ Error loading {algo}: {e}")
                raise e

        if self.only_common and len(dicts) > 1:
            common = set.intersection(*(set(d.keys()) for d in dicts))
            dicts = [{k: d[k] for k in sorted(common)} for d in dicts]
            print(f"  ↳  Common cardinalities selected: {sorted(common)}")

        return dicts

    def _to_pos(self, value: float, max_val: float, scale: str, canvas: int, min_val: float = 0.0) -> int:
        """Converts a value to canvas coordinate (TikZ points)."""
        if scale == "log":
            if min_val > 0:
                if value <= min_val: return 0
                return int(round((math.log10(value) - math.log10(min_val)) / (math.log10(max_val) - math.log10(min_val)) * canvas))
            else:
                if value <= 0: return 0
                return int(round(math.log10(value + 1) / math.log10(max_val + 1) * canvas))
        else:
            if value <= min_val: return 0
            return int(round((value - min_val) / (max_val - min_val) * canvas)) if max_val > min_val else 0

    def _nice_max(self, value: float) -> float:
        """Rounds up to a nice value for axes."""
        if value <= 0:
            return 10
        exp   = math.floor(math.log10(value))
        frac  = value / (10 ** exp)
        nice  = next(n for n in [1, 2, 5, 10] if n >= frac)
        return nice * (10 ** exp)

    def _log_ticks(self, min_val: float, max_val: float, canvas: int) -> list[tuple[float, int]]:
        """Ticks in powers of 10."""
        ticks = []
        if min_val <= 0: min_val = 1
        exp_start = math.floor(math.log10(min_val))
        exp = exp_start
        while 10 ** exp <= max_val:
            v   = float(10 ** exp)
            if v >= min_val:
                pos = self._to_pos(v, max_val, "log", canvas, min_val)
                ticks.append((v, pos))
            exp += 1
        return ticks

    def _lin_ticks(self, min_val: float, max_val: float, canvas: int, n: int = 6) -> list[tuple[float, int]]:
        """Regular linear ticks."""
        ticks = []
        for i in range(n):
            raw = min_val + (max_val - min_val) * i / (n - 1)
            pos = self._to_pos(raw, max_val, "lin", canvas, min_val)
            ticks.append((raw, pos))
        return ticks

    def _axis_ticks(self, min_val: float, max_val: float, scale: str, n_ticks: int = 6) -> list[tuple[float, int]]:
        """Delegates to _log_ticks or _lin_ticks based on scale."""
        canvas = self.width if scale == self.scale_x else int(self.height * 0.85)
        if scale == "log":
            return self._log_ticks(min_val, max_val, canvas)
        return self._lin_ticks(min_val, max_val, canvas, n_ticks)

    def _fmt(self, value: float) -> str:
        """Formats a number into readable LaTeX notation."""
        if value < 0.001:
            return "$0$"
        if value < 1000:
            return f"${value:.3g}$"
        exp  = int(math.floor(math.log10(value)))
        base = value / (10 ** exp)
        if abs(base - round(base)) < 0.05:
            base = int(round(base))
            return f"${base}\\!\\times\\!10^{{{exp}}}$"
        return f"${base:.1f}\\!\\times\\!10^{{{exp}}}$"

    def generate(self,
                 algos:       list[str],
                 output_path: str,
                 styles:      list[dict] | None = None) -> None:
        """
        Generates the TikZ .tex file.

        Parameters
        ----------
        algos : list[str]
            Names of the algorithms to compare.
        output_path : str
            Full path of the .tex file to write.
        styles : list[dict] | None
            Optional list of dictionaries per algorithm:
              {
                "color":      "RoyalBlue",         # name defined in DEFAULT_COLORS or TikZ color
                "line_style": "solid",              # "solid","dashed","dotted","dashdotted"
                "marker":     "circle",             # "circle","square","triangle","diamond","star","none"
                "line_width": "2pt",                # width of the curve
              }
            If None or incomplete, default values are used.
        """
        print(f"\n▶  Loading data…")
        dicts = self.load_all(algos)

        all_cards = sorted({k for d in dicts for k in d})
        all_times = [d[k] for d in dicts for k in d]
        if not all_cards or not all_times:
            print("  ⚠️  No data found.")
            return

        max_card    = self._nice_max(max(all_cards))
        max_time    = self._nice_max(max(all_times))
        min_card    = min(all_cards) if all_cards else 0
        min_time    = 0.0
        canvas_x    = self.width
        canvas_y    = int(self.height * 0.85)

        resolved_styles = self._resolve_styles(algos, styles)

        extra_libs = set()
        for st in resolved_styles:
            _, lib = self.MARKERS.get(st["marker"], ("", ""))
            if lib:
                extra_libs.add(lib.replace(r"\usetikzlibrary{", "").rstrip("}"))

        L = []

        L += [
            r"\documentclass[tikz, border=20pt]{standalone}",
            r"\usepackage{tikz}",
        ]
        base_libs = "arrows.meta, shapes, positioning, matrix"
        all_libs  = base_libs + (", " + ", ".join(extra_libs) if extra_libs else "")
        L.append(f"\\usetikzlibrary{{{all_libs}}}")
        L += [r"\usepackage{xcolor}", r"\usepackage{amsmath}", r"\begin{document}"]

        color_names = []
        for st in resolved_styles:
            cname, cmode, cval = st["_color_def"]
            if cmode:
                L.append(f"\\definecolor{{{cname}}}{{{cmode}}}{{{cval}}}")
            color_names.append(cname)

        for cname in color_names:
            L.append(
                f"\\tikzset{{leg{cname}/.style={{rectangle, fill={cname}, "
                f"draw=black, line width=0.6pt, minimum size=8pt, inner sep=0pt}}}}"
            )

        L.append(
            r"\begin{tikzpicture}["
            r"line join=round, line cap=round,"
            r"every node/.style={text=black, font=\small}"
            r"]"
        )

        x_ticks = self._axis_ticks(min_card, max_card, self.scale_x)
        y_ticks = self._axis_ticks(min_time, max_time, self.scale_y)

        for _, px in x_ticks[1:]:
            L.append(f"\\draw[gray!20] ({px}pt,0pt) -- ({px}pt,{canvas_y}pt);")
        for _, py in y_ticks[1:]:
            L.append(f"\\draw[gray!20] (0pt,{py}pt) -- ({canvas_x}pt,{py}pt);")

        L.append(f"\\draw[black, -stealth, line width=1.2pt] (0pt,-2pt) -- ({canvas_x+15}pt,-2pt);")
        L.append(f"\\draw[black, -stealth, line width=1.2pt] (-2pt,0pt) -- (-2pt,{canvas_y+15}pt);")

        for raw, px in x_ticks:
            L.append(
                f"\\draw[black] ({px}pt, 0pt) -- ({px}pt, -4pt)"
                f" node[below, font=\\scriptsize, text=black] {{{self._fmt(raw)}\\strut}};"
            )

        for raw, py in y_ticks:
            L.append(
                f"\\draw[black] (0pt, {py}pt) -- (-4pt, {py}pt)"
                f" node[left, font=\\scriptsize, text=black] {{{self._fmt(raw)}\\strut}};"
            )

        L.append(
            f"\\node[below=18pt, text=black] at ({canvas_x//2}pt, -2pt)"
            f" {{\\textit{{Cardinality}}}};"
        )

        L.append(
            f"\\node[rotate=90, above=22pt, text=black] at (-15pt, {canvas_y//2}pt)"
            f" {{\\textit{{Response time (s)}}}};"
        )

        if self.title:
            L.append(
                f"\\node[above=10pt, font=\\bfseries\\normalsize, text=black]"
                f" at ({canvas_x//2}pt, {canvas_y}pt) {{{self.title}}};"
            )

        for td, st, cname in zip(dicts, resolved_styles, color_names):
            lw        = st.get("line_width", "2pt")
            tikz_dash = self.LINE_STYLES.get(st["line_style"], "")
            dash_opt  = f", {tikz_dash}" if tikz_dash else ""

            pts = []
            for card in sorted(td.keys()):
                t  = td[card]
                px = self._to_pos(card, max_card, self.scale_x, canvas_x, min_card)
                py = self._to_pos(t,    max_time, self.scale_y, canvas_y, min_time)
                pts.append((px, py))

            if not pts:
                continue

            path = " -- ".join(f"({x}pt,{y}pt)" for x, y in pts)
            L.append(f"\\draw[{cname}, line width={lw}{dash_opt}] {path};")

            marker_tpl, _ = self.MARKERS.get(st["marker"], ("", ""))
            if marker_tpl:
                for x, y in pts:
                    L.append(
                        marker_tpl
                        .replace("{c}", cname)
                        .replace("{x}", str(x))
                        .replace("{y}", str(y))
                    )

        legend_x = canvas_x + 25
        legend_y = canvas_y // 2
        L.append(
            f"\\matrix ["
            f"draw=gray!50, fill=white, inner sep=8pt, row sep=4pt,"
            f" rounded corners=3pt, anchor=west"
            f"] at ({legend_x}pt, {legend_y}pt) {{"
        )
        for algo, cname in zip(algos, color_names):
            L.append(
                f"  \\node [leg{cname}, label=right:{{\\small\\texttt{{{algo}}}}}] {{}}; \\\\"
            )
        L.append("};")

        L += [r"\end{tikzpicture}", r"\end{document}"]

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(L))
        print(f"  📄 Generated: {output_path}")

    def _resolve_styles(self, algos: list[str],
                        styles: list[dict] | None) -> list[dict]:
        """Resolves default styles for each algorithm."""
        default_markers     = ["circle", "square", "triangle", "diamond", "star", "circle", "square"]
        default_line_styles = ["solid", "dashed", "dotted", "dashdotted", "solid", "dashed", "dotted"]

        resolved = []
        for i, algo in enumerate(algos):
            user_st = (styles[i] if styles and i < len(styles) else {}) or {}

            if "color" in user_st:
                cname    = user_st["color"]
                cdef     = (cname, "", "")
            else:
                cname, cmode, cval = self.DEFAULT_COLORS[i % len(self.DEFAULT_COLORS)]
                cdef               = (cname, cmode, cval)

            resolved.append({
                "_color_def": cdef,
                "line_style": user_st.get("line_style", default_line_styles[i]),
                "marker":     user_st.get("marker",     default_markers[i]),
                "line_width": user_st.get("line_width", "2pt"),
            })

        return resolved


if __name__ == "__main__":
    import sys

    try:
        available_algos = [
            "BUC", "StarCubing", "ClosetCube",
            "HierarchicalBUC", "HierarchicalStarCubing", "HierarchicalClosetCube"
        ]

        print(f"Available algorithms: {', '.join(available_algos)}")
        algos_input = input("Enter algorithm names separated by commas, or press Enter for ALL: ").strip()
        
        if not algos_input:
            algos = available_algos
            print("Using all available algorithms.")
        else:
            algos = [a.strip() for a in algos_input.split(",") if a.strip()]
        
        if not algos:
            print("No algorithms selected. Exiting.")
            sys.exit(0)

        out_filename = input("Enter output filename (e.g., custom_comparison.tex) [press Enter for default]: ").strip()
        if not out_filename:
            out_filename = "custom_comparison.tex"
        
        output_file = os.path.join(DEFAULT_OUT_DIR, out_filename)
        
        title = input("Enter plot title (leave empty for default): ").strip()
        if not title:
            if len(algos) <= 3:
                title = f"{' vs '.join(algos)} — Response time"
            else:
                title = f"Comparison of {len(algos)} algorithms — Response time"

        gen = TikzLatexGenerator(
            title       = title,
            scale_x     = "log",    
            scale_y     = "lin",    
            width       = 340,      
            height      = 300,      
            only_common = True,     
        )

        gen.generate(algos, output_file)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(0)
