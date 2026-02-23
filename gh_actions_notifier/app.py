"""Application orchestrator - lifecycle and threading."""

import logging
import os
import threading
from pathlib import Path

from .auth import Authenticator
from .config import load_config
from .github_api import GitHubClient
from .notifier import Notifier
from .poller import Poller
from .state import StateManager
from .tray import TrayIcon

log = logging.getLogger(__name__)


def _log_dir() -> Path:
    return Path(os.environ.get("APPDATA", Path.home())) / "gh-actions-notifier"


class Application:
    def __init__(self) -> None:
        self.log_path = self._setup_logging()
        self.config = load_config()
        self.state = StateManager()
        self.github = GitHubClient(self.state)
        self.auth = Authenticator(self.config, self.state, self.github)
        self.notifier = Notifier()
        self.poller = Poller(self, self.config, self.state, self.github, self.notifier)
        self.tray = TrayIcon(self)

        self._stop_event = threading.Event()
        self._poll_now_event = threading.Event()
        self._auth_requested = threading.Event()
        self.status_text = "Disconnected"

    def _setup_logging(self) -> Path:
        log_dir = _log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        return log_file

    def run(self) -> None:
        log.info("Starting GH Actions Notifier")
        self.tray.run(setup_callback=self._on_tray_ready)

    def _on_tray_ready(self, icon) -> None:
        """Called by pystray in a background thread after the icon is visible."""
        icon.visible = True
        log.info("Tray icon visible")
        threading.Thread(target=self._background_loop, daemon=True).start()

    def _background_loop(self) -> None:
        # Try to authenticate with existing token
        if self.state.token:
            user = self.github.get_user()
            if user:
                self._set_connected(user)
            else:
                self.state.token = ""
                self._set_disconnected("Token expired")

        while not self._stop_event.is_set():
            # Handle auth requests
            if self._auth_requested.is_set():
                self._auth_requested.clear()
                self._do_auth()

            # Poll if connected
            if self.state.token:
                self.tray.set_icon("polling")
                try:
                    self.poller.poll_once()
                    self.tray.set_icon("ok")
                except Exception as e:
                    log.error("Poll error: %s", e)
                    self.tray.set_icon("error")
                    self.status_text = f"Error: {e}"
                    self.tray.update_menu()

            # Interruptible sleep
            interval = self.config.get("poll_interval", 30)
            self._poll_now_event.wait(timeout=interval)
            self._poll_now_event.clear()

    def _do_auth(self) -> None:
        self.status_text = "Authenticating..."
        self.tray.update_menu()
        self.tray.set_icon("polling")
        try:
            user = self.auth.authenticate(self._stop_event)
            if user:
                self._set_connected(user)
            else:
                self._set_disconnected("Auth failed")
        except Exception as e:
            log.error("Auth error: %s", e)
            self._set_disconnected(f"Auth error: {e}")

    def _set_connected(self, username: str) -> None:
        self.status_text = f"Connected as {username}"
        self.tray.set_icon("ok")
        self.tray.update_menu()
        log.info("Connected as %s", username)

    def _set_disconnected(self, reason: str = "Disconnected") -> None:
        self.status_text = reason
        self.tray.set_icon("disconnected")
        self.tray.update_menu()
        log.info("Disconnected: %s", reason)

    def request_auth(self) -> None:
        self._auth_requested.set()
        self._poll_now_event.set()  # Wake the loop

    def poll_now(self) -> None:
        self._poll_now_event.set()

    def reload_config(self) -> None:
        self.config = load_config()
        self.poller.config = self.config
        self.auth.config = self.config
        self.poller.clear_repo_cache()
        log.info("Config reloaded")
        self.status_text = "Config reloaded"
        self.tray.update_menu()

    def shutdown(self) -> None:
        log.info("Shutting down")
        self._stop_event.set()
        self._poll_now_event.set()
        self.tray.stop()
