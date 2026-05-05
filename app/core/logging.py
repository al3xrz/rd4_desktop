from __future__ import annotations

import logging

from app.core.paths import ensure_log_dir, get_log_file


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    ensure_log_dir()
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(get_log_file(), encoding="utf-8"),
        ],
        force=True,
    )
