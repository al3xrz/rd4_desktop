# RD4 PyInstaller packaging

Цель сборки: desktop-приложение RD4 для Windows, включая Windows 7 при сборке на совместимом окружении.

## Рекомендуемое окружение

```text
Windows 7 VM или Windows 10 VM
Python 3.8.x
PySide2
PyInstaller
```

## Сборка

Из корня репозитория:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pyinstaller packaging\rd4.spec
```

`requirements.txt` предназначен именно для целевого Python 3.8.x. Для разработки на более новом Linux/Python окружении используйте `requirements-dev.txt`; такой build не является проверкой Windows 7.

Результат:

```text
dist\RD4\RD4.exe
```

## Что включается в bundle

```text
app/templates/**
app/resources/**
alembic.ini
migrations/**
```

Рабочая БД и логи не хранятся рядом с exe:

```text
%APPDATA%\RD4\rd4.db
%APPDATA%\RD4\logs\rd4.log
```

## Первый запуск

Приложение:

```text
1. создаёт каталог %APPDATA%\RD4
2. создаёт logs\rd4.log
3. создаёт rd4.db
4. применяет Alembic migrations
5. создаёт первого admin, если пользователей нет
6. открывает LoginWindow
```

Начальный пользователь:

```text
login: admin
password: admin
```

## Проверка

```text
[ ] RD4.exe стартует двойным кликом
[ ] создаётся %APPDATA%\RD4\rd4.db
[ ] создаётся %APPDATA%\RD4\logs\rd4.log
[ ] открывается окно логина
[ ] работает вход admin/admin
[ ] создаётся договор
[ ] создаются предоплаты
[ ] создаётся справочник услуг
[ ] создаётся акт
[ ] генерируются DOCX-файлы
[ ] приложение перезапускается без потери данных
```
