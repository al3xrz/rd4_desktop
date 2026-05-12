# AGENTS.md

## Project overview

This repository is the standalone RD4 desktop application.

It contains only the desktop stack:

- `app/` — application source code
- `app/core/` — config, paths, logging, database, migrations bootstrap
- `app/models/` — SQLAlchemy ORM models
- `app/repositories/` — data access layer
- `app/services/` — business logic and domain operations
- `app/ui/` — PySide2 UI
- `app/templates/` — DOCX templates
- `migrations/` — Alembic migrations
- `tests/` — smoke/unit tests
- `packaging/` — PyInstaller build files

## Architecture rules

Dependency direction:

```text
ui -> services -> repositories -> models/core
```

Do not introduce reverse dependencies:

```text
repositories -> ui
models -> services
services -> ui
```

Keep `ARCHITECTURE.md` in the repository root up to date when changing application structure, dependency direction, startup flow, database/migration rules, packaging, or major UI/service/model flows.

Keep `docs/` up to date when changing project behavior:

- `docs/user/` — user-facing workflows and UI behavior.
- `docs/admin/` — installation, data paths, database backend, backups, packaging, maintenance.
- `docs/developer/` — architecture, dependencies, migrations, validation, contributor workflow.

## Transaction rules

One business operation equals one service-level transaction.

Repositories must not commit. They may `flush()` to assign IDs.

## Database

SQLite DB location:

```text
Windows: %APPDATA%\RD4\rd4.db
Linux/macOS: ~/.rd4/rd4.db
Development override: RD4_DATA_DIR=.rd4
```

SQLite pragmas must stay enabled:

```sql
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

## Validation

Before finishing changes, run the relevant checks:

```bash
.venv/bin/python -m pytest tests
RD4_DATA_DIR=.rd4 .venv/bin/python -m alembic check
RD4_DATA_DIR=.rd4 .venv/bin/python -m app.main
```

For packaging work:

```bash
.venv/bin/python -m PyInstaller packaging/rd4.spec --noconfirm
RD4_DATA_DIR=.rd4_bundle_smoke dist/RD4/RD4
```

## Safety

- Do not edit generated DB files or logs.
- Do not commit `.venv/`, `.rd4/`, `build/`, or `dist/`.
- Do not hard-delete business rows unless explicitly requested.
- Use soft-delete fields for contracts, payments, acts, act service rows, and med services.
- Keep Windows 7/Python 3.8 compatibility in mind before changing dependencies.
