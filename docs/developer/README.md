# Документация разработчика

Этот раздел описывает внутреннее устройство RD4 и правила внесения изменений.

## Архитектура

Основное правило зависимостей:

```text
ui -> services -> repositories -> models/core
```

Обратные зависимости запрещены:

```text
repositories -> ui
models -> services
services -> ui
```

Подробности:

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Схема модулей и сигналов](module_signal_diagram.md)
- [HTML-схема взаимодействия модулей](module_interaction.html)
- [Назначение модулей и функций](code_reference_ru.md)

## Окружение

Целевая версия Python для совместимости с Windows 7:

```text
Python 3.8.x
```

Инструкция:

- [ENVIRONMENT_SETUP.md](../../ENVIRONMENT_SETUP.md)

## Проверки

Перед завершением изменений запускаются релевантные проверки:

```bash
.venv/bin/python -m pytest tests
RD4_DATA_DIR=.rd4 .venv/bin/python -m alembic check
RD4_DATA_DIR=.rd4 .venv/bin/python -m app.services.smoke
```

Для UI-only изменений минимум:

```bash
.venv/bin/python -m py_compile <changed-ui-files>
```

## Правило документации

При изменении поведения приложения нужно обновлять документацию:

- пользовательские сценарии — `docs/user/`;
- установка, сборка, база, обслуживание — `docs/admin/`;
- архитектура, зависимости, миграции, структура проекта — `docs/developer/`.

Если временно документация остается в корне проекта, из `docs/` должна быть ссылка на актуальный файл.
