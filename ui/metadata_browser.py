# metadata_browser.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QHBoxLayout, QMessageBox, QCheckBox, QDialog, QScrollArea,
    QFormLayout, QLineEdit, QDateTimeEdit
)
from PySide6.QtCore import Qt, QDateTime
import os
import mimetypes
import subprocess
import re
from datetime import datetime
from services.image_metadata import read_image_metadata
from services.video_metadata import read_video_metadata

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov", ".avi", ".mkv")

class NoScrollDateTimeEdit(QDateTimeEdit):
    def wheelEvent(self, event):
        event.ignore()

class MetadataViewer(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Metadata Viewer & Editor")
        self.setMinimumSize(1280, 720)

        self.file_path = file_path
        self.metadata = self.load_metadata()
        self.field_widgets = {}

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Main Heading
        heading = QLabel("📝 Metadata Editor")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #E0E0E0;
        """)
        layout.addWidget(heading)

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel(f"File: {file_path}"))
        top_bar.addStretch()

        copy_btn = QPushButton("\ud83d\udccb Copy Metadata")
        copy_btn.clicked.connect(self.copy_metadata_to_other_file)
        top_bar.addWidget(copy_btn)

        import_btn = QPushButton("\ud83d\udce5 Import Metadata (in_progress)")
        import_btn.clicked.connect(self.import_metadata_from_txt)
        top_bar.addWidget(import_btn)

        layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.form_layout = QFormLayout()
        container.setLayout(self.form_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        self.populate_fields()

        save_button = QPushButton("\ud83d\udcbe Save Metadata")
        save_button.clicked.connect(self.save_metadata)
        layout.addWidget(save_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def load_metadata(self):
        mime_type, _ = mimetypes.guess_type(self.file_path)
        return read_video_metadata(self.file_path) if mime_type and mime_type.startswith("video") else read_image_metadata(self.file_path)

    def populate_fields(self):
        for key, value in self.metadata.items():
            label = QLabel(key)
            if "Date" in key and isinstance(value, str):
                field = NoScrollDateTimeEdit()
                field.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
                dt = QDateTime.fromString(value, "yyyy-MM-dd HH:mm:ss")
                if not dt.isValid():
                    dt = QDateTime.fromString(value, "yyyy:MM:dd hh:mm:ss")
                field.setDateTime(dt if dt.isValid() else QDateTime.currentDateTime())
                self.form_layout.addRow(label, field)
                self.field_widgets[key] = field
            elif isinstance(value, (int, float, str)):
                field = QLineEdit(str(value))
                self.form_layout.addRow(label, field)
                self.field_widgets[key] = field

    def save_metadata(self):
        args = ["exiftool", "-overwrite_original"]
        for key, widget in self.field_widgets.items():
            if key.lower() in ["file name", "file size (mb)", "error", "warning"]:
                continue
            val = widget.text() if isinstance(widget, QLineEdit) else widget.dateTime().toString("yyyy:MM:dd HH:mm:ss")
            args.append(f"-{key.replace(' ', '')}={val}")
        args.append(self.file_path)
        try:
            subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            QMessageBox.information(self, "Success", "Metadata saved successfully.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to save metadata:\n{e.stderr.decode()}")

    def copy_metadata_to_other_file(self):
        target_file, _ = QFileDialog.getOpenFileName(self, "Select Target File")
        if not target_file:
            return
        try:
            mime_type, _ = mimetypes.guess_type(target_file)
            metadata = read_video_metadata(target_file) if mime_type and mime_type.startswith("video") else read_image_metadata(target_file)
            with open(os.path.splitext(target_file)[0] + ".txt", "w", encoding="utf-8") as f:
                for k, v in metadata.items():
                    f.write(f"{k}: {v}\n")
            subprocess.run(["exiftool", "-overwrite_original", f"-tagsFromFile={self.file_path}", target_file],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            QMessageBox.information(self, "Copied", f"Metadata copied to:\n{target_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {e}")

    def import_metadata_from_txt(self):
        txt_file, _ = QFileDialog.getOpenFileName(self, "Select Metadata TXT File", "", "Text Files (*.txt)")
        if not txt_file:
            return
        args = ["exiftool", "-overwrite_original"]
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" not in line:
                        continue
                    match = re.match(r"^(.*?):\s*(.*)$", line.strip())
                    if not match:
                        continue
                    key, val = match.group(1).strip().replace(" ", ""), match.group(2).strip()
                    if key.lower() not in ["filename", "filesize", "error", "warning"]:
                        args.append(f"-{key}={val}")
            args.append(self.file_path)
            subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            QMessageBox.information(self, "Imported", "Metadata imported successfully from TXT.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class MetadataBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.setMinimumSize(1300, 900)
        self.setWindowTitle("\ud83d\udcc1 Folder Import – Offline Metadata Editor")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        header_layout = QHBoxLayout()
        if self.go_back_callback:
            back_button = QPushButton("\u2190 Back")
            back_button.setFixedSize(80, 35)
            back_button.clicked.connect(self.go_back_callback)
            header_layout.addWidget(back_button)

        self.import_button = QPushButton("\ud83d\udcc1 Import Folder")
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(self.import_folder)

        self.export_button = QPushButton("\ud83d\udec4 Export Metadata (TXT)")
        self.export_button.setFixedHeight(40)
        self.export_button.clicked.connect(self.export_selected_metadata)

        self.delete_button = QPushButton("\ud83d\uddd1 Delete Metadata")
        self.delete_button.setFixedHeight(40)
        self.delete_button.clicked.connect(self.delete_selected_metadata)

        self.refresh_button = QPushButton("\ud83d\udd04 Refresh")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.clicked.connect(self.refresh_folder)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.export_button)
        header_layout.addWidget(self.delete_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

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

            checkbox = QCheckBox(entry)
            checkbox.setProperty("file_path", full_path)
            self.table.setCellWidget(row, 0, checkbox)
            self.table.setItem(row, 1, self._non_editable_item(mime or ext))
            self.table.setItem(row, 2, self._non_editable_item(f"{size_mb:.2f}"))
            self.table.setItem(row, 3, self._non_editable_item(modified))

            btn = QPushButton("View/Edit")
            btn.setProperty("file_path", full_path)
            btn.clicked.connect(self.handle_view_edit_click)
            self.table.setCellWidget(row, 4, btn)

    def handle_view_edit_click(self):
        file_path = self.sender().property("file_path")
        viewer = MetadataViewer(file_path, self)
        viewer.exec()

    def refresh_folder(self):
        current = self.folder_label.text()
        if current.startswith("Imported: "):
            self.import_folder(current.replace("Imported: ", ""))

    def export_selected_metadata(self):
        exported = 0
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if not isinstance(checkbox, QCheckBox) or not checkbox.isChecked():
                continue
            path = checkbox.property("file_path")
            metadata = read_video_metadata(path) if mimetypes.guess_type(path)[0].startswith("video") else read_image_metadata(path)
            try:
                with open(os.path.splitext(path)[0] + ".txt", "w", encoding="utf-8") as f:
                    for k, v in metadata.items():
                        f.write(f"{k}: {v}\n")
                exported += 1
            except Exception as e:
                print(f"❌ Failed to export {path}: {e}")
        QMessageBox.information(self, "Export", f"Exported metadata for {exported} file(s)." if exported else "No files selected.")

    def delete_selected_metadata(self):
        deleted = 0
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if not isinstance(checkbox, QCheckBox) or not checkbox.isChecked():
                continue
            path = checkbox.property("file_path")
            try:
                subprocess.run(["exiftool", "-overwrite_original", "-all=", path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                deleted += 1
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to delete metadata for {path}: {e.stderr.decode()}")
        QMessageBox.information(self, "Deleted", f"Deleted metadata for {deleted} file(s)." if deleted else "No files selected.")

    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item
