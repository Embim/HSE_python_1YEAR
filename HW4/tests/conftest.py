import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, patch

import src.auth.models  # noqa: F401
import src.links.models  # noqa: F401
from src.database import Base, get_db
from src.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_cache: dict[str, str] = {}


async def _cache_get(key: str) -> str | None:
    return _cache.get(key)


async def _cache_set(key: str, value: str, ttl: int = 3600) -> None:
    _cache[key] = value


async def _cache_delete(key: str) -> None:
    _cache.pop(key, None)


@pytest.fixture
def cache():
    _cache.clear()
    yield _cache
    _cache.clear()


@pytest.fixture
async def engine():
    _engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_session, cache):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("src.cache.client.init_redis", new_callable=AsyncMock),
        patch("src.cache.client.close_redis", new_callable=AsyncMock),
        patch("src.links.router.cache_get", side_effect=_cache_get),
        patch("src.links.router.cache_set", side_effect=_cache_set),
        patch("src.links.router.cache_delete", side_effect=_cache_delete),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()
