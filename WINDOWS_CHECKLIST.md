# Windows Build And Test Checklist

## Environment

```text
[ ] Windows 7 VM or Windows 10 VM prepared
[ ] Python 3.8.x installed
[ ] pip upgraded
[ ] Visual C++ runtime available if needed
[ ] Repository copied to VM
[ ] Environment prepared using ENVIRONMENT_SETUP.md
```

## Install

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Expected:

```text
[ ] python --version reports Python 3.8.x
[ ] requirements-dev.txt was not installed into this build venv
```

## Development run

```bat
python -m app.main
```

Expected:

```text
[ ] %APPDATA%\RD4 is created
[ ] %APPDATA%\RD4\rd4.db is created
[ ] %APPDATA%\RD4\logs\rd4.log is created
[ ] Alembic migrations apply
[ ] Login window opens
[ ] admin/admin works
```

## Functional smoke

```text
[ ] create contract
[ ] prepayments are created as payments
[ ] open contract card
[ ] add payment
[ ] add refund
[ ] unpost payment
[ ] create med service folder
[ ] create med service
[ ] create act
[ ] add med service to act
[ ] old act row keeps service snapshot after med service edit
[ ] balance is recalculated correctly
[ ] create user
[ ] reset password
[ ] block/unblock user
[ ] users page is admin-only
```

## DOCX

```text
[ ] paid contract DOCX renders
[ ] FOMS contract DOCX renders
[ ] act ticket DOCX renders
[ ] generated files open in Word/LibreOffice
[ ] Cyrillic text is correct
```

## PyInstaller

```bat
pyinstaller packaging\rd4.spec
```

Expected:

```text
[ ] dist\RD4\RD4.exe exists
[ ] dist\RD4\python38.dll exists
[ ] dist\RD4 contains bundled templates
[ ] dist\RD4 contains migrations
[ ] RD4.exe starts by double click
[ ] RD4.exe starts after reboot
[ ] data persists after app restart
```

## Windows 7-specific

```text
[ ] no missing DLL errors
[ ] Qt platform plugin windows loads
[ ] Visual C++ runtime errors absent
[ ] paths with Cyrillic user profile work
[ ] AppData write permissions work
```

## Missing python38.dll

If Windows reports that `python38.dll` is missing:

```text
[ ] run dist\RD4\RD4.exe from the full dist\RD4 folder
[ ] do not copy only RD4.exe to another folder
[ ] verify python38.dll exists in dist\RD4
[ ] verify python38.dll exists in the base Python 3.8 installation
```

Diagnostic commands:

```bat
dir dist\RD4\python38.dll
where python
python -c "import sys, pathlib; print(sys.executable); print(sys.base_prefix); print((pathlib.Path(sys.base_prefix) / 'python38.dll').exists())"
```
