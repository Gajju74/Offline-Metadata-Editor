from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QStackedLayout, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox
from PySide6.QtCore import Qt
import os
import mimetypes
from datetime import datetime

SUPPORTED_ENHANCEMENT_FORMATS = (".jpg", ".jpeg", ".png", ".bmp", ".mp4", ".mov", ".avi")

class EnhancementBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.setWindowTitle("🧠 AI Enhancement Tool")
        self.setMinimumSize(1300, 900)
        self.go_back_callback = go_back_callback
        self.current_folder = None

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        # Header
        header_layout = QHBoxLayout()

        if self.go_back_callback:
            back_button = QPushButton("← Back")
            back_button.setFixedSize(80, 35)
            back_button.clicked.connect(self.go_back_callback)
            header_layout.addWidget(back_button)

        self.import_button = QPushButton("📁 Import Folder")
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(self.import_folder)

        self.start_button = QPushButton("🚀 Start Enhancement")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.run_enhancement)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.start_button)
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "Type", "Size (MB)", "Modified", "Enhancement"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.folder_label.setText(f"Imported: {folder}")
        self.table.setRowCount(0)
        self.current_folder = folder

        for entry in os.listdir(folder):
            full_path = os.path.join(folder, entry)
            if not os.path.isfile(full_path):
                continue

            ext = os.path.splitext(entry)[1].lower()
            if ext not in SUPPORTED_ENHANCEMENT_FORMATS:
                continue

            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
            mime, _ = mimetypes.guess_type(full_path)

            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, self._non_editable_item(entry))
            self.table.setItem(row, 1, self._non_editable_item(mime or ext))
            self.table.setItem(row, 2, self._non_editable_item(f"{size_mb:.2f}"))
            self.table.setItem(row, 3, self._non_editable_item(modified))

            combo = QComboBox()
            combo.addItems(["None", "Upscale 2x", "Upscale 4x", "Sharpen (Low)", "Sharpen (High)"])
            combo.setProperty("file_path", full_path)
            self.table.setCellWidget(row, 4, combo)

    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def run_enhancement(self):
        results = []
        for row in range(self.table.rowCount()):
            combo: QComboBox = self.table.cellWidget(row, 4)
            file_path = combo.property("file_path")
            choice = combo.currentText()

            if choice == "None":
                continue

            results.append((file_path, choice))

        if not results:
            QMessageBox.information(self, "No Enhancement", "No files were selected for enhancement.")
            return

        QMessageBox.information(self, "Queued", f"Queued {len(results)} file(s) for enhancement.")
        # TODO: Call processing logic for each (file_path, choice) entry
        # Example: if choice == "Upscale 2x": use realesrgan 2x
        # Will be implemented next
