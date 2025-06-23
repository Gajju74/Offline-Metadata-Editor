# ui/metadata_viewer.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QDateTimeEdit,
    QPushButton, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, QDateTime
import mimetypes
import subprocess
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

        layout.addWidget(QLabel(f"Viewing Metadata: {file_path}"))

        # Scrollable form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.form_layout = QFormLayout()
        container.setLayout(self.form_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        self.populate_fields()

        # Buttons
        self.save_button = QPushButton("💾 Save Changes")
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
            # skip dict/list values for now

    def save_metadata(self):
        args = ["exiftool", "-overwrite_original"]

        for key, widget in self.field_widgets.items():
            # Skip keys that can't be written or are known system-level
            if key.lower() in ["file name", "file size (mb)", "error", "warning"]:
                continue

            if isinstance(widget, QLineEdit):
                val = widget.text()
            elif isinstance(widget, QDateTimeEdit):
                val = widget.dateTime().toString("yyyy:MM:dd HH:mm:ss")
            else:
                continue

            # Escape key names with = signs
            sanitized_key = key.replace(" ", "")
            args.append(f"-{sanitized_key}={val}")

        args.append(self.file_path)

        try:
            subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            QMessageBox.information(self, "Success", "Metadata saved successfully.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to save metadata:\n{e.stderr.decode()}")
