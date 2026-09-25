# feature/docker-ci — Docker, pre-commit и CI

Часть проекта [Resume Classifier](../../tree/main). Влита в `main` через [PR #2](../../pull/2).

## Что сделано

- **Dockerfile** — двухэтапная сборка: зависимости ставятся отдельным слоем и кешируются, в
  итоговый образ попадает только готовое окружение. Запуск не от root, healthcheck на `/healthz`.
- **docker-compose.yml** — приложение и PostgreSQL 17: volume для данных, общая сеть,
  healthcheck, приложение стартует после готовности БД, порт БД открыт только на `127.0.0.1`,
  лимиты CPU и памяти, ротация логов. Настройки берутся из `.env` (образец — `.env.example`).
- **scripts/test.sh** — поднимает PostgreSQL и запускает тесты с покрытием.
- **scripts/smoke.sh** — собирает образ, поднимает весь стек и проверяет, что сервис работает:
  запуск не от root, ответы всех эндпоинтов, поведение при остановке БД. В конце всё удаляет.
- **pre-commit** — ruff, форматирование, пробелы, конец файла, YAML/TOML, большие файлы,
  приватные ключи, права на запуск скриптов, актуальность `uv.lock`.
- **CI** — GitHub Actions на push в ветки и на pull request в `main`.

## CI

Три параллельные задачи, у каждой понятное имя при падении:

| Задача | Что проверяет |
|---|---|
| Lint and format | `ruff check` и `ruff format --check` |
| Tests and coverage | тесты с PostgreSQL, порог покрытия 90%, отчёт в артефактах |
| Smoke test | `scripts/smoke.sh`: сборка образа и запуск всего стека |

Первый запуск в этой ветке упал на подготовке с понятной ошибкой: была указана несуществующая
версия action `setup-uv`. Исправлено коммитом `ci: fix setup-uv version`.

## Как проверить

```bash
cp .env.example .env
docker compose up -d --build
./scripts/test.sh
./scripts/smoke.sh
uv run pre-commit install
```

Документация API — http://localhost:8000/docs.
