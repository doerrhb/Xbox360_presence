from __future__ import annotations

from pathlib import Path
import sys


RUN_VALUE_NAME = "Xbox360Presence"
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _quote(value: str) -> str:
    escaped = value.replace('"', r'\"')
    return f'"{escaped}"'


def startup_command() -> str:
    if getattr(sys, "frozen", False):
        return _quote(sys.executable)

    script_path = Path(__file__).resolve().with_name("xbox360_presence_tray.py")
    return f"{_quote(sys.executable)} {_quote(str(script_path))}"


def _open_run_key(root, access: int):
    import winreg

    return winreg.OpenKey(root, RUN_KEY_PATH, 0, access)


def _read_startup_value(root) -> str:
    import winreg

    try:
        with _open_run_key(root, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, RUN_VALUE_NAME)
            return str(value)
    except FileNotFoundError:
        return ""
    except OSError:
        return ""


def get_startup_value() -> str:
    if sys.platform != "win32":
        return ""

    import winreg

    return _read_startup_value(winreg.HKEY_CURRENT_USER) or _read_startup_value(
        winreg.HKEY_LOCAL_MACHINE
    )


def is_startup_enabled() -> bool:
    value = get_startup_value()
    return bool(value)


def set_startup_enabled(enabled: bool) -> None:
    if sys.platform != "win32":
        return

    import winreg

    if enabled:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH) as key:
            winreg.SetValueEx(
                key,
                RUN_VALUE_NAME,
                0,
                winreg.REG_SZ,
                startup_command(),
            )
        return

    machine_value = _read_startup_value(winreg.HKEY_LOCAL_MACHINE)
    if machine_value:
        try:
            with _open_run_key(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, RUN_VALUE_NAME)
        except OSError as exc:
            raise RuntimeError(
                "The all-users startup entry was created by the installer. "
                "Run Xbox360 Presence as administrator or change it from the installer."
            ) from exc

    try:
        with _open_run_key(winreg.HKEY_CURRENT_USER, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, RUN_VALUE_NAME)
    except FileNotFoundError:
        pass
    except OSError:
        pass
