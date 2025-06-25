# templates_manager.py

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class TemplatesManager(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🧰 Metadata Templates Manager (Coming soon)"))
        self.setLayout(layout)
