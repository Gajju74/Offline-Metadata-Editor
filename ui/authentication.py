from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt

class AuthenticationDialog(QDialog):
    def __init__(self, valid_credentials, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Authentication")
        self.setFixedSize(300, 150)
        
        self.valid_credentials = valid_credentials  # A dictionary with username: key pairs
        
        # Layouts
        layout = QVBoxLayout(self)
        
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit(self)
        self.key_label = QLabel("Key:")
        self.key_input = QLineEdit(self)
        self.key_input.setEchoMode(QLineEdit.Password)
        
        # Buttons
        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.authenticate)

        # Adding widgets
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.key_label)
        layout.addWidget(self.key_input)
        layout.addWidget(self.login_button)
        
    def authenticate(self):
        username = self.username_input.text()
        key = self.key_input.text()
        
        # Check if the credentials are valid
        if self.valid_credentials.get(username) == key:
            self.accept()  # Close dialog and allow access
        else:
            QMessageBox.warning(self, "Authentication Failed", "Invalid username or key. Please try again.")

