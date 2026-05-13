from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.paths import get_data_dir


@dataclass(frozen=True)
class Settings:
    """Настройки запуска, вычисленные из окружения настольного приложения."""

    data_dir: Path
    database_path: Path

    @property
    def database_url(self) -> str:
        """Вернуть SQLite URL для SQLAlchemy на основе пути к базе данных."""

        # SQLAlchemy ожидает прямые слеши в URL-путях на всех платформах.
        return f"sqlite:///{self.database_path.as_posix()}"


def load_settings() -> Settings:
    """Собрать настройки из окружения без создания директорий."""

    # get_data_dir() сначала учитывает RD4_DATA_DIR, затем берет путь по ОС.
    data_dir = get_data_dir()
    return Settings(data_dir=data_dir, database_path=data_dir / "rd4.db")


# Загружаем один раз при импорте, чтобы приложение использовало единый конфиг.
settings = load_settings()
