from PySide6.QtWidgets import QLineEdit, QHBoxLayout, QWidget
from PySide6.QtCore import Qt
import sys
import os

class CustomLineEdit(QWidget):
    def __init__(self, placeholder_text="", parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText(placeholder_text)
        self.layout.addWidget(self.line_edit)

        self.success_visible = False
        self.update_success_icon()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.normpath(os.path.join(base_path, relative_path))

    def set_success_visible(self, visible):
        self.success_visible = visible
        self.update_success_icon()

    def update_success_icon(self):
        if self.success_visible:
            icon_path = self.resource_path('assets/images/icons8-ok-20.png').replace('\\', '/')
            self.line_edit.setStyleSheet(f"""
                QLineEdit {{
                    background-image: url("{icon_path}");
                    background-repeat: no-repeat;
                    background-position: right;
                    background-origin: content;
                    padding-right: 16px;
                }}
            """)
        else:
            self.line_edit.setStyleSheet("")

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)

    def setReadOnly(self, read_only):
        self.line_edit.setReadOnly(read_only)

    def mousePressEvent(self, event):
        self.line_edit.mousePressEvent(event)

    def setFocus(self):
        self.line_edit.setFocus()