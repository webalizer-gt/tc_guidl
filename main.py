from PySide6.QtWidgets import QApplication
import sys
from qt_material import apply_stylesheet
from window import MainWindow
from functions import load_config

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')

    window = MainWindow()
        
    window.show()
    sys.exit(app.exec())
