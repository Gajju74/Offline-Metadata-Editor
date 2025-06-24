import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView
)
from PySide6.QtCore import Qt

from app.core.metadata_image import read_image_metadata, write_image_metadata
from app.core.metadata_video import read_video_metadata, write_video_metadata
from app.core.file_handler import is_supported_image, is_supported_video


class MetadataEditor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("📁 View & Edit File Metadata")
        self.resize(900, 600)

        # Layout setup
        self.layout = QVBoxLayout()

        # Label and upload button
        self.label = QLabel("Select a file to view and edit metadata")
        self.upload_button = QPushButton("📤 Upload File")
        self.upload_button.clicked.connect(self.select_file)

        # Table setup
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.metadata_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.metadata_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.metadata_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.metadata_table.setWordWrap(True)
        self.metadata_table.setAlternatingRowColors(True)
        self.metadata_table.setSelectionMode(QTableWidget.NoSelection)

        # Save button
        self.save_button = QPushButton("💾 Save Metadata")
        self.save_button.clicked.connect(self.save_metadata)

        # Assemble layout
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.upload_button)
        self.layout.addWidget(self.metadata_table)
        self.layout.addWidget(self.save_button)
        self.setLayout(self.layout)

        self.current_file = None

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "Media Files (*.jpg *.jpeg *.png *.mp4 *.avi *.mov)"
        )
        if file:
            self.current_file = file
            file_type = "Image" if is_supported_image(file) else "Video" if is_supported_video(file) else "Unknown"
            self.label.setText(f"📄 File: {os.path.basename(file)} | Type: {file_type}")
            self.load_metadata(file)

    def load_metadata(self, file):
        self.metadata_table.setRowCount(0)

        metadata = {}
        if is_supported_image(file):
            metadata = read_image_metadata(file)
        elif is_supported_video(file):
            metadata = read_video_metadata(file)
        else:
            self.label.setText("❌ Unsupported file type.")
            return

        for row, (key, value) in enumerate(metadata.items()):
            self.metadata_table.insertRow(row)

            key_item = QTableWidgetItem(str(key))
            key_item.setFlags(Qt.ItemIsEnabled)
            key_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)

            val_item = QTableWidgetItem(str(value))
            val_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            val_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            val_item.setToolTip(str(value))

            self.metadata_table.setItem(row, 0, key_item)
            self.metadata_table.setItem(row, 1, val_item)

    def save_metadata(self):
        if not self.current_file:
            return

        updated_metadata = {}
        for row in range(self.metadata_table.rowCount()):
            key = self.metadata_table.item(row, 0).text()
            value = self.metadata_table.item(row, 1).text()
            updated_metadata[key] = value

        file_type = "Image" if is_supported_image(self.current_file) else "Video"

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Updated File", self.current_file)
        if not save_path:
            return

        try:
            if file_type == "Image":
                write_image_metadata(self.current_file, updated_metadata, save_path)
            elif file_type == "Video":
                write_video_metadata(self.current_file, save_path, updated_metadata)

            self.label.setText(f"✅ Metadata saved to: {os.path.basename(save_path)}")
        except Exception as e:
            self.label.setText(f"❌ Failed to save metadata: {str(e)}")
