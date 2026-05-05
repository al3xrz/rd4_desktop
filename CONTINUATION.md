# Continuation Notes

This file summarizes where to continue after extracting RD4 Desktop into its own project.

## Completed

- Desktop skeleton
- AppData/data paths
- SQLite engine/session
- SQLite pragmas
- Alembic setup
- ORM models
- Repositories
- Business services
- Login/MainWindow UI skeleton
- Contracts page
- Contract details page
- Payments panel
- Acts panel
- Med services page
- Users page
- DOCX rendering
- PyInstaller spec
- Startup logging and critical error handling

Current automated checks pass:

```text
pytest tests -> passing
alembic check -> no new operations
app.services.smoke -> passing
```

## Important limitations

The work was developed and smoke-tested on Linux/Python 3.12 without PySide2 UI runtime.

The UI code compiles, but the actual windows must be tested on:

```text
Windows VM
Python 3.8.x
PySide2
```

## Next recommended tasks

1. Create a real Windows Python 3.8 environment.
2. Install `requirements.txt`.
3. Launch `python -m app.main`.
4. Manually test the full UI workflow.
5. Fix UI runtime issues found on PySide2.
6. Build with PyInstaller on Windows.
7. Test the build on Windows 7.

## Manual UI smoke scenario

```text
1. Start app
2. Login with admin/admin
3. Open Contracts
4. Create contract with prepayment
5. Open contract card
6. Add payment
7. Add refund
8. Unpost payment
9. Create med service folder
10. Create med service
11. Create act
12. Add med service to act
13. Confirm balance changes
14. Generate paid contract DOCX
15. Generate FOMS contract DOCX
16. Generate act ticket DOCX
17. Create operator/cashier user
18. Verify users page is admin-only
19. Restart app and verify data persists
```

## Known technical notes

- Initial admin is created only when the users table is empty.
- Default admin credentials are intentionally simple for first launch:

```text
admin/admin
```

Change this after installation or implement a first-run password setup.

- `DocxService.open_document()` uses:

```text
Windows: os.startfile
macOS: open
Linux: xdg-open
```

- In PyInstaller bundle, resources are loaded through `_MEIPASS`.

