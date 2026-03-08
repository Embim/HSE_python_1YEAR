import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_cache_get_returns_none_when_redis_none():
    with patch("src.cache.client.redis_client", None):
        from src.cache.client import cache_get
        result = await cache_get("some_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_get_calls_redis_get_and_returns_value():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = "cached_value"

    with patch("src.cache.client.redis_client", mock_redis):
        from src.cache.client import cache_get
        result = await cache_get("my_key")

    mock_redis.get.assert_awaited_once_with("my_key")
    assert result == "cached_value"


@pytest.mark.asyncio
async def test_cache_get_returns_none_for_missing_key():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("src.cache.client.redis_client", mock_redis):
        from src.cache.client import cache_get
        result = await cache_get("nonexistent_key")

    assert result is None


@pytest.mark.asyncio
async def test_cache_set_does_nothing_when_redis_none():
    with patch("src.cache.client.redis_client", None):
        from src.cache.client import cache_set
        await cache_set("key", "value", ttl=60)


@pytest.mark.asyncio
async def test_cache_set_calls_redis_set_with_correct_args():
    mock_redis = AsyncMock()

    with patch("src.cache.client.redis_client", mock_redis):
        from src.cache.client import cache_set
        await cache_set("my_key", "my_value", ttl=120)

    mock_redis.set.assert_awaited_once_with("my_key", "my_value", ex=120)


@pytest.mark.asyncio
async def test_cache_set_uses_default_ttl():
    mock_redis = AsyncMock()

    with patch("src.cache.client.redis_client", mock_redis):
        from src.cache.client import cache_set
        await cache_set("key", "value")

    mock_redis.set.assert_awaited_once_with("key", "value", ex=3600)


@pytest.mark.asyncio
async def test_cache_delete_does_nothing_when_redis_none():
    with patch("src.cache.client.redis_client", None):
        from src.cache.client import cache_delete
        await cache_delete("key")


@pytest.mark.asyncio
async def test_cache_delete_calls_redis_delete():
    mock_redis = AsyncMock()

    with patch("src.cache.client.redis_client", mock_redis):
        from src.cache.client import cache_delete
        await cache_delete("my_key")

    mock_redis.delete.assert_awaited_once_with("my_key")


@pytest.mark.asyncio
async def test_init_redis_creates_client():
    import src.cache.client as cache_module

    mock_redis_instance = MagicMock()
    mock_from_url = MagicMock(return_value=mock_redis_instance)

    original_client = cache_module.redis_client
    try:
        with patch("src.cache.client.aioredis") as mock_aioredis:
            mock_aioredis.from_url = mock_from_url
            await cache_module.init_redis()

        mock_from_url.assert_called_once()
        assert cache_module.redis_client == mock_redis_instance
    finally:
        cache_module.redis_client = original_client


@pytest.mark.asyncio
async def test_close_redis_calls_aclose_on_client():
    import src.cache.client as cache_module

    mock_redis = AsyncMock()
    original_client = cache_module.redis_client
    try:
        cache_module.redis_client = mock_redis
        await cache_module.close_redis()
        mock_redis.aclose.assert_awaited_once()
    finally:
        cache_module.redis_client = original_client


@pytest.mark.asyncio
async def test_close_redis_does_nothing_when_no_client():
    import src.cache.client as cache_module

    original_client = cache_module.redis_client
    try:
        cache_module.redis_client = None
        await cache_module.close_redis()
    finally:
        cache_module.redis_client = original_client
