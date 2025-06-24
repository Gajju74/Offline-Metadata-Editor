# batch_processor.py

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class BatchProcessor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📦 Batch Processing Interface (Coming soon)"))
        self.setLayout(layout)
