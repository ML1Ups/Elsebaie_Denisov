# feature/app — асинхронный веб-сервис

Часть проекта [Resume Classifier](../../tree/main). Влита в `main` через [PR #1](../../pull/1).

## Что сделано

- проект на uv: `pyproject.toml`, `uv.lock`, зависимости в группах `web` (нужны приложению) и
  `dev` (линтер и тесты);
- настроен ruff — линтер и форматтер;
- асинхронное приложение на FastAPI с пулом подключений asyncpg к PostgreSQL;
- три служебных эндпоинта;
- структурированные JSON-логи: у каждого запроса `request_id`, метод, путь, статус и время ответа;
- 16 тестов, покрытие 100% (порог 90%).

## Эндпоинты

| Путь | Что возвращает |
|---|---|
| `GET /healthz` | `{"status": "ok"}` — процесс жив, БД не проверяется |
| `GET /api/v1/version` | версию приложения |
| `GET /api/v1/health` | версию PostgreSQL и время его ответа; 503, если БД недоступна |

**Почему `/healthz` без `/api/v1`.** Это проверка для Docker и оркестратора, а не часть API.
Её адрес не меняется при выходе `/api/v2`, и она не зависит от БД: иначе при падении базы
перезапускались бы здоровые контейнеры приложения.

**Откуда версия.** `v1` в пути — версия API, а не приложения. Версия приложения хранится только
в `pyproject.toml` и читается через `importlib.metadata`, в коде она нигде не записана.

## Структура

```
src/resume_classifier/
├── __main__.py   запуск: настройка логов и uvicorn
├── main.py       создание приложения, пул БД на время работы
├── config.py     настройки из переменных окружения
├── db.py         пул asyncpg, запрос версии PostgreSQL
├── checks.py     проверки компонентов с таймаутом и замером времени
├── logs.py       JSON-логи и логирование запросов
├── schemas.py    модели ответов
└── api/          эндпоинты
```

## Правила ruff

`E W F` базовые ошибки, `I` порядок импортов, `N` имена, `UP` современный синтаксис, `B` типичные
баги, `S` безопасность, `ASYNC` блокировка event loop, `FAST` FastAPI, `SIM C4 RET` упрощения,
`PT` стиль pytest, `T20` запрет `print`, `RUF` правила ruff.

## Как проверить

Тестам нужен PostgreSQL:

```bash
uv sync
docker run -d --name resume-db -p 127.0.0.1:5432:5432 -e POSTGRES_USER=resume -e POSTGRES_PASSWORD=resume -e POSTGRES_DB=resume postgres:17-alpine
POSTGRES_HOST=localhost POSTGRES_USER=resume POSTGRES_PASSWORD=resume POSTGRES_DB=resume uv run pytest
```

В следующей ветке, [`feature/docker-ci`](../../tree/feature/docker-ci), это делается одной
командой `./scripts/test.sh`.
