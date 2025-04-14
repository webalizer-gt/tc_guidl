import sys
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QStatusBar, QStackedWidget, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QMovie
from home_widget import HomeWidget
from config_widget import ConfigWidget
from help_widget import HelpWidget
from functions import *

class MainWindow(QMainWindow):
    VERSION = {"major": 1, "minor": 0}  # Define the application version here

    status_signal = Signal(str)

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def check_version(self):
        """Check the version information and log warnings if necessary."""
        conf_version = get_version()
        conf_major = conf_version.get("major", 0)
        conf_minor = conf_version.get("minor", 0)

        major = self.VERSION["major"]
        minor = self.VERSION["minor"]
        if major == 0:
            self.update_status_bar("Warning: Old config file. Please update your File Name Schema!")
        else:
            self.update_status_bar(f"Running Version {major}.{minor}")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Twitch-Clip Downloader")
        self.setGeometry(100, 100, 800, 600)
        self.setFixedWidth(800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout(self.central_widget)

        # Left side layout for buttons
        self.left_layout = QVBoxLayout()
        self.left_widget = QWidget()
        self.left_widget.setLayout(self.left_layout)
        self.left_widget.setStyleSheet("background-color: #2c2c2c;")
        self.main_layout.addWidget(self.left_widget)

        self.home_button = QPushButton(self)
        self.home_button.setFixedSize(50, 50)
        self.home_button.setStyleSheet("border: none;background-color: none;")
        home_icon = QIcon(QPixmap(self.resource_path("assets/images/icons8-twitch.svg")).scaled(40, 40, Qt.KeepAspectRatio))
        self.home_button.setIcon(home_icon)
        self.home_button.setIconSize(home_icon.actualSize(self.home_button.size()))
        self.home_button.clicked.connect(self.show_home_widget)
        self.left_layout.addWidget(self.home_button, alignment=Qt.AlignTop)

        self.left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.config_button = QPushButton(self)
        self.config_button.setFixedSize(50, 50)
        self.config_button.setStyleSheet("border: none;background-color: none;")
        config_icon = QIcon(QPixmap(self.resource_path("assets/images/icons8-settings.svg")).scaled(40, 40, Qt.KeepAspectRatio))
        self.config_button.setIcon(config_icon)
        self.config_button.setIconSize(config_icon.actualSize(self.config_button.size()))
        self.config_button.clicked.connect(self.show_config_widget)
        self.left_layout.addWidget(self.config_button, alignment=Qt.AlignBottom)

        self.help_button = QPushButton(self)
        self.help_button.setFixedSize(50, 50)
        self.help_button.setStyleSheet("border: none;background-color: none;")
        help_icon = QIcon(QPixmap(self.resource_path("assets/images/icons8-help-40.png")).scaled(40, 40, Qt.KeepAspectRatio))
        self.help_button.setIcon(help_icon)
        self.help_button.setIconSize(help_icon.actualSize(self.help_button.size()))
        self.help_button.clicked.connect(self.show_help_widget)
        self.left_layout.addWidget(self.help_button, alignment=Qt.AlignBottom)

        # Right side layout for main content
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # Add status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.spinner_label = QLabel()
        self.spinner_movie = QMovie(self.resource_path("assets/images/30.gif"))
        self.spinner_label.setMovie(self.spinner_movie)
        #self.spinner_label.setFixedSize(128, 23)  # Set fixed size to avoid clipping
        self.spinner_label.setVisible(True)
        self.status_bar.addPermanentWidget(self.spinner_label)

         # Connect the status signal to the update_status_bar method
        self.status_signal.connect(self.update_status_bar)

        # Load configuration
        self.config_status = load_config()
        
        # Check version information
        self.check_version()
                
        # Home widget
        self.home_widget = HomeWidget(self)
        self.home_widget.status_update.connect(self.update_status_bar)
        self.stacked_widget.addWidget(self.home_widget)

        # Config widget
        self.config_widget = ConfigWidget(self)
        self.config_widget.status_update.connect(self.update_status_bar)
        self.stacked_widget.addWidget(self.config_widget)

        # Help widget
        self.help_widget = HelpWidget(self)
        self.help_widget.status_update.connect(self.update_status_bar)
        self.stacked_widget.addWidget(self.help_widget)

                
        if not self.config_status.get("success"):
            self.show_config_widget()
        #self.update_status_bar(f"{self.config_status.get('message')}")

    def show_home_widget(self):
        self.stacked_widget.setCurrentWidget(self.home_widget)

    def show_config_widget(self):
        self.stacked_widget.setCurrentWidget(self.config_widget)

    def show_help_widget(self):
        self.stacked_widget.setCurrentWidget(self.help_widget)

    def update_status_bar(self, message):
        self.status_bar.showMessage(message, 5000)
