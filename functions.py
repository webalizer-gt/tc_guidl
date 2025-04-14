# Ensure dependencies are checked before importing anything else
def check_dependencies():
    """Check if yt-dlp and requests libraries are available."""
    missing_dependencies = []

    # Check for yt-dlp
    try:
        import yt_dlp  # noqa
    except ImportError:
        missing_dependencies.append("yt-dlp")

    # Check for requests
    try:
        import requests  # noqa
    except ImportError:
        missing_dependencies.append("requests")

    # If any dependencies are missing, notify the user and exit
    if missing_dependencies:
        print(f"Error: The following dependencies are missing: {', '.join(missing_dependencies)}")
        print("Please install them using:")
        print("    pip install " + " ".join(missing_dependencies))
        exit(1)

# Call the dependency check first
check_dependencies()

# Now import the required modules, since we've confirmed they're installed
import requests
from yt_dlp import YoutubeDL
import os
import platform
import re
import json
import argparse
from datetime import datetime, timedelta
import subprocess
import shutil
from PySide6.QtCore import QObject

# Default values
CONFIG_FILE = "config.json"
# Global configuration variable
config = {} 
# In-memory cache for game names
game_cache = {}
# File name schema for downloaded clips
file_name_schema = {
    "Date": "{clip_date}",
    "Game": "{game_name}",
    "Title": "{clip_title}",
    "Creator": "{clip_creator}",
    "Broadcaster": "{broadcaster_name}",
    " \u00a6 ": " \u00a6 "
}

# Twitch API URLs
USER_API_URL = "https://api.twitch.tv/helix/users"
CLIPS_API_URL = "https://api.twitch.tv/helix/clips"
GAME_API_URL = "https://api.twitch.tv/helix/games"
VALIDATE_TOKEN_URL = "https://id.twitch.tv/oauth2/validate"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

def load_config():
    """Load configuration from config.json if it exists."""
    global config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as file:
                config = json.load(file)
                return {"success": True, "message": f"Configuration loaded from {CONFIG_FILE}"}
        except json.JSONDecodeError:
            return {"success": False, "error": "JSONDecodeError", "message": f"Unable to read {CONFIG_FILE}."}
    else:
        config = {}
        return {"success": False, "error": "FileNotFound", "message": "No configuration file found."}

def save_config_section(section, data):
    """
    Save updates to a specific section of the configuration dictionary.
    
    Args:
        section (str): The section of the config to update (e.g., "user" or "auth").
        data (dict): The new data to save in the specified section.

    Returns:
        dict: A dictionary indicating success or error details.
    """
    try:
        if section not in config:
            config[section] = {}

        # Update the section with new data
        config[section].update(data)

        # Also update the "version" section with the current VERSION from window.py
        from window import MainWindow  # Import MainWindow to access VERSION
        config["version"] = MainWindow.VERSION

        # Save to the config file
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4)

        return {"success": True, "message": f"{section.capitalize()} configuration saved to {CONFIG_FILE}."}
    except (IOError, json.JSONDecodeError) as e:
        return {"success": False, "error": "SaveError", "message": f"Failed to save configuration: {e}"}

def manage_twitch_oauth_token(client_id=None, client_secret=None):
    """
    Generates or renews a Twitch OAuth token using the client_credentials grant type.

    Args:
        client_id (str, optional): The Client ID of the Twitch application. Defaults to None.
        client_secret (str, optional): The Client Secret of the Twitch application. Defaults to None.

    Returns:
        dict: A dictionary with the access token and other information, or an error message if an error occurred.
    """
    auth = get_auth_config()
    client_id = client_id or auth.get("client_id")
    client_secret = client_secret or auth.get("client_secret")

    if not client_id or not client_secret:
        return {"error": "MISSING_CREDENTIALS", "message": "Client ID or Client Secret not provided."}

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    try:
        response = requests.post(TOKEN_URL, data=data)
        response.raise_for_status()
        token_data = response.json()

        if token_data:
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in")
            expiration_date = datetime.now() + timedelta(seconds=expires_in)
            formatted_date = expiration_date.strftime("%Y-%m-%d %H:%M:%S")

            save_return = save_config_section("auth", {
                "client_id": client_id,
                "client_secret": client_secret,
                "access_token": access_token,
                "expires_at": formatted_date
            })
            return save_return
        else:
            return {"error": "INVALID_RESPONSE", "message": "Received invalid response from Twitch API."}

    except requests.exceptions.RequestException as e:
        return {"error": "REQUEST_FAILED", "message": f"Failed to generate token. {e}"}

    return {"error": "UNKNOWN_ERROR", "message": "An unknown error occurred while generating the token."}

def get_user_config():
    """Extract user configuration from the loaded config."""
    user_config = config.get("user", {})
    return {
        "default_user_name": user_config.get("default_user_name"),
        "spacer": user_config.get("spacer", "{clip_date} \u00a6 {game_name} \u00a6 {clip_title} \u00a6 {clip_creator}"),
        "dl_folder": user_config.get("dl_folder")
    }

def get_auth_config():
    """Extract authentication configuration from the loaded config."""
    auth_config = config.get("auth", {})
    return {
        "client_id": auth_config.get("client_id", ""),
        "client_secret": auth_config.get("client_secret", ""),
        "access_token": auth_config.get("access_token", ""),
        "expires_at": auth_config.get("expires_at", "")
    }

def get_version():
    """Load the version information from config.json."""
    version = config.get("version", {})
    return {
        "major": version.get("major", 0),
        "minor": version.get("minor", 0)
    }

def get_broadcaster_id(user_name):
    """Get the broadcaster ID based on the channel name."""
    auth_config = get_auth_config()
    headers = {"Client-ID": auth_config["client_id"], "Authorization": f"Bearer {auth_config['access_token']}"}
    params = {"login": user_name}
    
    try:
        response = requests.get(USER_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("data"):
            return {"error": "USER_NOT_FOUND", "message": f"User '{user_name}' not found."}
        
        return {"id": data["data"][0]["id"]}
    except requests.exceptions.RequestException as e:
        return {"error": "REQUEST_FAILED", "message": f"Failed to fetch broadcaster ID for user '{user_name}'. {e}"}

def get_clips(broadcaster_id, start_timestamp, end_timestamp):
    """Fetch clips from the Twitch API."""
    auth_config = get_auth_config()
    headers = {"Client-ID": auth_config["client_id"], "Authorization": f"Bearer {auth_config['access_token']}"}
    clips = []
    seen_clip_ids = set()

    # Convert timestamps to ISO 8601 format
    start_timestamp = datetime.fromisoformat(start_timestamp).isoformat() + 'Z'
    end_timestamp = datetime.fromisoformat(end_timestamp).isoformat() + 'Z'

    def fetch_clips(limit):
        params = {
            "broadcaster_id": broadcaster_id,
            "first": limit,
            "started_at": start_timestamp,
            "ended_at": end_timestamp,
        }
        cursor = None
        while True:
            try:
                if cursor:
                    params["after"] = cursor
                response = requests.get(CLIPS_API_URL, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                for clip in data.get("data", []):
                    if clip["id"] not in seen_clip_ids:
                        clips.append(clip)
                        seen_clip_ids.add(clip["id"])
                cursor = data.get("pagination", {}).get("cursor")
                
                if not cursor:
                    break
            except requests.exceptions.RequestException as e:
                return {"error": "REQUEST_FAILED", "message": f"Error: Failed to fetch clips. {e}"}
                break

    # Fetch clips with different limits
    fetch_clips(2)
    fetch_clips(99)
    fetch_clips(50)

    clips.sort(key=lambda x: x["created_at"])
    #print(f"Info: {clips}")
    return clips

def get_game_name(game_id):
    """
    Fetch the name of a game based on its game_id, with in-memory caching.
    
    Args:
        game_id (str): The ID of the game.

    Returns:
        str: The name of the game or "Unknown" if an error occurs.
    """
    # Check the cache first
    if game_id in game_cache:
        return game_cache[game_id]

    # If not in cache, fetch from API
    auth_config = get_auth_config()
    headers = {"Client-ID": auth_config["client_id"], "Authorization": f"Bearer {auth_config['access_token']}"}
    params = {"id": game_id}

    try:
        response = requests.get(GAME_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            game_name = data["data"][0]["name"]
            game_cache[game_id] = game_name  # Save to in-memory cache
            return game_name
    except requests.exceptions.RequestException as e:
        return {"error": "REQUEST_FAILED", "message": f"Error: Failed to fetch game name for game_id {game_id}. {e}"}
    
    return "Unknown"

def download_clips(clips, dl_folder, status_callback):
    """Download clips using yt-dlp and format file names as specified."""
    downloaded_clips = []  # List to store paths of downloaded clips

    for clip in clips:
        try:
            filename = clip.get("filename", "unknown").strip()
            clip_url = clip.get("url")

            if not clip_url:
                if status_callback:
                    status_callback(f"Warning: Skipping clip with missing URL: {clip}")
                print(f"Warning: Skipping clip with missing data: {clip}")
                continue

            # Define the download-path + file name
            file_path = os.path.join(dl_folder, filename)
            print(f"File path: {file_path}")

            # Skip download if file already exists
            if os.path.exists(file_path):
                if status_callback:
                    status_callback(f"Info: Skipping download, file already exists: {filename}")
                print(f"Info: Skipping download, file already exists: {filename}")
                downloaded_clips.append(file_path)
                continue

            print(f"Downloading clip: {filename}")
            if status_callback:
                status_callback(f"Downloading clip: {filename}")

            # Options for yt-dlp
            ydl_opts = {
                "outtmpl": file_path,  # File name template
                "quiet": True,         # Minimal output
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([clip_url])

            downloaded_clips.append(file_path)  # Add the file path to the list

        except Exception as e:
            print(f"Error: Failed to download {clip_url}. {e}")
            if status_callback:
                status_callback(f"Error: Failed to download {clip_url}. {e}")

    return downloaded_clips

def is_vlc_available():
    """
    Check if VLC media player is installed and accessible.

    Returns:
        bool: True if VLC is available, False otherwise.
    """
    # Determine the platform
    current_platform = platform.system()

    try:
        if current_platform == "Windows":
            # Windows-specific VLC path
            vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
        elif current_platform in ("Linux", "Darwin"):  # Darwin is macOS
            # Linux/macOS-specific VLC command
            vlc_path = "vlc"
        else:
            print(f"Error: Unsupported platform: {current_platform}")
            return False

        # Check if VLC is installed and accessible
        if shutil.which(vlc_path):
            return True
        else:
            #print(f"Error: {vlc_path} is not installed or not in the PATH.")
            return False

    except Exception as ex:
        #print(f"Error: An unexpected error occurred while checking VLC availability: {ex}")
        return False

def open_clips_in_vlc(clips, status_callback):
    print(f"Info: Opening {len(clips)} clips in VLC.")
    """
    Open a list of video clips in VLC media player.

    Args:
        clips (list): A list of file paths to open in VLC.
    """
    if not clips:
        if status_callback:
            status_callback("Info: No clips available to play.")
        return

    # Determine the platform
    current_platform = platform.system()

    # Adjust paths for Windows
    if current_platform == "Windows":
        clips = [os.path.normpath(clip) for clip in clips]

    # Command to launch VLC
    try:
        if current_platform == "Windows":
            # Windows-specific VLC command
            vlc_path = r"C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
            if not os.path.exists(vlc_path):
                raise FileNotFoundError(f"Error: VLC not found at {vlc_path}.")
            vlc_command = [vlc_path, *clips]
        elif current_platform in ("Linux", "Darwin"):  # Darwin is macOS
            # Linux/macOS-specific VLC command
            vlc_command = ["vlc", *clips]
            if not shutil.which("vlc"):
                raise FileNotFoundError("Error: VLC is not installed or not in the PATH.")
        else:
            raise OSError(f"Error: Unsupported platform: {current_platform}")

        # Launch VLC
        subprocess.Popen(vlc_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        if status_callback:
            status_callback("Info: VLC launched successfully.")

    except FileNotFoundError as fnf_error:
        if status_callback:
            status_callback(f"Error: {fnf_error}")
    except OSError as os_error:
        if status_callback:
            status_callback(f"Error: {os_error}")
    except Exception as ex:
        if status_callback:
            status_callback(f"Error: An unexpected error occurred: {ex}")


