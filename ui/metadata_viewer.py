# ui/metadata_viewer.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QDateTimeEdit,
    QPushButton, QScrollArea, QWidget, QFileDialog, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt, QDateTime
import mimetypes
import subprocess
import os
import re
from services.image_metadata import read_image_metadata
from services.video_metadata import read_video_metadata


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

        # Top Bar with Copy/Import Metadata
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel(f"File: {file_path}"))
        top_bar.addStretch()

        self.copy_btn = QPushButton("📋 Copy Metadata")
        self.copy_btn.clicked.connect(self.copy_metadata_to_other_file)
        top_bar.addWidget(self.copy_btn)

        self.import_btn = QPushButton("📥 Import Metadata (in_progress)")
        self.import_btn.clicked.connect(self.import_metadata_from_txt)
        top_bar.addWidget(self.import_btn)

        layout.addLayout(top_bar)

        # Scrollable metadata form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.form_layout = QFormLayout()
        container.setLayout(self.form_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        self.populate_fields()

        self.save_button = QPushButton("💾 Save Metadata")
        self.save_button.clicked.connect(self.save_metadata)
        layout.addWidget(self.save_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

    def load_metadata(self):
        mime_type, _ = mimetypes.guess_type(self.file_path)
        if mime_type and mime_type.startswith("video"):
            return read_video_metadata(self.file_path)
        return read_image_metadata(self.file_path)

    def populate_fields(self):
        for key, value in self.metadata.items():
            label = QLabel(key)

            if "Date" in key and isinstance(value, str):
                field = QDateTimeEdit()
                field.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
                dt = QDateTime.fromString(value, "yyyy-MM-dd HH:mm:ss")
                if not dt.isValid():
                    dt = QDateTime.fromString(value, "yyyy:MM:dd hh:mm:ss")
                if dt.isValid():
                    field.setDateTime(dt)
                else:
                    field.setSpecialValueText(value)
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
            if isinstance(widget, QLineEdit):
                val = widget.text()
            elif isinstance(widget, QDateTimeEdit):
                val = widget.dateTime().toString("yyyy:MM:dd HH:mm:ss")
            else:
                continue

            sanitized_key = key.replace(" ", "")
            args.append(f"-{sanitized_key}={val}")

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

        # Step 1: Save current metadata of target as .txt
        backup_txt = os.path.splitext(target_file)[0] + ".txt"
        mime_type, _ = mimetypes.guess_type(target_file)
        try:
            if mime_type and mime_type.startswith("video"):
                target_metadata = read_video_metadata(target_file)
            else:
                target_metadata = read_image_metadata(target_file)

            with open(backup_txt, "w", encoding="utf-8") as f:
                for k, v in target_metadata.items():
                    f.write(f"{k}: {v}\n")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to back up target metadata:\n{e}")
            return

        # Step 2: Apply source metadata to target using exiftool
        args = ["exiftool", "-overwrite_original", f"-tagsFromFile={self.file_path}", target_file]
        try:
            subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            QMessageBox.information(self, "Copied", f"Metadata copied to:\n{target_file}")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to copy metadata:\n{e.stderr.decode()}")

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

                    # Split only on first colon that's surrounded by space(s)
                    match = re.match(r"^(.*?):\s*(.*)$", line.strip())
                    if not match:
                        continue

                    key = match.group(1).strip().replace(" ", "")
                    val = match.group(2).strip()

                    if key.lower() in ["filename", "filesize", "error", "warning"]:
                        continue

                    args.append(f"-{key}={val}")

            args.append(self.file_path)

            subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            QMessageBox.information(self, "Imported", "Metadata imported successfully from TXT.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "ExifTool Error", e.stderr.decode())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


