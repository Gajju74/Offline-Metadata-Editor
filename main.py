# main.py
import sys
from PySide6.QtWidgets import QApplication
from ui.file_browser import FileBrowser

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileBrowser()
    window.show()
    sys.exit(app.exec())
