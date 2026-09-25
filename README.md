# Resume Classifier

MLOps-система классификации резюме соискателей по профессиональным направлениям.

Текущий этап — каркас асинхронного веб-сервиса: служебные эндпоинты, тесты, Docker-образ,
pre-commit, CI и CD с публикацией версионированного образа в Docker Hub.

## Стек

- Python 3.13, [uv](https://docs.astral.sh/uv/) — менеджер пакетов и проекта
- FastAPI + uvicorn — асинхронный веб-фреймворк и сервер
- PostgreSQL 17 + asyncpg — БД и асинхронный драйвер
- pydantic-settings — конфигурация из переменных окружения
- structlog — структурированные JSON-логи
- ruff, pytest, pytest-asyncio, pytest-cov, pre-commit — разработка и проверки

Зависимости разделены на группы в `pyproject.toml`:

| Группа | Назначение | Где ставится |
|---|---|---|
| `web` | то, что нужно приложению в рантайме | локально и в Docker-образе |
| `dev` | линтер, тесты, pre-commit | только локально и в CI |

## Структура

```
src/resume_classifier/
├── __init__.py        версия приложения из метаданных пакета
├── __main__.py        точка входа: настройка логов и запуск uvicorn
├── main.py            создание FastAPI-приложения, lifespan (пул БД)
├── config.py          настройки из переменных окружения
├── db.py              пул подключений asyncpg, запрос версии PostgreSQL
├── checks.py          проверки компонентов с таймаутом и замером времени
├── logs.py            настройка structlog, middleware логирования запросов
├── schemas.py         модели ответов
└── api/
    ├── healthz.py     GET /healthz
    └── v1/
        ├── version.py GET /api/v1/version
        └── health.py  GET /api/v1/health
tests/                 тесты эндпоинтов, проверок, логирования и точки входа
scripts/
├── test.sh            поднять БД и запустить тесты с покрытием
└── smoke.sh           поднять весь стек в Docker и проверить, что он работает
```

## Быстрый старт (Docker Compose)

```bash
cp .env.example .env
docker compose up -d --build
curl localhost:8000/api/v1/health
```

Поднимаются два сервиса: `app` и `db`. У обоих есть healthcheck
(у `app` — `HEALTHCHECK` из Dockerfile), приложение стартует только после того, как БД стала
healthy. Данные БД хранятся в volume `pgdata`, сервисы общаются в сети `backend`,
для контейнеров заданы лимиты CPU/памяти и ротация логов. Порт БД открыт только на `127.0.0.1`.

## Локальная разработка

```bash
uv sync
uv run pre-commit install
cp .env.example .env
docker compose up -d db
uv run python -m resume_classifier
```

Приложение будет доступно на `http://127.0.0.1:8000`, документация — на `/docs`.

## Тесты

```bash
./scripts/test.sh
```

Скрипт проверяет, что есть `.env`, поднимает PostgreSQL из `docker-compose.yml`, дожидается его
готовности и запускает `pytest`. Аргументы передаются в pytest: `./scripts/test.sh -k health`.
Без скрипта — `docker compose up -d db`, затем `uv run pytest`.

Покрытие считается автоматически, порог — 90% (`fail_under` в `pyproject.toml`).
Проверяются как успешные сценарии, так и ошибки: недоступная БД, таймаут проверки,
логирование и прокидывание `X-Request-ID`.

## Smoke-тест

```bash
./scripts/smoke.sh
```

Тесты проверяют код, smoke-тест — что собранный продукт запускается и отвечает. Скрипт
собирает образ, поднимает весь стек `docker compose` под отдельным именем проекта (не мешает
основному), дожидается healthy-статуса и проверяет:

- контейнер приложения запущен не от root;
- `/healthz`, `/api/v1/version` (версия совпадает с `pyproject.toml`) и `/api/v1/health` отвечают 200;
- после остановки БД `/healthz` по-прежнему отвечает 200, а `/api/v1/health` — 503.

При ошибке выводит `FAIL` с причиной и логи контейнеров, завершается с кодом 1. В конце всегда
удаляет свои контейнеры и volume. Тот же скрипт запускается в CI.

## Эндпоинты

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/healthz` | liveness: процесс жив и отвечает, БД не трогает |
| GET | `/api/v1/version` | версия приложения |
| GET | `/api/v1/health` | end-to-end проверка внешних компонентов |

```
GET /api/v1/health
200 {"status": "ok", "components": [{"name": "postgres", "status": "ok", "version": "17.11", "response_time_ms": 21.19}]}
503 {"status": "error", "components": [{"name": "postgres", "status": "error", "version": null, "response_time_ms": 137.53}]}
```

### Почему `/healthz` без `/api/v1`

Это инфраструктурная проверка для Docker/оркестратора, а не часть бизнес-API. Её адрес не должен
меняться при выходе `/api/v2`, и она не зависит от БД: если бы liveness-проба падала вместе с
базой, оркестратор перезапускал бы здоровые контейнеры приложения, не решая проблему.
Состояние внешних зависимостей показывает `/api/v1/health`.

### Откуда берётся версия

`v1` в пути — версия контракта API, а не приложения. Версия приложения записана в одном месте —
`pyproject.toml` — и читается в рантайме через `importlib.metadata`. В Docker-образ пакет
устанавливается в venv (`--no-editable`), поэтому метаданные есть и в контейнере.
CD проверяет, что git-тег `vX.Y.Z` совпадает с версией в `pyproject.toml`, поэтому образ с тегом
`X.Y.Z` всегда отвечает `{"version": "X.Y.Z"}`.

## Конфигурация

| Переменная | По умолчанию | Описание |
|---|---|---|
| `APP_HOST` | `127.0.0.1` (в образе `0.0.0.0`) | адрес, на котором слушает сервер |
| `APP_PORT` | `8000` | порт сервера; в compose — порт на хосте |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_JSON` | `true` | `true` — JSON, `false` — читаемый вывод для разработки |
| `POSTGRES_HOST` | — | хост БД |
| `POSTGRES_PORT` | `5432` | порт БД |
| `POSTGRES_USER` | — | пользователь БД |
| `POSTGRES_PASSWORD` | — | пароль БД |
| `POSTGRES_DB` | — | имя БД |
| `POSTGRES_POOL_MAX_SIZE` | `5` | максимум соединений в пуле |
| `HEALTH_CHECK_TIMEOUT_SECONDS` | `2.0` | таймаут проверки одного компонента |

Настоящие значения хранятся в `.env`, который не попадает в git. В репозитории — только
`.env.example`.

## Логирование

Все логи, включая логи uvicorn, пишутся в stdout в формате JSON. Каждый запрос логируется
событием `request_finished` с полями `method`, `path`, `status_code`, `duration_ms` и
`request_id`. `request_id` берётся из заголовка `X-Request-ID` или генерируется и возвращается
в ответе. Сбои проверок компонентов пишутся как `warning` с именем компонента и ошибкой.

```json
{"method": "GET", "path": "/api/v1/health", "status_code": 200, "duration_ms": 22.6, "event": "request_finished", "request_id": "466cf8410fd94fbe8830bddff8ace23b", "logger": "resume_classifier.logs", "level": "info", "timestamp": "2026-09-25T18:04:36.880144Z"}
```

## Линтер и форматтер

Используется ruff (`[tool.ruff]` в `pyproject.toml`). Выбранные группы правил:

| Правила | Зачем |
|---|---|
| `E`, `W`, `F` | базовые ошибки стиля и pyflakes: неиспользуемые импорты, неопределённые имена |
| `I` | сортировка импортов |
| `N` | соглашения об именовании PEP 8 |
| `UP` | современный синтаксис для Python 3.13 |
| `B` | типичные баги (bugbear) |
| `S` | проверки безопасности (bandit); `assert` разрешён только в тестах |
| `ASYNC` | блокирующие вызовы внутри async-функций — защита event loop |
| `FAST` | правила для FastAPI |
| `SIM`, `C4`, `RET` | упрощение кода, comprehensions, возвраты из функций |
| `PT` | стиль pytest |
| `T20` | запрет `print` — только логирование |
| `RUF` | собственные правила ruff |

## pre-commit

Хуки из `.pre-commit-config.yaml`: ruff (lint с автоисправлением), ruff format, удаление
пробелов в конце строк, перевод строки в конце файла, единые окончания строк, проверка YAML и
TOML, запрет файлов больше 500 КБ (защита от случайного коммита датасета), конфликтов слияния и
приватных ключей, shebang и права на запуск у скриптов, синхронность `uv.lock` с `pyproject.toml`.

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## CI/CD

### CI — `.github/workflows/ci.yml`

Запускается на push в любую ветку, кроме `main`, на pull request в `main` и вызывается из CD.
Три параллельные задачи, каждая падает со своим понятным именем:

- **Lint and format** — `ruff check` (замечания видны прямо в diff PR) и `ruff format --check`
- **Tests and coverage** — pytest с PostgreSQL в сервис-контейнере, порог покрытия 90%,
  отчёт в summary и `coverage.xml` в артефактах
- **Smoke test** — `scripts/smoke.sh`: сборка образа и запуск всего стека `docker compose` с
  проверкой ответов, чтобы сломанный Dockerfile или compose ловился до merge

### CD — `.github/workflows/cd.yml`

Сначала целиком прогоняется CI, и только после его успеха образ собирается и публикуется в
Docker Hub. Образ собирается для двух платформ — `linux/amd64` и `linux/arm64` (Apple Silicon,
ARM-серверы), Docker сам скачивает подходящий вариант.

| Событие | Теги образа |
|---|---|
| push в feature-ветку, PR | ничего не публикуется, только CI |
| push в `main` | `main`, `sha-<commit>` |
| push тега `vX.Y.Z` | `X.Y.Z`, `X.Y`, `latest` |

Почему так:

- релиз — явное действие человека: неизменяемый semver-тег, совпадающий с версией в
  `pyproject.toml` (иначе CD падает);
- образ из `main` даёт свежую сборку для проверки, `sha-<commit>` однозначно связывает образ с
  коммитом;
- из feature-веток и PR ничего не публикуется: реестр не засоряется, непроверенный код не
  попадает в реестр.

Для работы CD в настройках репозитория на GitHub
(Settings → Secrets and variables → Actions) нужно добавить:

- переменную `DOCKERHUB_USERNAME` (вкладка Variables) — логин на Docker Hub;
- секрет `DOCKERHUB_TOKEN` (вкладка Secrets) — access token с правами Read & Write.

### Работа с ветками

Изменения делаются в отдельной ветке и попадают в `main` только через pull request:
push ветки и PR запускают CI, merge в `main` запускает CD.

### Выпуск релиза

Поднять версию в отдельной ветке и влить её в `main` через PR:

```bash
git switch -c release/0.2.0
uv version --bump minor
git commit -am "chore: release 0.2.0"
git push -u origin release/0.2.0
```

После merge поставить тег на `main`:

```bash
git switch main
git pull
git tag v0.2.0
git push origin v0.2.0
```
