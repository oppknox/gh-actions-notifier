"""Thread-safe token + last-seen run IDs persistence."""

import json
import logging
import os
import threading
from pathlib import Path

log = logging.getLogger(__name__)


def _state_path() -> Path:
    return (
        Path(os.environ.get("APPDATA", Path.home())) / "gh-actions-notifier" / "state.json"
    )


class StateManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._path = _state_path()
        self._data: dict = {"token": "", "last_seen_run_ids": {}}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log.error("Failed to load state: %s", e)

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    @property
    def token(self) -> str:
        with self._lock:
            return self._data.get("token", "")

    @token.setter
    def token(self, value: str) -> None:
        with self._lock:
            self._data["token"] = value
            self._save()

    def get_last_seen_id(self, repo_full_name: str) -> int:
        with self._lock:
            return self._data.get("last_seen_run_ids", {}).get(repo_full_name, 0)

    def set_last_seen_id(self, repo_full_name: str, run_id: int) -> None:
        with self._lock:
            self._data.setdefault("last_seen_run_ids", {})[repo_full_name] = run_id
            self._save()
