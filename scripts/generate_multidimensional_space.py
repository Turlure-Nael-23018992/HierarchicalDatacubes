import os

def generate_latex_table(output_path="scripts/output/multidimensional_space_OM3.tex"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    latex_content = r"""\documentclass{article}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage[margin=1in]{geometry}

\begin{document}

\begin{table}[htbp]
\centering
\caption{Multidimensional space of the data warehouse OM3}
\label{tab:multidimensional_space}
\vspace{0.5em}
\begin{tabular}{c|ccc}
\toprule
\texttt{RowId} & \texttt{IdP} & \texttt{IdT} & \texttt{IdS} \\
\midrule
1 & \textit{France} & $S_1$ & $A_1$ \\
2 & \textit{France} & $S_1$ & $A_{1-1}$ \\
3 & \textit{France} & $S_1$ & $A_{1-2}$ \\
4 & \textit{France} & $S_1$ & $A_2$ \\
\dots & \dots & \dots & \dots \\
5 & \textit{France} & $S_{1-1}$ & $A_1$ \\
\dots & \dots & \dots & \dots \\
6 & \textit{IDF} & $S_1$ & $A_1$ \\
\dots & \dots & \dots & \dots \\
7 & \textit{es} & $S_{3-3}$ & $A_{7-12}$ \\
8 & $P_1$ & $S_1$ & $A_1$ \\
\dots & \dots & \dots & \dots \\
9 & $P_1$ & $S_1$ & $A_2$ \\
\dots & \dots & \dots & \dots \\
10 & $P_3$ & $S_3$ & $A_7$ \\
\dots & \dots & \dots & \dots \\
11 & \textit{France} & $S_1$ & $\textit{ALL}_{\text{S}}$ \\
\dots & \dots & \dots & \dots \\
12 & \textit{PACA} & $S_{3-3}$ & $\textit{ALL}_{\text{S}}$ \\
13 & \textit{Marseille} & $S_1$ & $\textit{ALL}_{\text{S}}$ \\
\dots & \dots & \dots & \dots \\
14 & $P_1$ & $S_1$ & $\textit{ALL}_{\text{S}}$ \\
\dots & \dots & \dots & \dots \\
15 & \textit{France} & $\textit{ALL}_{\text{T}}$ & $A_1$ \\
16 & \textit{France} & $\textit{ALL}_{\text{T}}$ & $A_{1-1}$ \\
\dots & \dots & \dots & \dots \\
17 & \textit{fr} & $\textit{ALL}_{\text{T}}$ & $A_{7-12}$ \\
18 & $P_1$ & $\textit{ALL}_{\text{T}}$ & $A_1$ \\
\dots & \dots & \dots & \dots \\
19 & $\textit{ALL}_{\text{P}}$ & $S_1$ & $A_1$ \\
20 & $\textit{ALL}_{\text{P}}$ & $S_1$ & $A_{1-1}$ \\
\dots & \dots & \dots & \dots \\
21 & \textit{France} & $\textit{ALL}_{\text{T}}$ & $\textit{ALL}_{\text{S}}$ \\
22 & \textit{IDF} & $\textit{ALL}_{\text{T}}$ & $\textit{ALL}_{\text{S}}$ \\
23 & \textit{Paris} & $\textit{ALL}_{\text{T}}$ & $\textit{ALL}_{\text{S}}$ \\
\dots & \dots & \dots & \dots \\
24 & $\textit{ALL}_{\text{P}}$ & $S_1$ & $\textit{ALL}_{\text{S}}$ \\
\dots & \dots & \dots & \dots \\
25 & $\textit{ALL}_{\text{P}}$ & $\textit{ALL}_{\text{T}}$ & $A_7$ \\
\dots & \dots & \dots & \dots \\
26 & $\textit{ALL}_{\text{P}}$ & $\textit{ALL}_{\text{T}}$ & $\textit{ALL}_{\text{S}}$ \\
27 & $\emptyset$ & $\emptyset$ & $\emptyset$ \\
\bottomrule
\end{tabular}
\end{table}

\end{document}
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(latex_content.strip())
    print(f"✅ Fichier LaTeX exporté avec succès : {os.path.abspath(output_path)}")

if __name__ == "__main__":
    generate_latex_table()
