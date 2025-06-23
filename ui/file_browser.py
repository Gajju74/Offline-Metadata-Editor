# ui/file_browser.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView, QHBoxLayout
)
from PySide6.QtCore import Qt
import os
import mimetypes
from datetime import datetime
from ui.metadata_viewer import MetadataViewer

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov", ".avi", ".mkv")


class FileBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1600, 900)
        self.setWindowTitle("📁 Folder Import – Offline Metadata Editor")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        # Top Section
        header_layout = QHBoxLayout()
        self.import_button = QPushButton("📁 Import Folder")
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(self.import_folder)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")
        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "File Type", "Size (MB)", "Date Modified", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #f0f0f0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QLabel {
                color: #f0f0f0;
            }
            QTableWidget {
                background-color: #2a2a2a;
                border-radius: 8px;
                gridline-color: #444;
                alternate-background-color: #2f2f2f;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                font-weight: bold;
                padding: 8px;
                border: none;
                color: #ffffff;
                border-right: 1px solid #444;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #3a3a3a;
                border: none;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555;
                color: #fff;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)


        # Add widgets to layout
        layout.addLayout(header_layout)
        layout.addWidget(self.table)

    def import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.folder_label.setText(f"Imported: {folder}")
        self.table.setRowCount(0)

        for entry in os.listdir(folder):
            full_path = os.path.join(folder, entry)
            if not os.path.isfile(full_path):
                continue

            ext = os.path.splitext(entry)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
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

            # View/Edit Button
            btn = QPushButton("View/Edit")
            btn.setProperty("file_path", full_path)
            btn.clicked.connect(self.handle_view_edit_click)
            self.table.setCellWidget(row, 4, btn)

    def handle_view_edit_click(self):
        button = self.sender()
        file_path = button.property("file_path")

        viewer = MetadataViewer(file_path, self)
        viewer.exec()



    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item
