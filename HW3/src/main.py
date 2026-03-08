import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi

import src.auth.models
import src.links.models
from src.auth.router import router as auth_router
from src.cache.client import close_redis, init_redis
from src.links.router import router as links_router
from src.logger import api_logger, setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_logger.info("Application startup")
    await init_redis()
    yield
    await close_redis()
    api_logger.info("Application shutdown")


app = FastAPI(
    title="URL Shortener",
    description=(
        "Сервис сокращения ссылок на FastAPI + PostgreSQL + Redis.\n\n"
        "## Авторизация\n"
        "Получите токен через **POST /login**, затем нажмите кнопку **Authorize** (вверху справа) "
        "и вставьте токен в поле 'Bearer'.\n\n"
        "## Кэширование\n"
        "- Редирект 'GET /{short_code}' — кэш в Redis на **1 час**\n"
        "- Статистика 'GET /links/{short_code}/stats' — кэш на **5 минут**\n"
        "- При 'DELETE' / 'PUT' кэш инвалидируется автоматически"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    api_logger.info(
        "%s %s → %s  (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(auth_router)
app.include_router(links_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
