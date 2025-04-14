import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit, QHBoxLayout, QFormLayout, QSpacerItem, QSizePolicy, QGroupBox, QDateEdit, QListWidget, QListWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from custom_line_edit import CustomLineEdit
from datetime import datetime, timedelta
from functions import get_clips, download_clips, get_auth_config, get_user_config, get_broadcaster_id, get_game_name, is_vlc_available, open_clips_in_vlc


class SearchClipsThread(QThread):
    search_completed = Signal(list)
    search_failed = Signal(str)

    def __init__(self, broadcaster_id, date_from, date_to, parent=None):
        super().__init__(parent)
        self.broadcaster_id = broadcaster_id
        self.date_from = date_from
        self.date_to = date_to

    def run(self):
        try:
            clips = get_clips(self.broadcaster_id, self.date_from, self.date_to)
            self.search_completed.emit(clips)
        except Exception as e:
            self.search_failed.emit(str(e))


class DownloadClipsThread(QThread):
    download_completed = Signal(list)
    download_failed = Signal(str)

    def __init__(self, clips, download_folder, parent=None):
        super().__init__(parent)
        self.clips = clips
        self.download_folder = download_folder

    def run(self):
        try:
            downloaded_files = download_clips(self.clips, self.download_folder, self.parent().status_update.emit)
            self.download_completed.emit(downloaded_files)
        except Exception as e:
            self.download_failed.emit(str(e))


class HomeWidget(QWidget):
    status_update = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 10, 20, 10)  # Set margins: left, top, right, bottom

        self.label = QLabel("Download Clips", self)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        #self.label.mousePressEvent = self.label_clicked
        self.layout.addWidget(self.label)

        #self.topspacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        #self.layout.addItem(self.topspacer)

        # Settings
        self.settings_group = QGroupBox("Settings", self)
        self.settings_form_layout = QFormLayout()

        self.broadcaster_input = CustomLineEdit("Broadcaster", self)
        self.broadcaster_input.setStyleSheet("color: white;")
        self.settings_form_layout.addRow(QLabel("Broadcaster:", self), self.broadcaster_input)

        # Date Range Selection with Calendar
        self.date_from_input = QDateEdit(self)
        self.date_from_input.setCalendarPopup(True)
        self.date_from_input.setDisplayFormat("yyyy-MM-dd")
        self.date_from_input.setStyleSheet("color: white;")
        self.date_from_input.setFocusPolicy(Qt.StrongFocus)

        self.date_to_input = QDateEdit(self)
        self.date_to_input.setCalendarPopup(True)
        self.date_to_input.setDisplayFormat("yyyy-MM-dd")
        self.date_to_input.setStyleSheet("color: white;")
        self.date_to_input.setFocusPolicy(Qt.StrongFocus)

        # Disable manual input for date fields without affecting calendar interaction
        self.date_from_input.lineEdit().setEnabled(False)
        self.date_to_input.lineEdit().setEnabled(False)

        # Prevent year change by clicking into the field
        self.date_from_input.setButtonSymbols(QDateEdit.NoButtons)
        self.date_to_input.setButtonSymbols(QDateEdit.NoButtons)

        # Set default dates: yesterday and today
        today = datetime.now().date()
        yesterday = today - timedelta(days=2)

        self.date_from_input.setDate(yesterday)
        self.date_to_input.setDate(today)

        self.date_range_layout = QHBoxLayout()
        self.date_range_layout.addWidget(self.date_from_input)
        self.date_range_layout.addWidget(self.date_to_input)

        self.settings_form_layout.addRow(QLabel("Date Range:", self), self.date_range_layout)

        self.search_button = QPushButton("Search Clips", self)
        self.search_button.clicked.connect(self.search_clips)
        self.settings_form_layout.addRow(self.search_button)

        self.settings_group.setLayout(self.settings_form_layout)
        self.layout.addWidget(self.settings_group)

        # Clips
        self.clips_group = QGroupBox("Clips", self)
        self.clips_form_layout = QFormLayout()

        self.clips_list = QListWidget(self)
        self.clips_list.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Ermöglicht das Markieren mehrerer Clips
        self.clips_list.setMinimumHeight(200)  # Setzt eine Mindesthöhe für die Liste
        self.clips_form_layout.addRow(self.clips_list)

        self.download_folder_input = QLineEdit(self)
        self.download_folder_input.setPlaceholderText("Download-Folder")
        self.download_folder_input.setReadOnly(True)
        self.download_folder_input.setStyleSheet("color: white;")
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.select_download_folder)
        self.download_folder_layout = QHBoxLayout()
        self.download_folder_layout.addWidget(self.download_folder_input)
        self.download_folder_layout.addWidget(self.browse_button)
        self.clips_form_layout.addRow(QLabel("Download Folder:", self), self.download_folder_layout)

        self.download_button = QPushButton("Download", self)
        self.download_button.clicked.connect(self.download_selected_clips)
        self.download_vlc_button = QPushButton("Download && open in VLC", self)
        self.download_vlc_button.clicked.connect(self.download_selected_clips)

        if is_vlc_available():
            self.download_vlc_button.show()
        else:
            self.download_vlc_button.hide()

        download_buttons_layout = QHBoxLayout()
        download_buttons_layout.addWidget(self.download_button)
        download_buttons_layout.addWidget(self.download_vlc_button)
        self.clips_form_layout.addRow(download_buttons_layout)

        self.clips_group.setLayout(self.clips_form_layout)
        self.layout.addWidget(self.clips_group)  # Sicherstellen, dass die QGroupBox korrekt im Hauptlayout eingebettet ist

        self.clips = []  # Liste für alle Clips

        # Load existing configuration
        self.load_existing_config()

        self.broadcaster_check_timer = QTimer(self)
        self.broadcaster_check_timer.setSingleShot(True)
        self.broadcaster_check_timer.timeout.connect(self.check_broadcaster)

        self.broadcaster_input.line_edit.textChanged.connect(self.on_broadcaster_input_changed)

        # Validate date range
        def validate_date_range():
            if self.date_to_input.date() < self.date_from_input.date():
                self.status_update.emit("Error: End date cannot be earlier than start date.")

        self.date_from_input.dateChanged.connect(validate_date_range)
        self.date_to_input.dateChanged.connect(validate_date_range)

        self.clips_list.itemSelectionChanged.connect(self.update_download_button_state)
        self.update_download_button_state()

    def load_existing_config(self):
        auth_config = get_auth_config()
        user_config = get_user_config()
        self.broadcaster_input.setText(user_config.get("default_user_name", ""))
        self.download_folder_input.setText(user_config.get("dl_folder", ""))

    def on_broadcaster_input_changed(self):
        self.broadcaster_check_timer.start(1000)  # 1 Sekunde Verzögerung

    def check_broadcaster(self):
        broadcaster_name = self.broadcaster_input.text().strip()
        if broadcaster_name:
            result = get_broadcaster_id(broadcaster_name)
            if "error" in result:
                self.broadcaster_input.set_success_visible(False)
                self.status_update.emit(result["message"])
            else:
                self.broadcaster_input.set_success_visible(True)
                self.status_update.emit("Broadcaster ID found")

    def toggle_spinner(self, visible):
        main_window = self.window()
        if hasattr(main_window, 'spinner_label') and hasattr(main_window, 'spinner_movie'):
            main_window.spinner_label.setVisible(visible)
            if visible:
                main_window.spinner_movie.start()
            else:
                main_window.spinner_movie.stop()

    def search_clips(self):
        broadcaster_name = self.broadcaster_input.text().strip()
        if not broadcaster_name:
            self.status_update.emit("Error: Broadcaster cannot be empty.")
            self.broadcaster_input.setFocus()
            self.toggle_spinner(False)
            return

        result = get_broadcaster_id(broadcaster_name)
        if "error" in result:
            self.status_update.emit(result["message"])
            self.toggle_spinner(False)
            return

        broadcaster_id = result["id"]
        if not broadcaster_id:
            self.status_update.emit("Error: Broadcaster ID not found.")
            self.toggle_spinner(False)
            return

        date_from = self.date_from_input.date().toString("yyyy-MM-dd")
        date_to = self.date_to_input.date().toString("yyyy-MM-dd")

        self.toggle_spinner(True)
        self.clips_list.clear()

        self.search_thread = SearchClipsThread(broadcaster_id, date_from, date_to, self)
        self.search_thread.search_completed.connect(self.on_search_completed)
        self.search_thread.search_failed.connect(self.on_search_failed)
        self.search_thread.start()

    def on_search_completed(self, clips):
        self.clips = clips
        self.status_update.emit(f"{len(clips)} clips found.")
        self.clips_group.setTitle(f"Clips ({len(clips)} found)")
        self.toggle_spinner(False)

        user_config = get_user_config()
        spacer_template = user_config.get("spacer", "{clip_date} - {game_name} - {clip_title}")

        for clip in self.clips:
            try:
                broadcaster_name = re.sub(r"[<>:\"/\\|?*.'’‘]", "", clip.get("broadcaster_name", "unknown")).strip()
                clip_url = clip.get("url")
                clip_title = re.sub(r"[<>:\"/\\|?*.'’‘]", "", clip.get("title", "untitled")).strip()
                clip_creator = re.sub(r"[<>:\"/\\|?*.'’‘]", "", clip.get("creator_name", "unknown")).strip()
                clip_date = clip.get("created_at", "").split("T")[0]
                game_id = clip.get("game_id", "0")
                game_name = re.sub(r"[<>:\"/\\|?*.'’‘]", "", get_game_name(game_id)).strip()

                display_text = spacer_template.format(
                    clip_date=clip_date,
                    game_name=game_name,
                    clip_title=clip_title,
                    clip_creator=clip_creator,
                    broadcaster_name=broadcaster_name
                )
                display_text = display_text + ".mp4"

                clip["filename"] = display_text

                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, clip_url)
                self.clips_list.addItem(item)
            except Exception as e:
                self.status_update.emit(f"Error processing clip: {e}")
                continue

        for i in range(self.clips_list.count()):
            self.clips_list.item(i).setSelected(True)

    def on_search_failed(self, error_message):
        self.status_update.emit(f"Error: {error_message}")
        self.toggle_spinner(False)

    def select_download_folder(self):
        current_folder = self.download_folder_input.text()
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", current_folder)
        if folder:
            self.download_folder_input.setText(folder)

    def update_download_button_state(self):
        self.download_button.setEnabled(len(self.clips_list.selectedItems()) > 0)
        self.download_vlc_button.setEnabled(len(self.clips_list.selectedItems()) > 0)

    def download_selected_clips(self):
        self.toggle_spinner(True)  # Spinner aktivieren

        selected_clips = [item.data(Qt.UserRole) for item in self.clips_list.selectedItems()]
        download_folder = self.download_folder_input.text().strip()
        if not download_folder:
            self.status_update.emit("Error: Download folder is not set.")
            self.toggle_spinner(False)  # Spinner deaktivieren
            return
        if not selected_clips:
            self.status_update.emit("Error: No clips selected for download.")
            self.toggle_spinner(False)  # Spinner deaktivieren
            return

        filtered_clips = [clip for clip in self.clips if clip.get("url") in selected_clips]

        self.download_thread = DownloadClipsThread(filtered_clips, download_folder, self)
        self.download_thread.download_completed.connect(self.on_download_completed)
        self.download_thread.download_failed.connect(self.on_download_failed)

        # Speichern, ob der VLC-Button verwendet wurde
        self.download_thread.is_vlc_download = self.sender() == self.download_vlc_button

        self.download_thread.start()

    def on_download_completed(self, downloaded_files):
        self.status_update.emit("Download completed.")
        self.toggle_spinner(False)  # Spinner deaktivieren

        # Überprüfen, ob der VLC-Button verwendet wurde
        if getattr(self.download_thread, 'is_vlc_download', False):
            if is_vlc_available():
                open_clips_in_vlc(downloaded_files, self.status_update.emit)

    def on_download_failed(self, error_message):
        self.status_update.emit(f"Error: {error_message}")
        self.toggle_spinner(False)  # Spinner deaktivieren

