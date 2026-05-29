from __future__ import annotations

import configparser
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys
import threading
import time
from typing import Callable, Optional, Tuple

import requests
from pypresence import Presence


APP_NAME = "Xbox360 Presence"
CONFIG_FILE_NAME = "config.ini"
DEFAULT_CONFIG_FILE_NAME = "config_default.ini"
TITLE_IDS_FILE_NAME = "xbox360titleids.json"
POLL_INTERVAL_SECONDS = 15

PLACEHOLDER_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
PLACEHOLDER_IP_ADDRESS = "YOUR_XBOX_IP_HERE"

ICON_BASE_URL = "https://raw.githubusercontent.com/jnackmclain/Xbox360_presence/main/icons"
DEFAULT_IMAGE_URL = f"{ICON_BASE_URL}/default.png"
AURORA_IMAGE_URL = f"{ICON_BASE_URL}/00000166.png"

DEFAULT_CONFIG_TEXT = """[discord]
client_id = YOUR_CLIENT_ID_HERE

[xbox]
ip_address = YOUR_XBOX_IP_HERE
"""

StatusCallback = Callable[[str, str], None]
LogCallback = Callable[[str], None]


class ConfigError(RuntimeError):
    """Raised when the presence app cannot start because settings are missing."""


@dataclass
class PresenceSettings:
    config_path: Path
    client_id: str
    ip_address: str


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_base_dir() -> Path:
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def resource_path(file_name: str) -> Path:
    bundled_path = app_base_dir() / file_name
    if bundled_path.exists():
        return bundled_path
    return Path(__file__).resolve().parent / file_name


def user_config_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME
    return Path.home() / "AppData" / "Roaming" / APP_NAME


def get_config_path(prefer_local: bool = False) -> Path:
    override = os.environ.get("XBOX360_PRESENCE_CONFIG")
    if override:
        return Path(override).expanduser()

    if prefer_local:
        cwd_config = Path.cwd() / CONFIG_FILE_NAME
        cwd_default = Path.cwd() / DEFAULT_CONFIG_FILE_NAME
        if cwd_config.exists() or cwd_default.exists():
            return cwd_config
        return Path(__file__).resolve().parent / CONFIG_FILE_NAME

    return user_config_dir() / CONFIG_FILE_NAME


def ensure_config_file(
    config_path: Optional[Path] = None, prefer_local: bool = False
) -> Path:
    path = config_path or get_config_path(prefer_local=prefer_local)
    if path.exists():
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    default_path = resource_path(DEFAULT_CONFIG_FILE_NAME)
    if default_path.exists():
        path.write_text(default_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
    return path


def _read_config_parser(config_path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")
    return parser


def _is_unset(value: str, placeholder: str) -> bool:
    cleaned = (value or "").strip()
    return not cleaned or cleaned.upper() == placeholder.upper()


def load_settings(
    config_path: Optional[Path] = None,
    prefer_local: bool = False,
    require_ready: bool = True,
) -> PresenceSettings:
    path = ensure_config_file(config_path=config_path, prefer_local=prefer_local)
    parser = _read_config_parser(path)
    client_id = parser.get("discord", "client_id", fallback="").strip()
    ip_address = parser.get("xbox", "ip_address", fallback="").strip()

    if require_ready:
        if _is_unset(client_id, PLACEHOLDER_CLIENT_ID):
            raise ConfigError(
                "Discord client ID is not configured. Use Configure from the tray."
            )
        if _is_unset(ip_address, PLACEHOLDER_IP_ADDRESS):
            raise ConfigError(
                "Xbox IP address is not configured. Use Configure from the tray."
            )

    return PresenceSettings(path, client_id, ip_address)


def save_settings(client_id: str, ip_address: str, config_path: Optional[Path] = None) -> Path:
    path = ensure_config_file(config_path=config_path)
    parser = _read_config_parser(path)

    if not parser.has_section("discord"):
        parser.add_section("discord")
    if not parser.has_section("xbox"):
        parser.add_section("xbox")

    parser.set("discord", "client_id", client_id.strip())
    parser.set("xbox", "ip_address", ip_address.strip())

    with path.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)
    return path


_game_names_cache: Optional[dict] = None
_image_exists_cache = {}


def fetch_game_names() -> dict:
    global _game_names_cache
    if _game_names_cache is not None:
        return _game_names_cache

    with resource_path(TITLE_IDS_FILE_NAME).open("r", encoding="utf-8") as file:
        data = json.load(file)

    _game_names_cache = {game["TitleID"].upper(): game["Title"] for game in data}
    return _game_names_cache


def fetch_title_id(ip_address: str) -> Optional[str]:
    url = f"http://{ip_address}:9999/title"
    response = requests.get(url, timeout=5)

    if response.status_code != 200:
        return None

    try:
        data = response.json()
    except json.JSONDecodeError:
        return None

    title_id = data.get("titleid")
    if not title_id:
        return None

    title_id = str(title_id).strip()
    if title_id.startswith("0x"):
        title_id = title_id[2:]
    return title_id.upper()


def get_elapsed_time(start_time: datetime) -> str:
    elapsed = datetime.now() - start_time
    days, remainder = divmod(elapsed.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return (
            f"for {int(days)} day{'s' if days > 1 else ''}, "
            f"{int(hours)} hour{'s' if hours != 1 else ''}, and "
            f"{int(minutes)} minute{'s' if minutes != 1 else ''}"
        )
    if hours > 0:
        return (
            f"for {int(hours)} hour{'s' if hours != 1 else ''} and "
            f"{int(minutes)} minute{'s' if minutes != 1 else ''}"
        )
    return f"for {int(minutes)} minute{'s' if minutes != 1 else ''}"


def _image_url_for_title(title_id: str) -> str:
    image_url = f"{ICON_BASE_URL}/{title_id}.png"
    cached = _image_exists_cache.get(image_url)
    if cached is not None:
        return image_url if cached else DEFAULT_IMAGE_URL

    try:
        response = requests.get(image_url, timeout=5)
        exists = response.status_code == 200
    except requests.RequestException:
        exists = False

    _image_exists_cache[image_url] = exists
    return image_url if exists else DEFAULT_IMAGE_URL


def resolve_game(title_id: str) -> Tuple[str, str]:
    if title_id == "00000000":
        return "Aurora", AURORA_IMAGE_URL

    game_name = fetch_game_names().get(title_id, f"Unknown Title ID: {title_id}")
    return game_name, _image_url_for_title(title_id)


def update_discord_presence(
    rpc: Presence,
    ip_address: str,
    start_time: datetime,
    last_title_id: Optional[str],
    last_printed_minute: Optional[str],
    log_callback: Optional[LogCallback] = None,
) -> Tuple[datetime, Optional[str], Optional[str], str]:
    title_id = fetch_title_id(ip_address)

    if not title_id:
        try:
            rpc.clear()
        except Exception:
            pass
        return start_time, None, last_printed_minute, "Running: no title ID"

    game_name, image_url = resolve_game(title_id)

    if title_id != last_title_id:
        start_time = datetime.now()
        last_title_id = title_id

    elapsed_time = get_elapsed_time(start_time)
    if elapsed_time != last_printed_minute:
        message = (
            f"Displaying game '{game_name}' with Title ID: {title_id} "
            f"{elapsed_time}."
        )
        if log_callback:
            log_callback(message)
        last_printed_minute = elapsed_time

    rpc.update(
        details=game_name,
        large_image=image_url,
        large_text=game_name,
        start=int(start_time.timestamp()),
    )

    return start_time, last_title_id, last_printed_minute, f"Playing {game_name} {elapsed_time}"


class PresenceWorker:
    def __init__(
        self,
        poll_interval: int = POLL_INTERVAL_SECONDS,
        status_callback: Optional[StatusCallback] = None,
    ) -> None:
        self.poll_interval = poll_interval
        self.status_callback = status_callback
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.state = "stopped"
        self.message = "Stopped"

    @property
    def is_active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        with self._lock:
            if self.is_active:
                return
            self._stop_event = threading.Event()
            self._set_status("starting", "Starting")
            self._thread = threading.Thread(
                target=self._run,
                name="Xbox360PresenceWorker",
                daemon=True,
            )
            self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        thread = self._thread
        if thread is None or not thread.is_alive():
            self._set_status("stopped", "Stopped")
            return

        self._set_status("stopping", "Stopping")
        self._stop_event.set()
        thread.join(timeout=timeout)
        if thread.is_alive():
            self._set_status("stopping", "Stopping after current update")

    def restart(self) -> None:
        self.stop()
        self.start()

    def _set_status(self, state: str, message: str) -> None:
        self.state = state
        self.message = message
        if self.status_callback:
            self.status_callback(state, message)

    def _run(self) -> None:
        rpc = None
        connected = False

        try:
            settings = load_settings(require_ready=True)
            self._set_status("connecting", "Connecting to Discord")

            rpc = Presence(settings.client_id)
            rpc.connect()
            connected = True

            start_time = datetime.now()
            last_title_id = None
            last_printed_minute = None
            self._set_status("running", f"Running: polling {settings.ip_address}")

            while not self._stop_event.is_set():
                try:
                    (
                        start_time,
                        last_title_id,
                        last_printed_minute,
                        status_message,
                    ) = update_discord_presence(
                        rpc,
                        settings.ip_address,
                        start_time,
                        last_title_id,
                        last_printed_minute,
                    )
                    self._set_status("running", status_message)
                except requests.RequestException as exc:
                    try:
                        rpc.clear()
                    except Exception:
                        pass
                    last_title_id = None
                    self._set_status("running", f"Running: waiting for Xbox ({exc})")
                except Exception as exc:
                    self._set_status("error", f"Stopped: {exc}")
                    break

                if self._stop_event.wait(self.poll_interval):
                    break

        except ConfigError as exc:
            self._set_status("needs_config", str(exc))
        except Exception as exc:
            self._set_status("error", f"Stopped: {exc}")
        finally:
            if rpc is not None and connected:
                try:
                    rpc.clear()
                except Exception:
                    pass
                try:
                    rpc.close()
                except Exception:
                    pass

            if self._stop_event.is_set():
                self._set_status("stopped", "Stopped")


def run_foreground(ip_override: Optional[str] = None) -> None:
    settings = load_settings(prefer_local=True, require_ready=False)

    if _is_unset(settings.client_id, PLACEHOLDER_CLIENT_ID):
        raise ConfigError(f"Please update your client_id in {settings.config_path}")

    ip_address = ip_override or settings.ip_address
    if _is_unset(ip_address, PLACEHOLDER_IP_ADDRESS):
        ip_address = input(
            "Enter the IP address of your Xbox (Ensure Nova Web UI is running): "
        ).strip()

    if not ip_address:
        raise ConfigError("Xbox IP address is required.")

    rpc = Presence(settings.client_id)
    rpc.connect()

    start_time = datetime.now()
    last_title_id = None
    last_printed_minute = None

    try:
        while True:
            try:
                start_time, last_title_id, last_printed_minute, _ = (
                    update_discord_presence(
                        rpc,
                        ip_address,
                        start_time,
                        last_title_id,
                        last_printed_minute,
                        log_callback=lambda message: print(message, flush=True),
                    )
                )
            except requests.RequestException as exc:
                print(
                    f"Error connecting to the Xbox at http://{ip_address}:9999/title: {exc}. "
                    "Xbox presence cleared. Retrying...",
                    flush=True,
                )
                try:
                    rpc.clear()
                except Exception:
                    pass
                last_title_id = None
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Disconnecting from Discord...", flush=True)
    finally:
        try:
            rpc.clear()
        finally:
            rpc.close()
        print("Disconnected. Goodbye!", flush=True)
