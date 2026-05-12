# RD4 Desktop

Standalone desktop-версия RD4 на Python + PySide2 + SQLite.

Проект вынесен из исходного web-репозитория `rd4`, где оставались `client/` и `server/`. Текущий проект должен развиваться как отдельное desktop-приложение.

## Stack

```text
Python: 3.8.x для Windows 7/10 build
UI: PySide2 / Qt 5.15
Database: SQLite
ORM: SQLAlchemy
Migrations: Alembic
DOCX: docxtpl / python-docx
Packaging: PyInstaller
```

## Install

Подробная инструкция по созданию Python 3.8 окружения: [`ENVIRONMENT_SETUP.md`](ENVIRONMENT_SETUP.md).

Target Windows/Python 3.8:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Linux/macOS development without PySide2:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r requirements-dev.txt
```

## Run

```bash
python -m app.main
```

Local development DB in the project directory:

```bash
RD4_DATA_DIR=.rd4 .venv/bin/python -m app.main
```

First empty DB creates:

```text
login: admin
password: admin
```

## Checks

```bash
.venv/bin/python -m pytest tests
RD4_DATA_DIR=.rd4 .venv/bin/python -m alembic check
RD4_DATA_DIR=.rd4 .venv/bin/python -m app.services.smoke
```

## Build

See [`WINDOWS7_BUILD_GUIDE.md`](WINDOWS7_BUILD_GUIDE.md) and [`packaging/README.md`](packaging/README.md).
