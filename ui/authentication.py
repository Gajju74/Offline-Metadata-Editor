from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QLabel,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt

class AuthenticationDialog(QDialog):
    def __init__(self, valid_credentials, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Secure Login")
        self.setFixedSize(340, 250)
        self.setStyleSheet(self.get_styles())

        self.valid_credentials = valid_credentials

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        # Title
        title = QLabel("Welcome Back")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title)

        subtitle = QLabel("Enter your credentials to continue.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #aaa; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Access Key")
        self.key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.key_input)

        layout.addItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.authenticate)
        layout.addWidget(self.login_button)

    def authenticate(self):
        username = self.username_input.text().strip()
        key = self.key_input.text().strip()

        if self.valid_credentials.get(username) == key:
            self.accept()
        else:
            QMessageBox.warning(self, "Authentication Failed", "Invalid username or key.")

    def get_styles(self):
        return """
        QDialog {
            background-color: #232323;
            color: #f0f0f0;
            font-family: 'Segoe UI', sans-serif;
        }
        QLabel {
            color: #f0f0f0;
        }
        QLineEdit {
            padding: 9px 12px;
            border-radius: 6px;
            background-color: #333;
            border: 1px solid #555;
            color: #eee;
            font-size: 14px;
        }
        QLineEdit:focus {
            border: 1px solid #66afe9;
            background-color: #3b3b3b;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        """
