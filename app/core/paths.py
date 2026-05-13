from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIR_NAME = "RD4"


def get_bundle_dir() -> Path:
    """Вернуть корень приложения: временный каталог PyInstaller или исходники."""

    # В собранном приложении PyInstaller кладет ресурсы во временный _MEIPASS.
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")).resolve()

    # В режиме разработки поднимаемся от app/core/paths.py к корню репозитория.
    return Path(__file__).resolve().parents[2]


def get_data_dir() -> Path:
    """Определить директорию пользовательских данных RD4."""

    # Переменная окружения нужна для разработки, тестов и bundle smoke-проверок.
    custom_dir = os.environ.get("RD4_DATA_DIR")
    if custom_dir:
        return Path(custom_dir).expanduser().resolve()

    if sys.platform.startswith("win"):
        # Основной путь Windows: %APPDATA%\RD4, с запасным вариантом через home.
        appdata = os.environ.get("APPDATA")
        base_dir = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base_dir / APP_DIR_NAME

    return Path.home() / ".rd4"


def ensure_data_dir() -> Path:
    """Создать директорию данных при необходимости и вернуть ее путь."""

    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_dir() -> Path:
    """Вернуть путь к директории логов внутри пользовательских данных."""

    return get_data_dir() / "logs"


def ensure_log_dir() -> Path:
    """Создать директорию логов при необходимости и вернуть ее путь."""

    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_file() -> Path:
    """Вернуть путь к основному файлу журнала приложения."""

    return get_log_dir() / "rd4.log"


def get_resource_path(*parts: str) -> Path:
    """Собрать путь к ресурсу приложения в исходниках или PyInstaller bundle."""

    return get_bundle_dir().joinpath(*parts)
