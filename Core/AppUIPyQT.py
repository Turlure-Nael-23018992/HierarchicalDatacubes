import sys
import os
import time
import threading
import glob
import io
import contextlib
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QLabel, QComboBox, QPushButton, 
                                 QTextEdit, QFileDialog, QSpinBox, QProgressBar,
                                 QLineEdit, QTabWidget, QListWidget, QListWidgetItem,
                                 QCheckBox, QRadioButton, QButtonGroup, QGroupBox,
                                 QTableWidget, QTableWidgetItem, QHeaderView)
    from PyQt6.QtCore import QThread, pyqtSignal, Qt
    from PyQt6.QtGui import QColor, QBrush
except ImportError:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QLabel, QComboBox, QPushButton, 
                                 QTextEdit, QFileDialog, QSpinBox, QProgressBar,
                                 QLineEdit, QTabWidget, QListWidget, QListWidgetItem,
                                 QCheckBox, QRadioButton, QButtonGroup, QGroupBox,
                                 QTableWidget, QTableWidgetItem, QHeaderView)
    from PyQt5.QtCore import QThread, pyqtSignal, Qt
    from PyQt5.QtGui import QColor, QBrush

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import json
import re

# Internal imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Core.main import Main
from Core.latexMaker import LatexMaker

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.axes.set_title("Performance Preview")
        self.axes.set_xlabel("Row Count")
        self.axes.set_ylabel("Execution Time (s)")
        self.axes.grid(True, linestyle='--', alpha=0.7)
        fig.tight_layout()

class AlgoWorker(QThread):
    finished = pyqtSignal(float, str)  # time, log_message
    results_ready = pyqtSignal(str)
    data_ready = pyqtSignal(list, list) # rows, headers
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, algo_name, db_path, is_hierarchical):
        super().__init__()
        self.algo_name = algo_name
        self.db_path = db_path
        self.is_hierarchical = is_hierarchical

    def run(self):
        try:
            self.log.emit(f"Starting {self.algo_name} on {os.path.basename(self.db_path)}...")
            
            # Capture stdout to get algorithm results (the cube)
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                main_instance = Main(self.db_path, isPrinted=True)
                
                algo_map = {
                    "BUC": main_instance.runBUC,
                    "Star-Cubing": main_instance.runStarCubing,
                    "ClosetCube": main_instance.runClosetCube,
                    "Hierarchical BUC": main_instance.runHierarchicalBUC,
                    "Hierarchical Star-Cubing": main_instance.runHierarchicalStarCubing,
                    "Hierarchical ClosetCube": main_instance.runHierarchicalClosetCube,
                    "Hierarchical LevelUpCube": main_instance.runHierarchicalLevelUpCube,
                    "Hierarchical CompleteCube": main_instance.runHierarchicalCompleteCube,
                    "OptimizedHierarchicalStarCubing": main_instance.runOptimizedHierarchicalStarCubing,
                }
                
                if self.algo_name in algo_map:
                    results = algo_map[self.algo_name]()
                    exec_time = main_instance.time
                    output = f.getvalue()
                    
                    # Process structured data for the table
                    headers, rows = self.parse_results(results, main_instance)
                    
                    self.results_ready.emit(output)
                    self.data_ready.emit(rows, headers)
                    self.finished.emit(exec_time, f"Algorithm {self.algo_name} completed successfully.")
                else:
                    self.error.emit(f"Unknown algorithm: {self.algo_name}")
                
        except Exception as e:
            import traceback
            self.error.emit(f"Error during execution: {str(e)}\n{traceback.format_exc()}")

    def parse_results(self, results, main_instance):
        """Standardizes different algorithm outputs into (headers, rows)."""
        headers = []
        rows = []
        
        try:
            if self.algo_name == "Hierarchical BUC":
                all_flat = []
                headers = []
                patterns = sorted(results.keys(), key=lambda p: p.count('1'))
                
                for pattern in patterns:
                    current_rows = results[pattern]
                    if not current_rows: continue
                    
                    if not headers:
                        raw_headers = [k for k in current_rows[0].keys() if not k.startswith("_")]
                        headers = ["Level"] + raw_headers
                    elif rows:
                        # Add literal separator row
                        rows.append(["=" * 10] * len(headers))
                        
                    for r in current_rows:
                        row = [r.get("_all_count", 0)]
                        for h in headers[1:]:
                            row.append(str(r.get(h, "")))
                        rows.append(row)
            elif self.algo_name == "BUC":
                headers = ["Level"] + main_instance.BUC.dim_names + [main_instance.BUC.measure_name]
                for k, v in results.items():
                    level = list(k).count("ALL")
                    rows.append([level] + list(k) + [v])
            elif self.algo_name in ["Star-Cubing", "ClosetCube", "OptimizedHierarchicalStarCubing"]:
                if results:
                    raw_headers = list(results[0].keys())
                    headers = ["Level"] + raw_headers
                    last_anc_count = -1
                    for r in results:
                        vals = [str(r.get(h, "")) for h in raw_headers]
                        level = vals.count("ALL") # Simplified count
                        # If the algo returns specific ALLs like ALL_f, count those too
                        level = sum(1 for v in vals if "ALL" in v.upper())
                        
                        if last_anc_count != -1 and level != last_anc_count:
                            rows.append(["=" * 10] * len(headers))
                            
                        rows.append([level] + vals)
                        last_anc_count = level
            elif self.algo_name == "Hierarchical Star-Cubing":
                if results:
                    raw_headers = list(results[0].keys())
                    headers = ["Level"] + raw_headers
                    last_anc_count = -1
                    for r in results:
                        vals = [str(r.get(h, "")) for h in raw_headers]
                        level = sum(1 for v in vals if "ALL" in v.upper())
                        
                        if last_anc_count != -1 and level != last_anc_count:
                            rows.append(["=" * 10] * len(headers))
                            
                        rows.append([level] + vals)
                        last_anc_count = level
            elif self.algo_name in ["Hierarchical ClosetCube", "Hierarchical LevelUpCube"]:
                # HCC/LevelUp results are tuples (d1, d2, d3, m1, m2...)
                headers = ["Level"] + main_instance.hClosetCube.dim_cols + main_instance.hClosetCube.measure_cols
                
                # To calculate level, we check how many values are NOT in the leaf-level data
                # But since HCC is closed, it might be tricky. Let's just use 0 for now or calculate correctly.
                # Actually, HCC hierarchy doesn't have ALL but has parents.
                def get_hcc_level(row_tuple):
                    lvl = 0
                    for i, val in enumerate(row_tuple[:len(main_instance.hClosetCube.dim_cols)]):
                        dim_name = main_instance.hClosetCube.dim_cols[i]
                        # If the value has children in the hierarchy, it's an aggregation
                        if val in main_instance.hClosetCube.hierarchy.get(dim_name, {}):
                            lvl += 1
                    return lvl

                processed_rows = []
                for r in results:
                    lvl = get_hcc_level(r)
                    processed_rows.append([lvl] + list(r))
                
                # Sort by level to match other hierarchical algos and add separators
                processed_rows.sort(key=lambda x: x[0])
                
                last_lvl = -1
                for row_data in processed_rows:
                    if last_lvl != -1 and row_data[0] != last_lvl:
                        rows.append(["=" * 10] * len(headers))
                    rows.append(row_data)
                    last_lvl = row_data[0]
            elif self.algo_name == "Hierarchical CompleteCube":
                # CompleteCube results: (d1, d2, d3, m1...) where some dim vals may be 'ALL'
                headers = ["Level"] + main_instance.hCompleteCube.dim_cols + main_instance.hCompleteCube.measure_cols
                processed_rows = []
                for r in results:
                    vals = list(r[:len(main_instance.hCompleteCube.dim_cols)])
                    lvl = sum(1 for v in vals if str(v).upper() == "ALL")
                    processed_rows.append([lvl] + list(r))
                processed_rows.sort(key=lambda x: x[0])
                last_lvl = -1
                for row_data in processed_rows:
                    if last_lvl != -1 and row_data[0] != last_lvl:
                        rows.append(["=" * 10] * len(headers))
                    rows.append(row_data)
                    last_lvl = row_data[0]
        except Exception as e:
            print(f"Parsing error: {e}")
            
        return headers, rows

class BatchWorker(QThread):
    finished = pyqtSignal(dict) # {algo: {row_count: time}}
    progress = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, algos, dbs, smart_match=False):
        super().__init__()
        self.algos = algos
        self.dbs = dbs # List of (name, path)
        self.smart_match = smart_match

    def run(self):
        results = {}
        total_tasks = len(self.algos) * len(self.dbs)
        current_task = 0
        
        try:
            for algo in self.algos:
                results[algo] = {}
                is_hier_algo = "Hierarchical" in algo
                
                for db_name, db_path in self.dbs:
                    current_task += 1
                    
                    # Smart Matching Logic
                    actual_db_path = db_path
                    actual_db_name = db_name
                    if self.smart_match:
                        is_hier_db = "hierarchie" in db_name.lower()
                        if is_hier_algo and not is_hier_db:
                            # Redirect cosky -> hierarchie
                            match_name = db_name.replace("cosky_db", "hierarchie_db")
                            test_path = os.path.join(os.path.dirname(db_path), match_name)
                            if os.path.exists(test_path):
                                actual_db_path = test_path
                                actual_db_name = match_name
                        elif not is_hier_algo and is_hier_db:
                            # Redirect hierarchie -> cosky
                            match_name = db_name.replace("hierarchie_db", "cosky_db")
                            test_path = os.path.join(os.path.dirname(db_path), match_name)
                            if os.path.exists(test_path):
                                actual_db_path = test_path
                                actual_db_name = match_name

                    self.progress.emit(f"[{current_task}/{total_tasks}] Running {algo} on {actual_db_name}...")
                    
                    row_match = re.search(r"_R(\d+)", actual_db_name)
                    rows = int(row_match.group(1)) if row_match else 0
                    
                    try:
                        main_instance = Main(actual_db_path, isPrinted=False)
                        algo_map = {
                            "BUC": main_instance.runBUC,
                            "Star-Cubing": main_instance.runStarCubing,
                            "ClosetCube": main_instance.runClosetCube,
                            "Hierarchical BUC": main_instance.runHierarchicalBUC,
                            "Hierarchical Star-Cubing": main_instance.runHierarchicalStarCubing,
                            "Hierarchical ClosetCube": main_instance.runHierarchicalClosetCube,
                            "Hierarchical LevelUpCube": main_instance.runHierarchicalLevelUpCube,
                            "Hierarchical CompleteCube": main_instance.runHierarchicalCompleteCube,
                            "OptimizedHierarchicalStarCubing": main_instance.runOptimizedHierarchicalStarCubing,
                        }
                        
                        if algo in algo_map:
                            algo_map[algo]()
                            results[algo][rows] = main_instance.time
                        else:
                            self.progress.emit(f"⚠️ Unknown algo: {algo}")
                    except Exception as e:
                        self.progress.emit(f"❌ Error on {algo}/{db_name}: {str(e)}")
            
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class AppUIPyQT(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hierarchical Datacubes - Runner & Comparator")
        self.setMinimumSize(1000, 700)
        
        self.latex_maker = LatexMaker()
        self.all_databases = [] # List of (name, path)
        
        # Main Widget & Tab Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # --- TAB 1: RUNNER (Single Algo) ---
        self.tab_runner = QWidget()
        self.runner_layout = QVBoxLayout(self.tab_runner)
        self.tabs.addTab(self.tab_runner, "Single Runner")
        
        self.init_runner_ui()
        
        # --- TAB 2: COMPARATOR (Multi Algo / Multi DB) ---
        self.tab_comparator = QWidget()
        self.comp_layout = QHBoxLayout(self.tab_comparator)
        self.tabs.addTab(self.tab_comparator, "Comparator")
        
        self.init_comparator_ui()
        
        # Status Bar
        self.statusBar().showMessage("Ready")
        self.load_databases()

    def init_runner_ui(self):
        # Header
        self.header = QLabel("Hierarchical Datacubes Analysis")
        self.header.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        if hasattr(Qt.AlignmentFlag, 'AlignCenter'):
            self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.header.setAlignment(Qt.AlignCenter)
        self.runner_layout.addWidget(self.header)
        
        # Search Bar
        self.search_layout = QHBoxLayout()
        self.search_label = QLabel("Search DB:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter databases...")
        self.search_input.textChanged.connect(self.filter_databases)
        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_input)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_databases)
        self.search_layout.addWidget(self.refresh_btn)
        self.runner_layout.addLayout(self.search_layout)

        # DB Selection
        self.db_select_layout = QHBoxLayout()
        self.db_label = QLabel("Database:")
        self.db_combo = QComboBox()
        self.db_combo.setMinimumWidth(300)
        self.db_combo.currentIndexChanged.connect(self.validate_compatibility)
        self.db_browse_btn = QPushButton("Browse")
        self.db_browse_btn.clicked.connect(self.browse_db)
        
        self.db_select_layout.addWidget(self.db_label)
        self.db_select_layout.addWidget(self.db_combo)
        self.db_select_layout.addWidget(self.db_browse_btn)
        self.runner_layout.addLayout(self.db_select_layout)
        
        self.compat_label = QLabel("")
        self.compat_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.runner_layout.addWidget(self.compat_label)

        # Algo Selection
        self.algo_layout = QHBoxLayout()
        self.algo_label = QLabel("Algorithm:")
        self.algo_combo = QComboBox()
        self.available_algos = [
            "BUC", "Star-Cubing", "ClosetCube",
            "Hierarchical BUC", "Hierarchical Star-Cubing",
            "Hierarchical ClosetCube", "Hierarchical LevelUpCube",
            "Hierarchical CompleteCube", "OptimizedHierarchicalStarCubing"
        ]
        self.algo_combo.addItems(self.available_algos)
        self.algo_combo.currentIndexChanged.connect(self.validate_compatibility)
        self.algo_layout.addWidget(self.algo_label)
        self.algo_combo.setCurrentIndex(5)
        self.algo_layout.addWidget(self.algo_combo)
        self.runner_layout.addLayout(self.algo_layout)
        
        self.run_btn = QPushButton("Run Algorithm")
        self.run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.run_btn.clicked.connect(self.run_algorithm)
        self.runner_layout.addWidget(self.run_btn)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.runner_layout.addWidget(self.progress)
        
        # Output Tabs
        self.runner_tabs = QTabWidget()
        self.runner_layout.addWidget(self.runner_tabs)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', monospace;")
        self.runner_tabs.addTab(self.log_output, "Execution Logs")
        
        # Results Tab with Filter
        self.results_container = QWidget()
        self.results_vbox = QVBoxLayout(self.results_container)
        
        self.result_filter = QLineEdit()
        self.result_filter.setPlaceholderText("Filter results (e.g. 'Paris', '2023')...")
        self.result_filter.textChanged.connect(self.filter_results)
        
        self.result_options_layout = QHBoxLayout()
        self.result_options_layout.addWidget(self.result_filter)
        
        self.hide_all_checkbox = QCheckBox("Hide Aggregations (Rows with 'ALL')")
        self.hide_all_checkbox.setChecked(False)
        self.hide_all_checkbox.stateChanged.connect(self.filter_results)
        self.result_options_layout.addWidget(self.hide_all_checkbox)
        
        self.results_vbox.addLayout(self.result_options_layout)
        
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setStyleSheet("QTableWidget { background-color: #1e1e1e; color: #d4d4d4; } "
                                         "QHeaderView::section { background-color: #333; color: white; }")
        self.results_vbox.addWidget(self.results_table)
        
        self.runner_tabs.addTab(self.results_container, "Cube Results")
        
        # Keep hidden results_output for raw text if needed (optional, or just use it as back-up)
        self.raw_results_output = QTextEdit()
        self.raw_results_output.setReadOnly(True)
        self.raw_results_output.setVisible(False) 

    def init_comparator_ui(self):
        # Left Panel: Configuration
        self.comp_config = QWidget()
        self.comp_config.setMaximumWidth(300)
        self.comp_config_layout = QVBoxLayout(self.comp_config)
        self.comp_layout.addWidget(self.comp_config)
        
        # Mode Selection
        self.mode_group = QGroupBox("Data Source Mode")
        self.mode_layout = QVBoxLayout()
        self.radio_cache = QRadioButton("Use Cached Data (JSON)")
        self.radio_run = QRadioButton("Execute Algorithms (Live)")
        self.radio_cache.setChecked(True)
        self.mode_layout.addWidget(self.radio_cache)
        self.mode_layout.addWidget(self.radio_run)
        self.mode_group.setLayout(self.mode_layout)
        self.comp_config_layout.addWidget(self.mode_group)

        # Algo List (Checkable)
        self.algo_list_group = QGroupBox("Select Algorithms")
        self.algo_list_layout = QVBoxLayout()
        self.algo_checks = []
        for algo in self.available_algos:
            cb = QCheckBox(algo)
            if "Hierarchical" in algo: cb.setChecked(True)
            self.algo_checks.append(cb)
            self.algo_list_layout.addWidget(cb)
        self.algo_list_group.setLayout(self.algo_list_layout)
        self.comp_config_layout.addWidget(self.algo_list_group)
        
        # DB List (Checkable)
        self.db_list_group = QGroupBox("Select Datasets")
        self.db_list_layout = QVBoxLayout()
        self.db_list_widget = QListWidget()
        self.db_list_layout.addWidget(self.db_list_widget)
        self.db_list_group.setLayout(self.db_list_layout)
        self.comp_config_layout.addWidget(self.db_list_group)
        
        # Smart Match Checkbox
        self.check_smart_match = QCheckBox("Auto-match compatible DBs")
        self.check_smart_match.setToolTip("Redirects standard algos to 'cosky_' DBs and hierarchical algos to 'hierarchie_' DBs")
        self.check_smart_match.setChecked(True)
        self.comp_config_layout.addWidget(self.check_smart_match)
        
        self.compare_btn = QPushButton("Analyze & Compare")
        self.compare_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        self.compare_btn.clicked.connect(self.run_comparison)
        self.comp_config_layout.addWidget(self.compare_btn)
        
        # Right Panel: Visualization
        self.viz_panel = QWidget()
        self.viz_layout = QVBoxLayout(self.viz_panel)
        self.comp_layout.addWidget(self.viz_panel)
        
        self.canvas = MplCanvas(self)
        self.viz_layout.addWidget(self.canvas)
        
        self.comp_log = QTextEdit()
        self.comp_log.setReadOnly(True)
        self.comp_log.setMaximumHeight(150)
        self.comp_log.setStyleSheet("background-color: #1e1e1e; color: #888; font-family: 'Consolas', monospace;")
        self.viz_layout.addWidget(self.comp_log)

    def load_databases(self):
        """Scans the DB/ directory for .db files."""
        db_dir = os.path.join(project_root, "DB")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        db_files = glob.glob(os.path.join(db_dir, "*.db"))
        self.all_databases = [(os.path.basename(f), f) for f in db_files]
        self.filter_databases()
        
        # Update Comparator list
        self.db_list_widget.clear()
        for name, path in self.all_databases:
            item = QListWidgetItem(name)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.db_list_widget.addItem(item)
            
        self.log(f"Found {len(self.all_databases)} databases in {db_dir}")

    def filter_databases(self):
        """Filters the database combo box based on search input."""
        search_text = self.search_input.text().lower()
        self.db_combo.clear()
        
        for name, path in self.all_databases:
            if search_text in name.lower():
                self.db_combo.addItem(name, path)
        
        self.validate_compatibility()

    def browse_db(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Database File", os.path.join(project_root, "DB"), "SQLite Files (*.db);;All Files (*)")
        if file_path:
            name = os.path.basename(file_path)
            if not any(path == file_path for _, path in self.all_databases):
                self.all_databases.append((name, file_path))
                self.filter_databases()
            
            index = self.db_combo.findData(file_path)
            if index >= 0:
                self.db_combo.setCurrentIndex(index)

    def validate_compatibility(self):
        """Checks if the algorithm is compatible with the selected database."""
        if not hasattr(self, 'algo_combo') or not hasattr(self, 'db_combo'):
            return

        algo = self.algo_combo.currentText()
        db_path = self.db_combo.currentData()
        
        if not db_path:
            self.compat_label.setText("No database selected")
            self.compat_label.setStyleSheet("color: orange;")
            return

        db_name = os.path.basename(db_path).lower()
        is_hier_algo = "Hierarchical" in algo
        is_hier_db = "hierarchie" in db_name or "hierarchical" in db_name

        if is_hier_algo and not is_hier_db:
            self.compat_label.setText("⚠️ Warning: Hierarchical algo selected with non-hierarchical DB")
            self.compat_label.setStyleSheet("color: #FFCC00;")
        elif not is_hier_algo and is_hier_db:
            self.compat_label.setText("ℹ️ Note: Standard algo selected with hierarchical DB")
            self.compat_label.setStyleSheet("color: #00BCFF;")
        else:
            self.compat_label.setText("✅ Compatibility OK")
            self.compat_label.setStyleSheet("color: #4CAF50;")

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")

    def run_algorithm(self):
        algo = self.algo_combo.currentText()
        db_path = self.db_combo.currentData()
        
        if not db_path:
            self.log("Error: No database selected.")
            return
            
        if not os.path.exists(db_path):
            self.log(f"Error: Database file not found at {db_path}")
            return
            
        self.run_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.statusBar().showMessage(f"Executing {algo}...")
        self.log("Initializing algorithm execution...")
        self.results_table.setRowCount(0)
        self.result_filter.clear()
        
        self.worker = AlgoWorker(algo, db_path, "Hierarchical" in algo)
        self.worker.log.connect(self.log)
        self.worker.results_ready.connect(lambda r: self.raw_results_output.setText(r))
        self.worker.data_ready.connect(self.display_structured_results)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def display_structured_results(self, rows, headers):
        """Populates the QTableWidget with the results with safety limit."""
        self.results_table.setSortingEnabled(False)
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Row limit for performance
        MAX_ROWS = 5000
        display_rows = rows[:MAX_ROWS]
        self.results_table.setRowCount(len(display_rows))
        
        for i, row in enumerate(display_rows):
            # Check if this row is an aggregation (Level > 0)
            is_aggr = False
            try:
                if str(row[0]) != "0" and str(row[0]) != "Level" and "=" not in str(row[0]):
                    is_aggr = True
            except: pass
            
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                
                # Highlight Level column, 'ALL' cells, or aggregated row dimensions
                is_all = "ALL" in str(val).upper()
                
                if is_all or (is_aggr and 0 <= j < len(row) - 1):
                    item.setForeground(QColor('gray'))
                    if is_all:
                        item.setToolTip("Aggregated dimension")
                
                self.results_table.setItem(i, j, item)
        
        if len(rows) > MAX_ROWS:
            self.log(f"⚠️ Warning: Too many results ({len(rows)}). Only showing first {MAX_ROWS} in table.")
            
        self.results_table.setSortingEnabled(True)

    def filter_results(self):
        """Hides rows based on search text AND toggle."""
        search_text = self.result_filter.text().lower()
        hide_all = self.hide_all_checkbox.isChecked()
        
        for i in range(self.results_table.rowCount()):
            match = (search_text == "")
            is_aggregated = False
            
            for j in range(self.results_table.columnCount()):
                item = self.results_table.item(i, j)
                if not item: continue
                text = item.text()
                
                # Check for ALL in any dimension column (skip Level and Measure columns for 'ALL' check)
                if 0 < j < self.results_table.columnCount() - 1:
                    if "ALL" in text.upper():
                        is_aggregated = True
                
                if search_text and search_text in text.lower():
                    match = True
            
            should_hide = (not match) or (hide_all and is_aggregated)
            self.results_table.setRowHidden(i, should_hide)

    def on_finished(self, exec_time, message):
        self.run_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.log(message)
        self.log(f"Execution Time: {exec_time:.4f} seconds")
        self.statusBar().showMessage(f"Completed in {exec_time:.4f}s")
        # Automatically switch to Results tab
        if self.results_table.rowCount() > 0:
            self.runner_tabs.setCurrentIndex(1)

    def run_comparison(self):
        """Handles the multi-algo multi-db comparison logic."""
        selected_algos = [cb.text() for cb in self.algo_checks if cb.isChecked()]
        selected_dbs = []
        for i in range(self.db_list_widget.count()):
            item = self.db_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_dbs.append((item.text(), item.data(Qt.ItemDataRole.UserRole)))
        
        if not selected_algos or not selected_dbs:
            self.statusBar().showMessage("Error: Select at least one algo and one database.")
            return

        self.comp_log.clear()
        self.comp_log.append(f"Starting analysis of {len(selected_algos)} algos on {len(selected_dbs)} databases...")
        
        if self.radio_cache.isChecked():
            self.process_cache_comparison(selected_algos, selected_dbs)
        else:
            self.process_live_comparison(selected_algos, selected_dbs)

    def process_cache_comparison(self, algos, dbs):
        """Loads data from existing JSON files in Assets/ExecutionTime."""
        results = {}
        for algo in algos:
            results[algo] = {}
            # Try to find JSON for this algo
            algo_dir = os.path.join(project_root, "Assets", "ExecutionTime", algo.replace("-", "").replace(" ", ""))
            
            for db_name, db_path in dbs:
                actual_db_name = db_name
                is_hier_algo = "Hierarchical" in algo
                
                if self.check_smart_match.isChecked():
                    is_hier_db = "hierarchie" in db_name.lower()
                    if is_hier_algo and not is_hier_db:
                        actual_db_name = db_name.replace("cosky_db", "hierarchie_db")
                    elif not is_hier_algo and is_hier_db:
                        actual_db_name = db_name.replace("hierarchie_db", "cosky_db")

                row_match = re.search(r"_R(\d+)", actual_db_name)
                if not row_match: continue
                rows = int(row_match.group(1))
                
                found = False
                if os.path.exists(algo_dir):
                    for json_file in glob.glob(os.path.join(algo_dir, "*.json")):
                        try:
                            with open(json_file, "r") as f:
                                data = json.load(f)
                                # Handle both flat and nested 'time_data' format
                                time_source = data.get("time_data", data)
                                if str(rows) in time_source:
                                    val = time_source[str(rows)]
                                    # Handle if value is a list (from benchmark.py) or a single float
                                    results[algo][rows] = val[0] if isinstance(val, list) else val
                                    found = True
                                    self.comp_log.append(f"📁 Found cache for {algo} on {db_name} in {os.path.basename(json_file)}")
                                    break
                        except Exception as e:
                            self.comp_log.append(f"❌ Error reading {json_file}: {str(e)}")
                
                if not found:
                    self.comp_log.append(f"⚠️ No cached data found for {algo} on {db_name}")

        self.display_comparison_results(results)

    def process_live_comparison(self, algos, dbs):
        """Sequentially runs algorithms to collect fresh data."""
        self.compare_btn.setEnabled(False)
        self.statusBar().showMessage("Live comparison in progress...")
        
        self.batch_worker = BatchWorker(algos, dbs, smart_match=self.check_smart_match.isChecked())
        self.batch_worker.progress.connect(lambda msg: self.comp_log.append(msg))
        self.batch_worker.finished.connect(self.on_batch_finished)
        self.batch_worker.error.connect(lambda err: self.comp_log.append(f"🔴 Batch Error: {err}"))
        self.batch_worker.start()

    def on_batch_finished(self, results):
        self.compare_btn.setEnabled(True)
        self.statusBar().showMessage("Batch analysis complete.")
        self.display_comparison_results(results)

    def display_comparison_results(self, results):
        """Plots the results on the canvas and generates LaTeX export."""
        self.canvas.axes.clear()
        self.canvas.axes.set_title("Performance Comparison (Preview)")
        self.canvas.axes.set_xlabel("Row Count")
        self.canvas.axes.set_ylabel("Execution Time (s)")
        self.canvas.axes.grid(True, linestyle='--', alpha=0.7)
        
        has_data = False
        export_data = {}
        
        for algo, data in results.items():
            if not data: continue
            has_data = True
            export_data[algo] = {}
            
            # Sort by row count
            sorted_rows = sorted(data.keys())
            sorted_times = [data[r] for r in sorted_rows]
            self.canvas.axes.plot(sorted_rows, sorted_times, marker='o', label=algo)
            
            # Prepare for LaTeX
            for r in sorted_rows:
                export_data[algo][f"db_R{r}"] = {"duration_seconds": data[r], "success": True}
        
        if has_data:
            self.canvas.axes.legend()
            self.canvas.draw()
            
            # Export to LaTeX
            temp_json = os.path.join(project_root, "Assets", "last_comparison.json")
            with open(temp_json, "w") as f:
                json.dump(export_data, f)
            
            # Determine sub-folder based on algorithm count
            count_map = {1: "oneAlgo", 2: "twoAlgos", 3: "threeAlgos", 4: "fourAlgos", 5: "fiveAlgos"}
            algo_count = len(results)
            sub_folder_name = count_map.get(algo_count, f"{algo_count}Algos")
            
            output_folder = os.path.join(project_root, "Assets", "LatexReports", sub_folder_name)
            os.makedirs(output_folder, exist_ok=True)
            
            # Generate filename including ALL algorithms
            safe_algos = [re.sub(r'[^a-zA-Z0-9]', '_', a) for a in results.keys()]
            report_name = f"{'_vs_'.join(safe_algos)}.tex"
            report_path = os.path.join(output_folder, report_name)
            
            self.latex_maker.generate_custom_comparison(
                temp_json, 
                report_path, 
                list(results.keys()), 
                "Performance Comparison Preview"
            )
            self.comp_log.append(f"✅ Preview updated and LaTeX exported to {report_path}")
        else:
            self.comp_log.append("❌ No data available to plot.")
            self.canvas.draw()

    def on_error(self, error_msg):
        self.run_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.log(f"Error: {error_msg}")
        self.statusBar().showMessage("Error occurred")

def main():
    app = QApplication(sys.argv)
    window = AppUIPyQT()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
