from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit, QHBoxLayout, QFormLayout, QSpacerItem, QSizePolicy, QGroupBox
from PySide6.QtCore import Qt, Signal, QTimer
from custom_line_edit import CustomLineEdit
from functions import get_auth_config, get_user_config, file_name_schema, manage_twitch_oauth_token, get_broadcaster_id, save_config_section
from home_widget import HomeWidget

class ConfigWidget(QWidget):
    status_update = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 10, 20, 10)  # Set margins: left, top, right, bottom

        self.config_label = QLabel("Settings", self)
        self.config_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.config_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.layout.addWidget(self.config_label)

        # Twitch Client-ID & Client-Secret
        self.twitch_auth_group = QGroupBox("Twitch Authentication", self)
        self.auth_form_layout = QFormLayout()
        
        self.client_id_input = QLineEdit(self)
        self.client_id_input.setPlaceholderText("Twitch Client-ID")
        self.client_id_input.setStyleSheet("color: white;")
        self.auth_form_layout.addRow(QLabel("Twitch Client-ID:", self), self.client_id_input)

        self.client_secret_input = QLineEdit(self)
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        self.client_secret_input.setPlaceholderText("Twitch Client-Secret")
        self.client_secret_input.setStyleSheet("color: white;")
        self.auth_form_layout.addRow(QLabel("Twitch Client-Secret:", self), self.client_secret_input)

        self.test_button = QPushButton("Create/Renew Auth-Token", self)
        self.test_button.clicked.connect(self.test_connection)
        self.auth_form_layout.addRow(self.test_button)

        self.client_id_input.textChanged.connect(self.update_test_button_state)
        self.client_secret_input.textChanged.connect(self.update_test_button_state)
        self.update_test_button_state()

        self.twitch_auth_group.setLayout(self.auth_form_layout)
        self.layout.addWidget(self.twitch_auth_group)
     
        # Default Settings
        self.defaults_group = QGroupBox("Default Settings", self)
        self.defaults_form_layout = QFormLayout()

        self.default_broadcaster_input = CustomLineEdit("Default Broadcaster", self)
        self.default_broadcaster_input.setStyleSheet("color: white;")
        self.defaults_form_layout.addRow(QLabel("Default Broadcaster:", self), self.default_broadcaster_input)

        self.download_folder_input = QLineEdit(self)
        self.download_folder_input.setPlaceholderText("Download-Folder")
        self.download_folder_input.setReadOnly(True)
        self.download_folder_input.setStyleSheet("color: white;")
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.setStyleSheet("min-width: 55px;")
        self.browse_button.clicked.connect(self.select_download_folder)
        self.download_folder_layout = QHBoxLayout()
        self.download_folder_layout.addWidget(self.download_folder_input)
        self.download_folder_layout.addWidget(self.browse_button)
        self.defaults_form_layout.addRow(QLabel("Download Folder:", self), self.download_folder_layout)

        self.file_name_schema_input = QLineEdit(self)
        self.file_name_schema_input.setReadOnly(True)  # Setze das Feld auf schreibgeschützt
        self.file_name_schema_input.setStyleSheet("color: white;")
        #self.file_name_schema_input.textChanged.connect(lambda: self.file_name_schema_input.setStyleSheet("color: red;"))
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.setStyleSheet("min-width: 55px;")
        self.clear_button.clicked.connect(lambda: self.file_name_schema_input.clear())
        self.file_name_schema_layout = QHBoxLayout()
        self.file_name_schema_layout.addWidget(self.file_name_schema_input)
        self.file_name_schema_layout.addWidget(self.clear_button)
        self.defaults_form_layout.addRow(QLabel("File Name Schema:", self), self.file_name_schema_layout)
        self.file_name_button_layout = QHBoxLayout()
        for label, value in file_name_schema.items():
            self.schema_button = QPushButton(label, self)
            self.schema_button.setFlat(True)
            self.schema_button.setStyleSheet("font-size: 10px;")
            self.schema_button.clicked.connect(lambda checked, v=value: self.on_schema_button_click(v))
            self.file_name_button_layout.addWidget(self.schema_button)
        self.file_name_button_layout.addStretch()  # Fügt einen Spacer rechts von den Buttons hinzu
        self.defaults_form_layout.addRow(QLabel("Available values:", self), self.file_name_button_layout)

        self.save_config_button = QPushButton("Save Configuration", self)
        self.save_config_button.clicked.connect(self.save_configuration)
        self.defaults_form_layout.addRow(self.save_config_button)

        self.defaults_group.setLayout(self.defaults_form_layout)
        self.layout.addWidget(self.defaults_group)

        self.bottomspacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.bottomspacer)

        # Load existing configuration
        self.load_existing_config()

        self.broadcaster_check_timer = QTimer(self)
        self.broadcaster_check_timer.setSingleShot(True)
        self.broadcaster_check_timer.timeout.connect(self.check_broadcaster)

        self.default_broadcaster_input.line_edit.textChanged.connect(self.on_broadcaster_input_changed)

    def load_existing_config(self):
        auth_config = get_auth_config()
        # print(auth_config)  # Debugging line to check the loaded auth config
        self.client_id_input.setText(auth_config.get("client_id", ""))
        self.client_secret_input.setText(auth_config.get("client_secret", ""))
        user_config = get_user_config()
        self.default_broadcaster_input.setText(user_config.get("default_user_name", ""))
        self.download_folder_input.setText(user_config.get("dl_folder", ""))
        self.file_name_schema_input.setText(user_config.get("spacer"))

    def test_connection(self):
        client_id = self.client_id_input.text()
        client_secret = self.client_secret_input.text()

        result = manage_twitch_oauth_token(client_id, client_secret)
        if "error" in result:
            self.status_update.emit(result["message"])
        else:
            self.status_update.emit("Connection successful")
    
    def select_download_folder(self):
        current_folder = self.download_folder_input.text()
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", current_folder)
        if folder:
            self.download_folder_input.setText(folder)

    def save_configuration(self):
        default_broadcaster = self.default_broadcaster_input.text().strip()
        download_folder = self.download_folder_input.text().strip()
        file_name_schema = self.file_name_schema_input.text().strip()

        if not default_broadcaster:
            self.status_update.emit("Error: Default Broadcaster cannot be empty.")
            self.default_broadcaster_input.setFocus()
            return
        if not download_folder:
            self.status_update.emit("Error: Download Folder cannot be empty.")
            self.download_folder_input.setFocus()
            return
        if not file_name_schema:
            self.status_update.emit("Error: File Name Schema cannot be empty.")
            self.file_name_schema_input.setFocus()
            return

        result = save_config_section("user", {
            "default_user_name": default_broadcaster,
            "dl_folder": download_folder,
            "spacer": file_name_schema
        })
        if result["success"]:
            self.status_update.emit(result["message"])

            # Update fields in HomeWidget if they are empty
            main_window = self.window()
            if hasattr(main_window, 'home_widget') and isinstance(main_window.home_widget, HomeWidget):
                home_widget = main_window.home_widget
                if not home_widget.broadcaster_input.text().strip():
                    home_widget.broadcaster_input.setText(default_broadcaster)
                if not home_widget.download_folder_input.text().strip():
                    home_widget.download_folder_input.setText(download_folder)
        else:
            self.status_update.emit(f"Error: {result['message']}")

    def on_schema_button_click(self, value):
        current_text = self.file_name_schema_input.text()

        if ".mp4" in current_text:
            current_text = current_text.replace(".mp4", "")  # Entferne ".mp4"

        self.file_name_schema_input.setText(current_text + value)

        self.file_name_schema_input.setFocus()

    def update_test_button_state(self):
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        self.test_button.setEnabled(bool(client_id and client_secret))

    def on_broadcaster_input_changed(self):
        self.broadcaster_check_timer.start(1000)  # 1 Sekunde Verzögerung

    def check_broadcaster(self):
        broadcaster_name = self.default_broadcaster_input.text().strip()
        if broadcaster_name:
            result = get_broadcaster_id(broadcaster_name)
            if "error" in result:
                self.default_broadcaster_input.set_success_visible(False)
                self.status_update.emit(result["message"])
            else:
                self.default_broadcaster_input.set_success_visible(True)
