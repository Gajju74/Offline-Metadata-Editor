from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QStackedLayout
from PySide6.QtCore import Qt
from ui.file_browser import FileBrowser
from ui.conversion_viewer import ConversionViewer
from ui.noise_browser import NoiseCancellationBrowser  # ✅ import noise tool
from ui.enhancement_browser import EnhancementBrowser

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome AI Metadata Software")
        self.setMinimumSize(1300, 900)

        self.stacked_layout = QStackedLayout(self)

        # --- Dashboard View ---
        self.dashboard_widget = QWidget()
        dash_layout = QVBoxLayout()
        dash_layout.setAlignment(Qt.AlignTop)
        self.dashboard_widget.setLayout(dash_layout)

        heading = QLabel("Welcome AI Metadata Software")
        heading.setStyleSheet("font-size: 24px; font-weight: bold; color: #003399;")
        dash_layout.addWidget(heading)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        metadata_btn = self.create_button("Meta data Editer", self.open_metadata_editor)
        conversion_btn = self.create_button("Conversion Video", self.open_converter)
        audio_btn = self.create_button("Audio noise reduction", self.open_noise_browser)
        enhancement_btn = self.create_button("Enhancement using AI", self.open_enhancement_browser)

        for btn in [metadata_btn, conversion_btn, audio_btn, enhancement_btn]:
            button_layout.addWidget(btn)

        dash_layout.addLayout(button_layout)

        # --- Feature Views ---
        self.metadata_editor = FileBrowser(self.go_back_to_dashboard)
        self.converter_viewer = ConversionViewer(self.go_back_to_dashboard)
        self.noise_browser = NoiseCancellationBrowser(self.go_back_to_dashboard)
        self.enhancement_browser = EnhancementBrowser(self.go_back_to_dashboard)  # ✅ new feature

        # Add views to stacked layout
        self.stacked_layout.addWidget(self.dashboard_widget)     # index 0
        self.stacked_layout.addWidget(self.metadata_editor)      # index 1
        self.stacked_layout.addWidget(self.converter_viewer)     # index 2
        self.stacked_layout.addWidget(self.noise_browser)        # index 3
        self.stacked_layout.addWidget(self.enhancement_browser)
        self.setLayout(self.stacked_layout)

    def create_button(self, label, callback=None):
        btn = QPushButton(f"{label}\nclick")
        btn.setFixedSize(200, 100)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #ccc;
                border: none;
            }
            QPushButton:hover {
                background-color: #bbb;
            }
        """)
        if callback:
            btn.clicked.connect(callback)
        return btn

    def open_metadata_editor(self):
        self.stacked_layout.setCurrentIndex(1)

    def open_converter(self):
        self.stacked_layout.setCurrentIndex(2)

    def open_noise_browser(self):
        self.stacked_layout.setCurrentIndex(3)
    
    def open_enhancement_browser(self):
        self.stacked_layout.setCurrentIndex(4)

    def go_back_to_dashboard(self):
        self.stacked_layout.setCurrentIndex(0)
