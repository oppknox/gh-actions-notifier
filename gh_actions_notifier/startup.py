"""Manage Windows startup shortcut."""

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def _startup_dir() -> Path:
    return Path(os.environ.get("APPDATA", Path.home())) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _shortcut_path() -> Path:
    return _startup_dir() / "GH Actions Notifier.vbs"


def _build_vbs_script() -> str:
    """VBS wrapper that launches pythonw with run.pyw (no console window)."""
    # Find the run.pyw relative to this package
    pkg_dir = Path(__file__).resolve().parent
    run_pyw = pkg_dir.parent / "run.pyw"
    pythonw = Path(sys.executable).parent / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)
    return (
        f'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.CurrentDirectory = "{run_pyw.parent}"\n'
        f'WshShell.Run """{pythonw}"" ""{run_pyw}""", 0, False\n'
    )


def is_startup_enabled() -> bool:
    return _shortcut_path().exists()


def enable_startup() -> None:
    path = _shortcut_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_build_vbs_script(), encoding="utf-8")
    log.info("Startup enabled: %s", path)


def disable_startup() -> None:
    path = _shortcut_path()
    if path.exists():
        path.unlink()
        log.info("Startup disabled: removed %s", path)
