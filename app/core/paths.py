from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIR_NAME = "RD4"


def get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parents[2]


def get_data_dir() -> Path:
    custom_dir = os.environ.get("RD4_DATA_DIR")
    if custom_dir:
        return Path(custom_dir).expanduser().resolve()

    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        base_dir = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base_dir / APP_DIR_NAME

    return Path.home() / ".rd4"


def ensure_data_dir() -> Path:
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_dir() -> Path:
    return get_data_dir() / "logs"


def ensure_log_dir() -> Path:
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_file() -> Path:
    return get_log_dir() / "rd4.log"


def get_resource_path(*parts: str) -> Path:
    return get_bundle_dir().joinpath(*parts)
