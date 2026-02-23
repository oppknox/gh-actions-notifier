"""GitHub authentication via Personal Access Token."""

import logging
import threading
import tkinter as tk
from tkinter import simpledialog
import webbrowser

log = logging.getLogger(__name__)

# URL to create a new PAT with the right scopes pre-selected
NEW_TOKEN_URL = "https://github.com/settings/tokens/new?scopes=repo&description=GH+Actions+Notifier"


class Authenticator:
    def __init__(self, config: dict, state, github_client) -> None:
        self.config = config
        self._state = state
        self._github = github_client

    def authenticate(self, stop_event: threading.Event) -> str | None:
        """Open browser to create PAT, show input dialog, validate token.
        Returns username on success, None on failure.
        """
        # Open the GitHub token creation page
        webbrowser.open(NEW_TOKEN_URL)

        # Show a tkinter input dialog (must run on its own Tk root)
        token = self._ask_for_token()
        if not token:
            log.info("Auth cancelled - no token entered")
            return None

        token = token.strip()
        self._state.token = token

        user = self._github.get_user()
        if user:
            return user

        # Token invalid - clear it
        self._state.token = ""
        log.error("Token validation failed")
        return None

    @staticmethod
    def _ask_for_token() -> str | None:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        token = simpledialog.askstring(
            "GH Actions Notifier",
            "Paste your GitHub Personal Access Token:\n\n"
            "(A browser tab opened to create one - select the 'repo' scope,\n"
            " generate it, then paste it here)",
            parent=root,
        )
        root.destroy()
        return token
