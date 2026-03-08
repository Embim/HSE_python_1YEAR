# URL Shortener — HW4 (Testing)

FastAPI-сервис сокращения ссылок с полным набором тестов: unit, функциональные и нагрузочные.

## Структура тестов

```
tests/
├── conftest.py                          # фикстуры: in-memory SQLite, mock Redis, AsyncClient
├── unit/
│   ├── test_service.py                  # hash_password, create_access_token, increment_click
│   ├── test_schemas.py                  # валидация Pydantic-схем (UserCreate, LinkCreate, ...)
│   ├── test_cache.py                    # cache_get / cache_set / cache_delete
│   ├── test_dependencies.py             # get_current_user, get_optional_user, get_current_user_basic
│   ├── test_router_functions.py         # register, login, valid_link, custom_openapi, get_db
│   └── test_links_router_direct.py      # shorten, redirect, stats, search, delete, update, cleanup
└── functional/
│   ├── test_auth.py                     # /register, /login, /users/me через HTTP
│   └── test_links.py                    # /links/* через HTTP (44 теста)
└── load/
    └── locustfile.py                    # нагрузочное тестирование (Locust)
```

## Запуск тестов

### Требования

```bash
pip install -r requirements.txt
```
### Запуск

```bash
# из папки проекта
pytest --cov=src --cov-report=term-missing --cov-report=html
```

Отчёт HTML будет сгенерирован в папку `htmlcov/`. Открыть:

```bash
# Windows
start htmlcov/index.html

# Linux / macOS
open htmlcov/index.html
```

### Только unit-тесты

```bash
pytest tests/unit/ -v
```

### Только функциональные тесты

```bash
pytest tests/functional/ -v
```

### Нагрузочное тестирование (Locust)

```bash
pip install locust

docker-compose up --build

locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Результаты покрытия

| Модуль | Покрытие |
|---|---|
| `src/auth/constants.py` | 100% |
| `src/auth/config.py` | 100% |
| `src/auth/service.py` | 100% |
| `src/auth/dependencies.py` | 100% |
| `src/auth/router.py` | 100% |
| `src/auth/models.py` | 100% |
| `src/auth/schemas.py` | 100% |
| `src/links/dependencies.py` | 100% |
| `src/links/router.py` | 100% |
| `src/links/models.py` | 100% |
| `src/links/schemas.py` | 100% |
| `src/links/service.py` | 100% |
| `src/cache/client.py` | 100% |
| `src/database.py` | 100% |
| `src/models.py` | 100% |
| `src/config.py` | 100% |
| `src/main.py` | ~85% (lifespan body) |
| **Итого** | **99%** |


## Виды тестирования

| Вид | Файлы | Инструмент |
|---|---|---|
| Модульное (Unit) | `tests/unit/` | `pytest`, `unittest.mock` |
| Функциональное | `tests/functional/` | `pytest`, `httpx.AsyncClient` |
| Нагрузочное (Load) | `tests/load/locustfile.py` | `locust` |

## Запуск сервиса (production)

```bash
cp .env.example .env
docker-compose up --build
```

