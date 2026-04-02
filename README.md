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

### 🚀 Quick Start (Recommended)

To install everything automatically in a virtual environment:

#### 🪟 Windows
Run the `install.bat` file:
```bash
./install.bat
```

#### 🐧 Linux / 🍎 macOS
Run the `install.sh` script:
```bash
./install.sh
```

---

### 🛠️ Manual Installation (Advanced)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd HierarchicalDatacubes
   ```

2. **Install dependencies**:
   It is recommended to use a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

## 📋 Usage

After installation, you can launch the tools directly from your terminal (ensure your virtual environment is activated):

### 📊 Desktop Application (PyQt6)
```bash
datacube-gui
```

### ⌨️ CLI Benchmark Tool
```bash
datacube-cli
```

---

## 🙏 Acknowledgments

This project is based on and continues the initial work from [MatteraAurelien/HierarchicalDatacubes-Repo](https://github.com/MatteraAurelien/HierarchicalDatacubes-Repo).

## 📄 License

This project is distributed under the MIT License - see the [LICENSE](LICENSE) file for more details. 
It was developed as part of a research internship on Hierarchical Datacubes.

---
*Created by Nael - 2026*
