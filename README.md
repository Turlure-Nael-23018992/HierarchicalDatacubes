# Hierarchical Datacubes Analysis Tool

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Tests](https://github.com/Turlure-Nael-23018992/HierarchicalDatacubes/actions/workflows/python-tests.yml/badge.svg)](https://github.com/Turlure-Nael-23018992/HierarchicalDatacubes/actions/workflows/python-tests.yml)
![Coverage Status](./coverage.svg)

A professional desktop application for benchmark and performance analysis of **Hierarchical Datacube** algorithms.

---

## 🚀 Overview

This project provides a comprehensive suite for analyzing and comparing the efficiency of various datacube construction algorithms. It specifically focuses on the transition from classical models to hierarchical structures, offering a specialized environment for algorithms like **BUC**, **Star-Cubing**, and **ClosetCube**.

Developed as part of a research internship, this tool enables researchers and developers to visualize performance bottlenecks and export high-quality reports for academic publications.

## ✨ Key Features

-   📊 **Dual-Tab PyQt6 Interface**:
    -   **Runner Tab**: Execute individual algorithms with real-time logging and performance tracking.
    -   **Comparator Tab**: Benchmark multiple algorithms simultaneously against various datasets.
-   🧠 **Smart Database Matching**:
    -   Automatically redirects standard algorithms to flat databases (`cosky_db`) and hierarchical algorithms to hierarchical formats (`hierarchie_db`).
-   📈 **Advanced Visualization**:
    -   **Live Preview**: Integrated Matplotlib charts for immediate feedback.
    -   **Pro-Grade LaTeX Export**: Automatic generation of TikZ-based graphs optimized for academic reporting.
-   💾 **Performance Caching**:
    -   Save and load performance data to avoid redundant executions.
    -   JSON-based results management.

## 🛠 Project Structure

-   `Core/`: Application core, containing the PyQt6 UI (`AppUIPyQT.py`) and orchestration logic.
-   `scripts/Algorithms/`: Implementations of core algorithms (BUC, Star-Cubing, ClosetCube, and their hierarchical variants).
-   `scripts/databaseManagement/`: Engines for data generation, DB handling, and LaTeX/TikZ export.
-   `Assets/`:
    -   `ExecutionTime/`: Cached performance results.
    -   `LatexReports/`: Organized PDF/TikZ exports categorized by algorithm count.
-   `DB/`: SQLite databases used for benchmarking.

## ⚙️ Installation

### Prerequisites
- Python 3.10 or higher.

### Steps
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd HierarchicalDatacubes
   ```

2. **Install dependencies**:
   It is recommended to use a virtual environment. You can install the project and its dependencies using `pip`:
   ```bash
   pip install -e .
   ```
   *Note: This will install all dependencies defined in `pyproject.toml`.*

## 📋 Usage

To launch the main desktop application:

```bash
python Core/AppUIPyQT.py
```

### Running from CLI
You can also run the algorithms via the terminal using the `Core/main.py` script:
```bash
python Core/main.py
```

---

## 📄 License

This project is part of a research internship on Hierarchical Datacubes.

---
*Created by Nael - 2026*
