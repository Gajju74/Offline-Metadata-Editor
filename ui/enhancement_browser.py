from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox, QProgressDialog
from PySide6.QtCore import Qt, QThread, Signal
import os
import mimetypes
from datetime import datetime
from PIL import Image, ImageEnhance
import torch
from py_real_esrgan.model import RealESRGAN

SUPPORTED_ENHANCEMENT_FORMATS = (".jpg", ".jpeg", ".png", ".bmp")  # Only image formats for now

class EnhancementWorker(QThread):
    progress_updated = Signal(int)
    enhancement_done = Signal()

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks

    def run(self):
        model = RealESRGAN(device="cpu")
        model.load_weights("models/RealESRGAN_x4plus.pth")

        for i, (file_path, choice) in enumerate(self.tasks):
            output_path = os.path.splitext(file_path)[0] + "_enhanced.png"
            if "Upscale" in choice:
                img = Image.open(file_path).convert("RGB")
                result = model.predict(img)
                result.save(output_path)
            elif "Sharpen" in choice:
                level = 1.3 if "Low" in choice else 1.8
                img = Image.open(file_path)
                enhancer = ImageEnhance.Sharpness(img)
                result = enhancer.enhance(level)
                result.save(output_path)

            self.progress_updated.emit(i + 1)

        self.enhancement_done.emit()

class EnhancementBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.setWindowTitle("Enhancement Tool")
        self.setMinimumSize(1300, 900)
        self.go_back_callback = go_back_callback
        self.current_folder = None

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        header_layout = QHBoxLayout()

        heading = QLabel("AI Enhancement")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 25px;
            color: #66afe9;
            padding-top: 10px;
        """)
        layout.addWidget(heading)

        if self.go_back_callback:
            back_button = QPushButton("← Back")
            back_button.setFixedSize(80, 35)
            back_button.clicked.connect(self.go_back_callback)
            header_layout.addWidget(back_button)

        self.import_button = QPushButton("📁 Import Folder")
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(lambda: self.import_folder())

        self.start_button = QPushButton("Start Enhancement")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.run_enhancement)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.clicked.connect(self.refresh_folder)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.start_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "Type", "Size (MB)", "Modified", "Enhancement"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def import_folder(self, folder=None):
        if folder is None:
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

    def refresh_folder(self):
        if self.current_folder and os.path.isdir(self.current_folder):
            self.import_folder(self.current_folder)

    # def run_enhancement(self):
    #     results = []
    #     for row in range(self.table.rowCount()):
    #         combo: QComboBox = self.table.cellWidget(row, 4)
    #         file_path = combo.property("file_path")
    #         choice = combo.currentText()

    #         if choice != "None":
    #             results.append((file_path, choice))

    #     if not results:
    #         QMessageBox.information(self, "No Enhancement", "No files were selected for enhancement.")
    #         return

    #     self.progress_dialog = QProgressDialog("Enhancing images...", "Cancel", 0, len(results), self)
    #     self.progress_dialog.setWindowModality(Qt.WindowModal)
    #     self.progress_dialog.setMinimumDuration(0)
    #     self.progress_dialog.setValue(0)

    #     self.worker = EnhancementWorker(results)
    #     self.worker.progress_updated.connect(self.progress_dialog.setValue)
    #     self.worker.enhancement_done.connect(self.on_enhancement_done)
    #     self.worker.start()

    def run_enhancement(self):
        results = []
        for row in range(self.table.rowCount()):
            combo: QComboBox = self.table.cellWidget(row, 4)
            file_path = combo.property("file_path")
            choice = combo.currentText()

            if choice != "None":
                results.append((file_path, choice))

        if not results:
            QMessageBox.information(self, "No Enhancement", "No files were selected for enhancement.")
            return

        self.progress_dialog = QProgressDialog("Enhancing images...", "Cancel", 0, len(results), self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)

        self.progress_dialog.setMinimumWidth(400)
        self.worker = EnhancementWorker(results)
        self.worker.progress_updated.connect(self.progress_dialog.setValue)
        self.worker.enhancement_done.connect(self.on_enhancement_done)
        self.worker.start()

    def on_enhancement_done(self):
        self.progress_dialog.close()
        QMessageBox.information(self, "Done", "Enhancement complete.")
