from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView, QHBoxLayout
)
from PySide6.QtCore import Qt
import os
import mimetypes
from datetime import datetime

SUPPORTED_VIDEO_FORMATS = (".mp4", ".avi", ".mov", ".mkv")

class VideoEditorBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.setWindowTitle("🎬 Video Editor Tool")
        self.setMinimumSize(1300, 900)
        self.go_back_callback = go_back_callback
        self.current_folder = None

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        header_layout = QHBoxLayout()

        if self.go_back_callback:
            back_button = QPushButton("← Back")
            back_button.setFixedSize(80, 35)
            back_button.clicked.connect(self.go_back_callback)
            header_layout.addWidget(back_button)

        self.import_button = QPushButton("📁 Import Folder")
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(self.import_folder)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.clicked.connect(self.refresh_folder)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File Name", "Type", "Size (MB)", "Modified"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder or not os.path.isdir(folder):
            return

        self.folder_label.setText(f"Imported: {folder}")
        self.table.setRowCount(0)
        self.current_folder = folder

        for entry in os.listdir(folder):
            full_path = os.path.join(folder, entry)
            if not os.path.isfile(full_path):
                continue

            ext = os.path.splitext(entry)[1].lower()
            if ext not in SUPPORTED_VIDEO_FORMATS:
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

    def refresh_folder(self):
        if self.current_folder and os.path.isdir(self.current_folder):
            self.import_folder()

    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item
