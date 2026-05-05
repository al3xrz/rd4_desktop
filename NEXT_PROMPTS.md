# Suggested Next Prompts

Use these after switching Codex to the standalone `rd4_desktop` project.

## Prompt 1: UI runtime check

```text
Запусти desktop-приложение в этом отдельном проекте. Если PySide2 доступен, проверь UI вручную насколько возможно. Если запуск падает, исправь runtime ошибки PySide2, не меняя архитектуру слоёв.
```

## Prompt 2: first-run hardening

```text
Сделай безопасный first-run flow: если создан начальный admin/admin, после первого входа предложи сменить пароль или добавь явное предупреждение в UI. Сохрани текущую архитектуру services/ui.
```

## Prompt 3: UI polish

```text
Пройди по PySide2 UI и улучши удобство: размеры колонок, сообщения ошибок, обязательные поля, обновление summary после операций, запрет пустых сохранений. Не добавляй новый стек.
```

## Prompt 4: Windows packaging

```text
Проверь PyInstaller packaging на Windows/Python 3.8. Исправь spec, hiddenimports, templates/migrations paths и Qt plugin issues. После сборки обнови packaging/README.md фактическими шагами.
```

## Prompt 5: migration from old web DB

```text
Подготовь план импорта данных из старой PostgreSQL/FastAPI версии в SQLite desktop. Сначала только анализ схем и mapping, без реализации импорта.
```

