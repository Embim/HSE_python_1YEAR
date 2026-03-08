# URL Shortener — HW3

FastAPI-сервис сокращения ссылок с PostgreSQL, Redis и JWT-авторизацией.

## Запуск

'''bash
cp .env.example .env
docker-compose up --build
'''

Секретный ключ можно создать с помощью 

python -c "import secrets; print(secrets.token_hex(32))"

Сервис будет доступен на 'http://localhost:8000'.
Документация: 'http://localhost:8000/docs'

## Переменные окружения (.env)

| Переменная | Описание | Пример |
|---|---|---|
| 'DATABASE_URL' | Строка подключения к PostgreSQL | 'postgresql+asyncpg://postgres:postgres@db:5432/shortener' |
| 'REDIS_URL' | Строка подключения к Redis | 'redis://redis:6379' |
| 'SECRET_KEY' | Секрет для подписи JWT | 'my-secret' |
| 'ACCESS_TOKEN_EXPIRE_MINUTES' | Время жизни токена (мин) | '60' |

## Таблицы БД

### users
| Поле | Тип | Описание |
|---|---|---|
| id | Integer PK | |
| username | String(50) unique | |
| email | String(100) unique | |
| hashed_password | String | bcrypt-хэш |
| created_at | DateTime | |

### links
| Поле | Тип | Описание |
|---|---|---|
| id | Integer PK | |
| original_url | String | оригинальная ссылка |
| short_code | String(20) unique | 6 символов |
| user_id | Integer FK nullable | NULL для анонимов |
| created_at | DateTime | |
| expires_at | DateTime nullable | TTL |
| last_used_at | DateTime nullable | |
| click_count | Integer | default 0 |
| is_deleted | Boolean | soft delete |

## Эндпоинты

- 'POST /register' — регистрация пользователя
- 'POST /login' — вход, возвращает JWT-токен
- 'POST /links/shorten' — создать короткую ссылку (анонимно или авторизованно)
- 'GET /{short_code}' — редирект на оригинальный URL
- 'GET /links/{short_code}/stats' — статистика по ссылке (клики, даты)
- 'GET /links/search?original_url=...' — найти короткие ссылки по оригинальному URL
- 'PUT /links/{short_code}' — обновить оригинальный URL (только владелец)
- 'DELETE /links/{short_code}' — удалить ссылку (только владелец)

### Дополнительные функции

- 'DELETE /links/cleanup?days=30' — удалить неиспользуемые ссылки старше N дней
- 'GET /links/expired' — список истёкших ссылок
