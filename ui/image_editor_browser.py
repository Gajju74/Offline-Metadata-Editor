# ui/image_editor_browser.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QDialog, QScrollArea, QSizePolicy, QSlider, QMessageBox
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QMouseEvent
from PySide6.QtCore import Qt, QRect, QPoint
import os
import mimetypes
from datetime import datetime

SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".heic", ".bmp")

class ImageEditorBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.setWindowTitle("Image Editor")
        self.setMinimumSize(1300, 900)
        self.go_back_callback = go_back_callback
        self.current_folder = None

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        # Header Layout
        header_layout = QHBoxLayout()

        heading = QLabel("Image Editor")
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

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "Type", "Size (MB)", "Modified", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def import_folder(self, folder=None):
        folder = folder or QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.current_folder = folder
        self.folder_label.setText(f"Imported: {folder}")
        self.table.setRowCount(0)

        for entry in os.listdir(folder):
            full_path = os.path.join(folder, entry)
            if not os.path.isfile(full_path):
                continue

            ext = os.path.splitext(entry)[1].lower()
            if ext not in SUPPORTED_IMAGE_FORMATS:
                continue

            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
            mime, _ = mimetypes.guess_type(full_path)

            row = self.table.rowCount()
            self.table.insertRow(row)

            checkbox = QCheckBox(entry)
            checkbox.setProperty("file_path", full_path)
            self.table.setCellWidget(row, 0, checkbox)

            self.table.setItem(row, 1, self._non_editable_item(mime or ext))
            self.table.setItem(row, 2, self._non_editable_item(f"{size_mb:.2f}"))
            self.table.setItem(row, 3, self._non_editable_item(modified))

            btn = QPushButton("Edit")
            btn.setProperty("file_path", full_path)
            btn.clicked.connect(self.open_editor)
            self.table.setCellWidget(row, 4, btn)

    def refresh_folder(self):
        if self.current_folder:
            self.import_folder(self.current_folder)


    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def open_editor(self):
        sender = self.sender()
        file_path = sender.property("file_path")

        dialog = QDialog(self)
        dialog.setWindowTitle("Image Viewer")
        dialog.setMinimumSize(1000, 700)

        layout = QVBoxLayout(dialog)

        class CropLabel(QLabel):
            def __init__(self, pixmap):
                super().__init__()
                self.original_pixmap = pixmap
                self.setPixmap(pixmap)
                self.setAlignment(Qt.AlignCenter)
                self.start = self.end = None
                self.crop_rect = None

            def mousePressEvent(self, event: QMouseEvent):
                self.start = event.pos()
                self.end = self.start
                self.update()

            def mouseMoveEvent(self, event: QMouseEvent):
                self.end = event.pos()
                self.update()

            def mouseReleaseEvent(self, event: QMouseEvent):
                self.end = event.pos()
                self.crop_rect = QRect(self.start, self.end).normalized()
                self.update()

            def paintEvent(self, event):
                super().paintEvent(event)
                if self.start and self.end:
                    painter = QPainter(self)
                    pen = QPen(QColor(0, 120, 215), 2, Qt.DashLine)
                    painter.setPen(pen)
                    painter.drawRect(QRect(self.start, self.end))

            def get_mapped_crop_rect(self):
                if not self.crop_rect:
                    return None

                displayed_pixmap = self.pixmap()
                if displayed_pixmap is None:
                    return None

                # Dimensions
                label_width = self.width()
                label_height = self.height()
                pixmap_width = displayed_pixmap.width()
                pixmap_height = displayed_pixmap.height()

                # Offset if pixmap is centered in label
                offset_x = max(0, (label_width - pixmap_width) // 2)
                offset_y = max(0, (label_height - pixmap_height) // 2)

                # Adjust crop rect relative to pixmap position
                adjusted = QRect(
                    self.crop_rect.x() - offset_x,
                    self.crop_rect.y() - offset_y,
                    self.crop_rect.width(),
                    self.crop_rect.height()
                )

                # Scale to original pixmap dimensions
                ratio_x = self.original_pixmap.width() / pixmap_width
                ratio_y = self.original_pixmap.height() / pixmap_height

                return QRect(
                    int(adjusted.x() * ratio_x),
                    int(adjusted.y() * ratio_y),
                    int(adjusted.width() * ratio_x),
                    int(adjusted.height() * ratio_y)
                ).normalized()

        pixmap = QPixmap(file_path)

        image_label = CropLabel(pixmap)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(image_label)
        layout.addWidget(scroll)

        zoom_slider = QSlider(Qt.Horizontal)
        zoom_slider.setRange(10, 300)
        zoom_slider.setValue(100)
        layout.addWidget(zoom_slider)

        def update_image(scale_percent):
            factor = scale_percent / 100.0
            scaled = pixmap.scaled(pixmap.size() * factor, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled)
            image_label.resize(scaled.size())

        zoom_slider.valueChanged.connect(update_image)
        update_image(zoom_slider.value())



        def crop_image():
            mapped_rect = image_label.get_mapped_crop_rect()
            if not mapped_rect or mapped_rect.width() <= 0 or mapped_rect.height() <= 0:
                QMessageBox.warning(dialog, "Invalid Crop", "Calculated crop area is empty.")
                return

            # Crop from original pixmap
            cropped = pixmap.copy(mapped_rect)

            # Update label and UI
            image_label.original_pixmap = cropped
            image_label.setPixmap(cropped)
            image_label.crop_rect = None
            update_image(zoom_slider.value())

            # Save cropped image
            base, ext = os.path.splitext(file_path)
            cropped_path = f"{base}_cropped.png"  # force PNG to test

            print("Saving cropped image to:", cropped_path)
            print("Cropped size:", cropped.size())
            print("IsNull:", cropped.isNull())

            success = cropped.save(cropped_path, "PNG")  # try forcing format
            if success:
                QMessageBox.information(dialog, "Image Saved", f"Cropped image saved to:\n{cropped_path}")
            else:
                QMessageBox.critical(dialog, "Save Failed", f"Could not save image to:\n{cropped_path}")


            # print(f"Crop rect: {rect.x()}, {rect.y()}, {rect.width()}, {rect.height()}")
            # print(f"Crop coords on original: {x}, {y}, {w}, {h}")

        crop_btn = QPushButton("✂ Crop")
        layout.addWidget(crop_btn)
        crop_btn.clicked.connect(crop_image)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

