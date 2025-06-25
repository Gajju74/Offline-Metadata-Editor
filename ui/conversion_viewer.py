# ui/conversion_viewer.py
import os
import datetime
import subprocess
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt
from services.conversion_service import batch_convert_folder
from ui.conversion import SUPPORTED_IMAGE_FORMATS, SUPPORTED_VIDEO_FORMATS

class ConversionViewer(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.setMinimumSize(1300, 900)
        self.setWindowTitle("🌀 Bulk File Format Converter")

        layout = QVBoxLayout(self)

        # --- Top Bar ---
        top_bar = QHBoxLayout()
        if self.go_back_callback:
            back_btn = QPushButton("← Back")
            back_btn.setFixedSize(100, 40)
            back_btn.clicked.connect(self.go_back_callback)
            top_bar.addWidget(back_btn)

        # Import Folder Button
        self.folder_btn = QPushButton("📁 Import Folder")
        self.folder_btn.setFixedSize(140, 40)
        self.folder_btn.clicked.connect(self.import_folder)
        top_bar.addWidget(self.folder_btn)

        # Format Dropdown
        self.format_dropdown = QComboBox()
        self.format_dropdown.setFixedSize(140, 40)
        self.format_dropdown.addItem("Select output format")
        for fmt in SUPPORTED_IMAGE_FORMATS + SUPPORTED_VIDEO_FORMATS:
            self.format_dropdown.addItem(fmt.lstrip("."))
        top_bar.addWidget(self.format_dropdown)

        # Convert Button
        self.convert_btn = QPushButton("🔁 Convert")
        self.convert_btn.setFixedSize(100, 40)
        self.convert_btn.clicked.connect(self.run_bulk_conversion)
        top_bar.addWidget(self.convert_btn)

        # Refresh Button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setFixedSize(100, 40)
        self.refresh_button.clicked.connect(self.refresh_folder)
        top_bar.addWidget(self.refresh_button)


        # Download All Button
        self.download_all_btn = QPushButton("⬇️ Download All")
        self.download_all_btn.setFixedSize(140, 40)
        self.download_all_btn.clicked.connect(self.download_all_files)
        top_bar.addWidget(self.download_all_btn)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "File Type", "Size (MB)", "Date Modified", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.folder_path = None
        self.converted_file_paths = []

    def refresh_folder(self):
        self.table.setRowCount(0)
        self.converted_file_paths = []
        self.folder_path = None
        self.format_dropdown.setCurrentIndex(0)
        QMessageBox.information(self, "Reset", "View has been cleared.")


    def import_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_path = folder_path
            QMessageBox.information(self, "Folder Selected", f"Folder: {folder_path}")

    def run_bulk_conversion(self):
        if not self.folder_path:
            QMessageBox.warning(self, "No Folder", "Please select a folder first.")
            return

        output_format = self.format_dropdown.currentText().strip()
        if output_format == "Select output format":
            QMessageBox.warning(self, "No Format", "Please select an output format.")
            return

        output_dir = os.path.join(self.folder_path, "converted_output")
        results = batch_convert_folder(self.folder_path, output_format, output_dir=output_dir)

        self.converted_file_paths = []
        self.table.setRowCount(0)

        row = 0
        for result in results:
            if "result" in result:
                file_path = result["result"]
                if os.path.isfile(file_path):
                    self.converted_file_paths.append(file_path)
                    file_info = os.stat(file_path)
                    file_name = os.path.basename(file_path)
                    file_type = os.path.splitext(file_name)[1].lstrip(".")
                    file_size = f"{file_info.st_size / (1024 * 1024):.2f}"
                    modified = datetime.datetime.fromtimestamp(file_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(file_name))
                    self.table.setItem(row, 1, QTableWidgetItem(file_type))
                    self.table.setItem(row, 2, QTableWidgetItem(file_size))
                    self.table.setItem(row, 3, QTableWidgetItem(modified))

                    download_btn = QPushButton("Download")
                    download_btn.clicked.connect(lambda _, path=file_path: os.startfile(path))
                    self.table.setCellWidget(row, 4, download_btn)

                    row += 1

        if not self.converted_file_paths:
            QMessageBox.information(self, "Conversion Complete", "No valid files converted.")
        else:
            QMessageBox.information(self, "Success", f"{len(self.converted_file_paths)} file(s) converted.")

    def download_all_files(self):
        if not self.converted_file_paths:
            QMessageBox.warning(self, "No Files", "There are no converted files to download.")
            return

        output_dir = os.path.dirname(self.converted_file_paths[0])
        try:
            os.startfile(output_dir)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open folder:\n{e}")
