# app/ui/main_window.py

from PySide6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from .metadata_editor import MetadataEditor
from .batch_processor import BatchProcessor
from .templates_manager import TemplatesManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline File Metadata Editor & Converter")
        self.setMinimumSize(1000, 700)

        # Create tab widget
        tabs = QTabWidget()
        tabs.addTab(MetadataEditor(), "Metadata Editor")
        tabs.addTab(BatchProcessor(), "Batch Processing")
        tabs.addTab(TemplatesManager(), "Templates")

        self.setCentralWidget(tabs)
        self.setStatusBar(QStatusBar())

