from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView, QHBoxLayout, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt
import os
import mimetypes
from datetime import datetime
import subprocess
from ui.metadata_viewer import MetadataViewer
from services.image_metadata import read_image_metadata
from services.video_metadata import read_video_metadata

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

        self.export_button = QPushButton("📤 Export Metadata (TXT)")
        self.export_button.setFixedHeight(40)
        self.export_button.clicked.connect(self.export_selected_metadata)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")

        self.delete_button = QPushButton("🗑 Delete Metadata")
        self.delete_button.setFixedHeight(40)
        self.delete_button.clicked.connect(self.delete_selected_metadata)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.clicked.connect(self.refresh_folder)

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.export_button)
        header_layout.addWidget(self.delete_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "File Type", "Size (MB)", "Date Modified", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)

        layout.addLayout(header_layout)
        layout.addWidget(self.table)

    def import_folder(self, folder_path=None):
        folder = folder_path or QFileDialog.getExistingDirectory(self, "Select Folder")
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
            self.table.setRowHeight(row, 30)

            # File Name + Checkbox (in one cell)
            checkbox = QCheckBox(entry)
            checkbox.setProperty("file_path", full_path)
            self.table.setCellWidget(row, 0, checkbox)

            self.table.setItem(row, 1, self._non_editable_item(mime or ext))
            self.table.setItem(row, 2, self._non_editable_item(f"{size_mb:.2f}"))
            self.table.setItem(row, 3, self._non_editable_item(modified))

            # View/Edit Button
            btn = QPushButton("View/Edit")
            btn.setProperty("file_path", full_path)
            btn.clicked.connect(self.handle_view_edit_click)
            self.table.setCellWidget(row, 4, btn)

    def handle_view_edit_click(self):
        from ui.metadata_viewer import MetadataViewer  # Avoid circular import
        button = self.sender()
        file_path = button.property("file_path")
        viewer = MetadataViewer(file_path, self)
        viewer.exec()

    def refresh_folder(self):
        current_folder_text = self.folder_label.text()
        if current_folder_text.startswith("Imported: "):
            folder = current_folder_text.replace("Imported: ", "")
            if os.path.isdir(folder):
                self.import_folder(folder)

    def export_selected_metadata(self):
        exported = 0
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if not isinstance(checkbox, QCheckBox) or not checkbox.isChecked():
                continue

            file_path = checkbox.property("file_path")
            mime_type, _ = mimetypes.guess_type(file_path)

            if mime_type and mime_type.startswith("video"):
                metadata = read_video_metadata(file_path)
            else:
                metadata = read_image_metadata(file_path)

            txt_path = os.path.splitext(file_path)[0] + ".txt"
            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    for key, value in metadata.items():
                        f.write(f"{key}: {value}\n")
                exported += 1
            except Exception as e:
                print(f"❌ Failed to export metadata for {file_path}: {e}")

        if exported:
            QMessageBox.information(self, "Export Complete", f"Exported metadata for {exported} file(s).")
        else:
            QMessageBox.warning(self, "No Files", "No files were selected for export.")

    def delete_selected_metadata(self):
        deleted = 0
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if not isinstance(checkbox, QCheckBox) or not checkbox.isChecked():
                continue

            file_path = checkbox.property("file_path")
            try:
                subprocess.run(["exiftool", "-overwrite_original", "-all=", file_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                deleted += 1
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to delete metadata for {file_path}: {e.stderr.decode()}")

        if deleted:
            QMessageBox.information(self, "Deleted", f"Deleted metadata for {deleted} file(s).")
        else:
            QMessageBox.warning(self, "No Files", "No files were selected for metadata deletion.")

    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item
