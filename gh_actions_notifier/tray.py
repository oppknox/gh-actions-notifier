"""System tray icon with right-click menu."""

from __future__ import annotations

import logging
import os

import pystray

from . import icons
from .config import config_path
from .startup import is_startup_enabled, enable_startup, disable_startup

log = logging.getLogger(__name__)


class TrayIcon:
    """Manages the Windows system tray icon and its right-click context menu."""

    def __init__(self, app) -> None:
        self._app = app
        self._icon: pystray.Icon | None = None

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(self._app.status_text, lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Authenticate", self._on_authenticate),
            pystray.MenuItem("Poll Now", self._on_poll_now),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Config", self._on_open_config),
            pystray.MenuItem("Reload Config", self._on_reload_config),
            pystray.MenuItem("Open Log", self._on_open_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Start with Windows",
                self._on_toggle_startup,
                checked=lambda _: is_startup_enabled(),
            ),
            pystray.MenuItem("Quit", self._on_quit),
        )

    def run(self, setup_callback) -> None:
        self._icon = pystray.Icon(
            name="gh-actions-notifier",
            icon=icons.icon_disconnected(),
            title="GH Actions Notifier",
            menu=self._build_menu(),
        )
        self._icon.run(setup=setup_callback)

    def set_icon(self, status: str) -> None:
        if self._icon is None:
            return
        icon_map = {
            "ok": icons.icon_ok,
            "error": icons.icon_error,
            "disconnected": icons.icon_disconnected,
            "polling": icons.icon_polling,
        }
        fn = icon_map.get(status, icons.icon_disconnected)
        self._icon.icon = fn()

    def update_menu(self) -> None:
        if self._icon is not None:
            self._icon.menu = self._build_menu()
            self._icon.update_menu()

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()

    def _on_authenticate(self, icon, item) -> None:
        self._app.request_auth()

    def _on_poll_now(self, icon, item) -> None:
        self._app.poll_now()

    def _on_open_config(self, icon, item) -> None:
        path = config_path()
        if not path.exists():
            from .config import save_config, DEFAULT_CONFIG
            save_config(DEFAULT_CONFIG)
        os.startfile(str(path))

    def _on_reload_config(self, icon, item) -> None:
        self._app.reload_config()

    def _on_open_log(self, icon, item) -> None:
        log_path = self._app.log_path
        if log_path and log_path.exists():
            os.startfile(str(log_path))

    def _on_toggle_startup(self, icon, item) -> None:
        if is_startup_enabled():
            disable_startup()
        else:
            enable_startup()

    def _on_quit(self, icon, item) -> None:
        self._app.shutdown()
