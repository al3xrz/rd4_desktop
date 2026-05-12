# Windows 7 build guide

Пошаговая инструкция для сборки RD4 desktop под Windows 7/10 через PyInstaller.

## 1. Подготовить машину для сборки

Используйте Windows 7 VM или Windows 10 VM. Для проверки совместимости с Windows 7 лучше собирать и запускать именно в Windows 7 VM.

Установите:

```text
Python 3.8.x
Visual C++ Runtime, если PySide2 или PyInstaller сообщают о missing DLL
Git или архив с исходниками проекта
```

Проверьте Python:

```bat
python --version
```

Ожидаемо:

```text
Python 3.8.x
```

## 2. Создать виртуальное окружение

Из корня проекта:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
```

## 3. Установить зависимости

Для целевой Windows/Python 3.8 сборки используйте только основной файл зависимостей:

```bat
pip install -r requirements.txt
```

Не устанавливайте одновременно `requirements-dev.txt` в это же окружение: там другая версия `pyinstaller`, предназначенная для разработки на более новых системах.

## 4. Проверить запуск из исходников

```bat
python -m app.main
```

При первом запуске приложение должно создать:

```text
%APPDATA%\RD4\rd4.db
%APPDATA%\RD4\logs\rd4.log
```

Начальный пользователь:

```text
login: admin
password: admin
```

## 5. Собрать приложение

```bat
python -m PyInstaller packaging\rd4.spec --noconfirm
```

Результат:

```text
dist\RD4\RD4.exe
```

Это onedir-сборка: рядом с `RD4.exe` лежат библиотеки, ресурсы, миграции и bundled-шаблоны.

## 6. Что попадает в bundle

PyInstaller spec включает:

```text
alembic.ini
migrations\
app\templates\
app\resources\
```

Рабочая база и логи не хранятся рядом с exe. Они создаются в профиле пользователя:

```text
%APPDATA%\RD4\rd4.db
%APPDATA%\RD4\logs\rd4.log
```

## 7. Где держать редактируемые файлы

База уже находится в редактируемом системном каталоге пользователя:

```text
%APPDATA%\RD4\rd4.db
```

Шаблоны в текущей версии читаются из bundle:

```text
dist\RD4\app\templates\docx\
```

Если приложение лежит в `C:\RD4`, эти DOCX можно редактировать через проводник. Если приложение лежит в `C:\Program Files\RD4`, обычный пользователь может не иметь прав на запись.

Самый удобный вариант для эксплуатации: хранить пользовательские шаблоны в `%APPDATA%\RD4\templates\docx\` и при первом запуске копировать туда bundled-шаблоны. Это потребует небольшой доработки `app/services/docx.py` и `app/core/paths.py`.

## 8. Проверить собранный bundle

Запустите:

```bat
dist\RD4\RD4.exe
```

Проверьте:

```text
[ ] открывается окно логина
[ ] работает вход admin/admin
[ ] создаётся договор
[ ] создаётся платёж
[ ] создаётся акт
[ ] справочник услуг открывается
[ ] DOCX-шаблоны генерируют документы
[ ] после перезапуска данные сохраняются
[ ] %APPDATA%\RD4\rd4.db существует
[ ] %APPDATA%\RD4\logs\rd4.log существует
```

## 9. Проверка на Windows 7

На Windows 7 отдельно проверьте:

```text
[ ] нет missing DLL ошибок
[ ] загружается Qt platform plugin windows
[ ] кириллица в путях профиля пользователя работает
[ ] AppData доступен на запись
[ ] DOCX открываются в Word/LibreOffice
```

## 10. Локальная smoke-сборка на Linux

В Linux можно проверить, что `packaging/rd4.spec` собирается, но это не создаёт Windows exe:

```bash
.venv/bin/python -m PyInstaller packaging/rd4.spec --noconfirm
RD4_DATA_DIR=.rd4_bundle_smoke dist/RD4/RD4
```

Для GUI-запуска в Linux может понадобиться доступ к X11/Wayland и Qt platform plugins.
