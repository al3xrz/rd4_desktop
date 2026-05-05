from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.core.paths import ensure_data_dir, get_resource_path


PROJECT_ROOT = get_resource_path()


def get_alembic_config() -> Config:
    config = Config(str(get_resource_path("alembic.ini")))
    config.set_main_option("script_location", str(get_resource_path("migrations")))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def run_migrations() -> None:
    ensure_data_dir()
    command.upgrade(get_alembic_config(), "head")
