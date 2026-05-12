# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


SPEC_PATH = Path(SPECPATH).resolve()
SPEC_DIR = SPEC_PATH.parent if SPEC_PATH.suffix == ".spec" else SPEC_PATH
ROOT = SPEC_DIR.parent

datas = [
    (str(ROOT / "alembic.ini"), "."),
    (str(ROOT / "migrations"), "migrations"),
    (str(ROOT / "app" / "templates"), "app/templates"),
    (str(ROOT / "app" / "resources"), "app/resources"),
]


a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "app.ui.application",
        "app.ui.login_window",
        "app.ui.main_window",
        "app.ui.contracts_page",
        "app.ui.contract_details_page",
        "app.ui.med_services_page",
        "app.ui.users_page",
        "docxtpl",
        "docx",
        "logging.config",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RD4",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RD4",
)
