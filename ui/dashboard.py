from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QStackedLayout, QSpacerItem, QSizePolicy, QGridLayout,
    QDialog
)
from PySide6.QtCore import Qt
from ui.metadata_browser import MetadataBrowser
from ui.conversion_browser import ConversionBrowser
from ui.noise_browser import NoiseCancellationBrowser
from ui.enhancement_browser import EnhancementBrowser
from ui.video_editor_browser import VideoEditorBrowser
from ui.image_editor_browser import ImageEditorBrowser
from ui.authentication import AuthenticationDialog
from ui.batch_renamer_browser import BatchRenamerBrowser

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metadata and Video Editor")
        self.setMinimumSize(1300, 900)

        self.valid_credentials = {
            "admin": "12345",
            "user": "password"
        }

        # Authentication dialog
        self.auth_dialog = AuthenticationDialog(self.valid_credentials)
        if self.auth_dialog.exec() == QDialog.Accepted:
            self.setup_ui()  # Proceed if authenticated
        else:
            self.close()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #eeeeee;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #f0f0f0;
            }
        """)

        self.stacked_layout = QStackedLayout(self)

        # Dashboard View
        self.dashboard_widget = QWidget()
        dash_layout = QVBoxLayout()
        dash_layout.setAlignment(Qt.AlignCenter)
        self.dashboard_widget.setLayout(dash_layout)

        heading = QLabel("Metadata and Video Editor")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 12px;
        """)
        dash_layout.addWidget(heading)

        subtitle = QLabel("Select a feature to begin")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 18px; color: #aaa; margin-bottom: 30px;")
        dash_layout.addWidget(subtitle)

        # Grid layout for buttons
        grid_layout = QGridLayout()
        grid_layout.setSpacing(25)
        grid_layout.setAlignment(Qt.AlignCenter)

        buttons = [
            ("Meta Data Editor", self.open_metadata_editor),
            ("Video Converter", self.open_converter),
            ("Noise Reduction", self.open_noise_browser),
            ("AI Enhancement", self.open_enhancement_browser),
            ("Video Editor", self.open_video_editor_browser),
            ("Image Editor", self.open_image_editor_browser),
            ("Batch Renamer", self.open_batch_renamer_browser),
        ]

        for i, (label, func) in enumerate(buttons):
            row = i // 5
            col = i % 5
            grid_layout.addWidget(self.create_button(label, func), row, col)

        dash_layout.addLayout(grid_layout)
        dash_layout.addItem(QSpacerItem(0, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Feature Views
        self.metadata_editor = MetadataBrowser(self.go_back_to_dashboard)
        self.converter_viewer = ConversionBrowser(self.go_back_to_dashboard)
        self.noise_browser = NoiseCancellationBrowser(self.go_back_to_dashboard)
        self.enhancement_browser = EnhancementBrowser(self.go_back_to_dashboard)
        self.video_editor_browser = VideoEditorBrowser(self.go_back_to_dashboard)
        self.image_editor_browser = ImageEditorBrowser(self.go_back_to_dashboard)
        self.batch_renamer_browser = BatchRenamerBrowser(self.go_back_to_dashboard)

        # Add to stacked layout
        self.stacked_layout.addWidget(self.dashboard_widget)
        self.stacked_layout.addWidget(self.metadata_editor)
        self.stacked_layout.addWidget(self.converter_viewer)
        self.stacked_layout.addWidget(self.noise_browser)
        self.stacked_layout.addWidget(self.enhancement_browser)
        self.stacked_layout.addWidget(self.video_editor_browser)
        self.stacked_layout.addWidget(self.image_editor_browser)
        self.stacked_layout.addWidget(self.batch_renamer_browser)

        self.setLayout(self.stacked_layout)

    def create_button(self, label, callback=None):
        btn = QPushButton(label)
        btn.setFixedSize(220, 110)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background-color: #333;
                border-radius: 10px;
                padding: 10px;
                border: 1px solid #555;
            }
            QPushButton:hover {
                background-color: #444;
                border: 1px solid #66afe9;
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

    def open_video_editor_browser(self):
        self.stacked_layout.setCurrentIndex(5)

    def open_image_editor_browser(self):
        self.stacked_layout.setCurrentIndex(6)

    def open_batch_renamer_browser(self):
        self.stacked_layout.setCurrentIndex(7)

    def go_back_to_dashboard(self):
        self.stacked_layout.setCurrentIndex(0)

