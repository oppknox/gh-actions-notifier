"""GitHub authentication via Personal Access Token.

Opens the GitHub token creation page in the user's browser, then shows
a tkinter dialog to paste the token. The token is validated against
the GitHub API before being stored.
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
import webbrowser

log = logging.getLogger(__name__)

# URL to create a new PAT with the right scopes pre-selected
NEW_TOKEN_URL = "https://github.com/settings/tokens/new?scopes=repo&description=GH+Actions+Notifier"


class Authenticator:
    """Handles GitHub Personal Access Token authentication."""

    def __init__(self, config: dict, state, github_client) -> None:
        self.config = config
        self._state = state
        self._github = github_client

    def authenticate(self, stop_event: threading.Event) -> str | None:
        """Open browser to create a PAT, show input dialog, and validate.

        Returns the authenticated username on success, or None on failure.
        """
        webbrowser.open(NEW_TOKEN_URL)

        token = self._ask_for_token()
        if not token:
            log.info("Auth cancelled - no token entered")
            return None

        token = token.strip()
        if not token.startswith(("ghp_", "github_pat_")):
            log.warning("Token doesn't match expected GitHub PAT format")

        self._state.token = token
        user = self._github.get_user()
        if user:
            return user

        # Token invalid - clear it and notify user
        self._state.token = ""
        log.error("Token validation failed - GitHub API rejected the token")
        self._show_error("Authentication failed. The token was rejected by GitHub.\n\n"
                         "Make sure you copied the full token and that it has the 'repo' scope.")
        return None

    @staticmethod
    def _ask_for_token() -> str | None:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        token = simpledialog.askstring(
            "GH Actions Notifier",
            "Paste your GitHub Personal Access Token:\n\n"
            "(A browser tab opened to create one — select the 'repo' scope,\n"
            " generate it, then paste it here)",
            parent=root,
        )
        root.destroy()
        return token

    @staticmethod
    def _show_error(message: str) -> None:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror("GH Actions Notifier", message, parent=root)
        root.destroy()
