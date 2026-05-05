from __future__ import annotations

from pathlib import Path


def test_init_database_creates_sqlite_file(tmp_path, monkeypatch):
    data_dir = tmp_path / "rd4-data"
    monkeypatch.setenv("RD4_DATA_DIR", str(data_dir))

    from app.core import config
    from app.core import database

    database.settings = config.load_settings()
    database.get_engine.cache_clear()
    database.get_session_factory.cache_clear()

    database.init_database()

    assert Path(database.settings.database_path).is_file()

    with database.get_engine().connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert connection.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
        assert connection.exec_driver_sql("PRAGMA synchronous").scalar() == 1


def test_run_migrations_creates_version_table(tmp_path, monkeypatch):
    data_dir = tmp_path / "rd4-data"
    monkeypatch.setenv("RD4_DATA_DIR", str(data_dir))

    from app.core import config
    from app.core import database
    from app.core import migrations

    current_settings = config.load_settings()
    database.settings = current_settings
    migrations.settings = current_settings
    database.get_engine.cache_clear()
    database.get_session_factory.cache_clear()

    database.init_database()
    migrations.run_migrations()

    with database.get_engine().connect() as connection:
        version = connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()

    assert version is not None
