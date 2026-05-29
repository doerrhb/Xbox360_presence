from __future__ import annotations

import os
from pathlib import Path
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

from PIL import Image, ImageDraw
import pystray

from presence_service import (
    APP_NAME,
    PLACEHOLDER_CLIENT_ID,
    PLACEHOLDER_IP_ADDRESS,
    PresenceWorker,
    ensure_config_file,
    load_settings,
    resource_path,
    save_settings,
)
from windows_startup import is_startup_enabled, set_startup_enabled


class TrayApplication:
    def __init__(self) -> None:
        self.worker = PresenceWorker(status_callback=self._on_status_changed)
        self.icon: Optional[pystray.Icon] = None
        self._config_window_lock = threading.Lock()
        self._config_window_open = False

    def run(self) -> None:
        self.icon = pystray.Icon(
            "Xbox360Presence",
            self._load_icon_image(),
            APP_NAME,
            menu=self._build_menu(),
        )
        self.worker.start()
        self.icon.run()

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: self._status_label(),
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Start Rich Presence",
                self._start_presence,
                enabled=lambda item: not self.worker.is_active,
                default=True,
            ),
            pystray.MenuItem(
                "Stop Rich Presence",
                self._stop_presence,
                enabled=lambda item: self.worker.is_active,
            ),
            pystray.MenuItem(
                "Restart Rich Presence",
                self._restart_presence,
                enabled=lambda item: self.worker.is_active,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Configure...", self._open_config_dialog),
            pystray.MenuItem("Open Config Folder", self._open_config_folder),
            pystray.MenuItem(
                "Run at Windows startup",
                self._toggle_startup,
                checked=lambda item: is_startup_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._exit_app),
        )

    def _status_label(self) -> str:
        message = self.worker.message or "Stopped"
        if len(message) > 64:
            message = f"{message[:61]}..."
        return f"Status: {message}"

    def _load_icon_image(self) -> Image.Image:
        icon_path = resource_path("avatar.ico")
        try:
            return Image.open(icon_path)
        except Exception:
            image = Image.new("RGBA", (64, 64), (20, 20, 20, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse((8, 8, 56, 56), fill=(38, 132, 62, 255))
            draw.rectangle((20, 27, 44, 37), fill=(255, 255, 255, 255))
            return image

    def _on_status_changed(self, state: str, message: str) -> None:
        if self.icon is None:
            return

        title = f"{APP_NAME} - {message}"
        self.icon.title = title[:127]
        self.icon.update_menu()

    def _start_presence(self, icon=None, item=None) -> None:
        self.worker.start()
        self._refresh_menu()

    def _stop_presence(self, icon=None, item=None) -> None:
        self.worker.stop()
        self._refresh_menu()

    def _restart_presence(self, icon=None, item=None) -> None:
        self.worker.restart()
        self._refresh_menu()

    def _toggle_startup(self, icon=None, item=None) -> None:
        try:
            set_startup_enabled(not is_startup_enabled())
        except RuntimeError as exc:
            messagebox.showerror(APP_NAME, str(exc))
        self._refresh_menu()

    def _open_config_folder(self, icon=None, item=None) -> None:
        config_path = ensure_config_file()
        folder = config_path.parent
        if os.name == "nt":
            os.startfile(str(folder))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    def _open_config_dialog(self, icon=None, item=None) -> None:
        with self._config_window_lock:
            if self._config_window_open:
                return
            self._config_window_open = True

        thread = threading.Thread(
            target=self._show_config_dialog,
            name="Xbox360PresenceConfig",
            daemon=True,
        )
        thread.start()

    def _show_config_dialog(self) -> None:
        config_path = ensure_config_file()
        settings = load_settings(config_path=config_path, require_ready=False)

        root = tk.Tk()
        root.title(f"{APP_NAME} Configuration")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        frame = tk.Frame(root, padx=16, pady=14)
        frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(frame, text="Discord Client ID").grid(row=0, column=0, sticky="w")
        client_id_var = tk.StringVar(
            value=settings.client_id if settings.client_id else PLACEHOLDER_CLIENT_ID
        )
        client_entry = tk.Entry(frame, textvariable=client_id_var, width=44)
        client_entry.grid(row=1, column=0, sticky="ew", pady=(2, 10))

        tk.Label(frame, text="Xbox IP Address").grid(row=2, column=0, sticky="w")
        ip_var = tk.StringVar(
            value=settings.ip_address if settings.ip_address else PLACEHOLDER_IP_ADDRESS
        )
        ip_entry = tk.Entry(frame, textvariable=ip_var, width=44)
        ip_entry.grid(row=3, column=0, sticky="ew", pady=(2, 12))

        path_label = tk.Label(frame, text=str(config_path), fg="#555555")
        path_label.grid(row=4, column=0, sticky="w", pady=(0, 12))

        buttons = tk.Frame(frame)
        buttons.grid(row=5, column=0, sticky="e")

        def save() -> None:
            client_id = client_id_var.get().strip()
            ip_address = ip_var.get().strip()

            if not client_id or client_id == PLACEHOLDER_CLIENT_ID:
                messagebox.showerror(APP_NAME, "Enter your Discord client ID.")
                return
            if not ip_address or ip_address == PLACEHOLDER_IP_ADDRESS:
                messagebox.showerror(APP_NAME, "Enter your Xbox IP address.")
                return

            should_start_after_save = self.worker.state == "needs_config"
            was_running = self.worker.is_active

            save_settings(client_id, ip_address, config_path=config_path)
            if was_running:
                self.worker.restart()
            elif should_start_after_save:
                self.worker.start()
            messagebox.showinfo(APP_NAME, "Configuration saved.")
            root.destroy()

        tk.Button(buttons, text="Cancel", command=root.destroy, width=10).grid(
            row=0, column=0, padx=(0, 8)
        )
        tk.Button(buttons, text="Save", command=save, width=10).grid(row=0, column=1)

        try:
            client_entry.focus_set()
            root.mainloop()
        finally:
            with self._config_window_lock:
                self._config_window_open = False

    def _exit_app(self, icon=None, item=None) -> None:
        self.worker.stop(timeout=5)
        if self.icon is not None:
            self.icon.stop()

    def _refresh_menu(self) -> None:
        if self.icon is not None:
            self.icon.update_menu()


def main() -> None:
    TrayApplication().run()


if __name__ == "__main__":
    main()
