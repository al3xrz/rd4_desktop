from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.paths import get_data_dir


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_path: Path

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


def load_settings() -> Settings:
    data_dir = get_data_dir()
    return Settings(data_dir=data_dir, database_path=data_dir / "rd4.db")


settings = load_settings()
