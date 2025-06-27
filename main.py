# main.py
# import sys
# from PySide6.QtWidgets import QApplication
# from ui.file_browser import FileBrowser

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = FileBrowser()
#     window.show()
#     sys.exit(app.exec())

import sys
from PySide6.QtWidgets import QApplication
from ui.dashboard import MainWindow  # new dashboard file

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 

