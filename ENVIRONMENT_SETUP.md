# Environment setup

Пошаговая инструкция по созданию окружения RD4 Desktop с нужной версией Python и `.venv`.

## Целевая версия

Для Windows 7/10 build используется:

```text
Python 3.8.x
```

В репозитории есть `.python-version`:

```text
3.8
```

Она помогает `uv` и другим менеджерам выбрать нужную версию Python.

## Вариант A: Windows build environment

Этот вариант используйте для настоящей сборки `RD4.exe`.

1. Установите Python 3.8.x.
2. Откройте `cmd` или PowerShell в корне проекта.
3. Проверьте версию:

```bat
python --version
```

Ожидаемо:

```text
Python 3.8.x
```

4. Создайте `.venv`:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
```

5. Установите зависимости:

```bat
pip install -r requirements.txt
```

Не устанавливайте `requirements-dev.txt` в это же окружение для Windows build: там указан `pyinstaller>=6`, а целевой `requirements.txt` фиксирует `pyinstaller>=4.10,<5`.

6. Проверьте приложение из исходников:

```bat
python -m app.main
```

## Вариант B: uv в Linux/macOS или локальной dev-среде

Если системного `python3.8` нет, `uv` может скачать Python 3.8 и создать `.venv`.

Обычный вариант:

```bash
uv python install 3.8
uv venv --python 3.8 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Если домашний cache недоступен или проект находится в sandbox-среде, задайте локальные пути:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_PYTHON_INSTALL_DIR=.uv/python uv python install 3.8
UV_CACHE_DIR=/tmp/uv-cache UV_PYTHON_INSTALL_DIR=.uv/python uv venv --python 3.8 .venv
UV_CACHE_DIR=/tmp/uv-cache UV_PYTHON_INSTALL_DIR=.uv/python uv pip install --python .venv/bin/python -r requirements.txt
```

Проверьте:

```bash
.venv/bin/python --version
UV_CACHE_DIR=/tmp/uv-cache uv pip check --python .venv/bin/python
```

## Вариант C: dev-only environment

`requirements-dev.txt` предназначен для разработки на более новых системах, где не нужна строгая Windows 7/Python 3.8 упаковка.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r requirements-dev.txt
```

Такое окружение не является проверкой Windows 7 build.

## Проверки

После установки:

```bash
.venv/bin/python -m pytest tests
RD4_DATA_DIR=.rd4 .venv/bin/python -m alembic check
RD4_DATA_DIR=.rd4 .venv/bin/python -m app.main
```

Для GUI в Linux может понадобиться доступ к X11/Wayland и Qt platform plugins.

## Что не коммитить

Эти каталоги и файлы являются локальными:

```text
.venv/
.uv/
.rd4/
build/
dist/
```

Они уже добавлены в `.gitignore`.
