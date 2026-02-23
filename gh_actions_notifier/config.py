"""JSON config at %APPDATA%\\gh-actions-notifier\\config.json.

Manages a simple JSON configuration file with poll interval and
repo allowlist/blocklist settings. Missing keys are filled from defaults.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "poll_interval": 30,
    "allowlist": [],
    "blocklist": [],
}

def _config_dir() -> Path:
    return Path(os.environ.get("APPDATA", Path.home())) / "gh-actions-notifier"


def config_path() -> Path:
    return _config_dir() / "config.json"


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = {**DEFAULT_CONFIG, **data}
        return merged
    except (json.JSONDecodeError, OSError) as e:
        log.error("Failed to load config: %s", e)
        return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    log.info("Config saved to %s", path)
