import json
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from src.links.models import Link
from src.links.schemas import LinkCreate, LinkOut, LinkStats, LinkUpdate


def _mock_link(
    short_code: str = "abc123",
    original_url: str = "https://example.com/",
    user_id: int | None = 1,
    is_deleted: bool = False,
    expires_at=None,
    click_count: int = 0,
) -> MagicMock:
    link = MagicMock(spec=Link)
    link.short_code = short_code
    link.original_url = original_url
    link.user_id = user_id
    link.is_deleted = is_deleted
    link.expires_at = expires_at
    link.click_count = click_count
    link.last_used_at = None
    return link


def _mock_db(link=None):
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = link
    result.scalars.return_value.all.return_value = [link] if link else []
    db.execute.return_value = result
    return db


async def test_shorten_custom_alias_success():
    from src.links.router import shorten_link

    db = _mock_db(link=None)
    data = LinkCreate(original_url="https://example.com", custom_alias="mylink")

    link = await shorten_link(data, db, current_user=None)

    db.add.assert_called_once()
    db.commit.assert_awaited_once()


async def test_shorten_custom_alias_duplicate_raises_400():
    from src.links.router import shorten_link

    existing = _mock_link()
    db = _mock_db(link=existing)
    data = LinkCreate(original_url="https://example.com", custom_alias="taken")

    with pytest.raises(HTTPException) as exc:
        await shorten_link(data, db, current_user=None)
    assert exc.value.status_code == 400
    assert "Alias already in use" in exc.value.detail


async def test_shorten_random_code_loop():
    from src.links.router import shorten_link

    existing = _mock_link()
    none_result = MagicMock()
    none_result.scalar_one_or_none.return_value = None

    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = existing

    db = AsyncMock()
    db.execute.side_effect = [existing_result, none_result]

    data = LinkCreate(original_url="https://example.com")
    link = await shorten_link(data, db, current_user=None)
    db.add.assert_called_once()


async def test_shorten_with_authenticated_user():
    from src.links.router import shorten_link

    db = _mock_db(link=None)
    user = MagicMock()
    user.id = 42
    data = LinkCreate(original_url="https://example.com")

    await shorten_link(data, db, current_user=user)

    added_link = db.add.call_args[0][0]
    assert added_link.user_id == 42


async def test_get_link_stats_cache_miss():
    from src.links.router import get_link_stats

    link = _mock_link()

    with (
        patch("src.links.router.cache_get", return_value=None),
        patch("src.links.router.cache_set", new_callable=AsyncMock) as mock_set,
    ):
        stats = await get_link_stats(link)

    assert stats.short_code == link.short_code
    mock_set.assert_awaited_once()


async def test_get_link_stats_cache_hit():
    from src.links.router import get_link_stats

    link = _mock_link()
    cached_data = json.dumps({
        "original_url": "https://example.com/",
        "short_code": "abc123",
        "created_at": datetime.now(UTC).isoformat(),
        "click_count": 5,
        "last_used_at": None,
        "expires_at": None,
    })

    with patch("src.links.router.cache_get", return_value=cached_data):
        stats = await get_link_stats(link)

    assert stats["short_code"] == "abc123"


async def test_search_links_returns_results():
    from src.links.router import search_links

    link = _mock_link()
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [link]
    db.execute.return_value = result

    results = await search_links("https://example.com", db)
    assert len(results) == 1


async def test_search_links_returns_empty():
    from src.links.router import search_links

    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute.return_value = result

    results = await search_links("https://no-match.com", db)
    assert results == []


async def test_get_expired_links_returns_list():
    from src.links.router import get_expired_links

    link = _mock_link(expires_at=datetime.now(UTC) - timedelta(hours=1))
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [link]
    db.execute.return_value = result

    results = await get_expired_links(db)
    assert len(results) == 1


async def test_cleanup_unused_links_deletes():
    from src.links.router import cleanup_unused_links

    link = _mock_link(user_id=1)
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [link]
    db.execute.return_value = result

    user = MagicMock()
    user.id = 1

    with patch("src.links.router.cache_delete", new_callable=AsyncMock):
        response = await cleanup_unused_links(days=30, db=db, current_user=user)

    assert response["deleted"] == 1
    assert link.is_deleted is True
    db.commit.assert_awaited_once()


async def test_cleanup_unused_links_empty():
    from src.links.router import cleanup_unused_links

    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute.return_value = result

    user = MagicMock()
    response = await cleanup_unused_links(days=30, db=db, current_user=user)
    assert response["deleted"] == 0


async def test_delete_link_not_owner_raises_403():
    from src.links.router import delete_link

    link = _mock_link(user_id=1)
    db = AsyncMock()
    user = MagicMock()
    user.id = 2

    with pytest.raises(HTTPException) as exc:
        await delete_link(link=link, db=db, current_user=user)
    assert exc.value.status_code == 403


async def test_delete_link_owner_success():
    from src.links.router import delete_link

    link = _mock_link(user_id=1)
    db = AsyncMock()
    user = MagicMock()
    user.id = 1

    with patch("src.links.router.cache_delete", new_callable=AsyncMock):
        await delete_link(link=link, db=db, current_user=user)

    assert link.is_deleted is True
    db.commit.assert_awaited_once()


async def test_update_link_not_owner_raises_403():
    from src.links.router import update_link

    link = _mock_link(user_id=1)
    db = AsyncMock()
    user = MagicMock()
    user.id = 2

    data = LinkUpdate(original_url="https://new.example.com")
    with pytest.raises(HTTPException) as exc:
        await update_link(data=data, link=link, db=db, current_user=user)
    assert exc.value.status_code == 403


async def test_update_link_owner_success():
    from src.links.router import update_link

    link = _mock_link(user_id=1)
    db = AsyncMock()
    user = MagicMock()
    user.id = 1

    data = LinkUpdate(original_url="https://new.example.com")
    with patch("src.links.router.cache_delete", new_callable=AsyncMock):
        result = await update_link(data=data, link=link, db=db, current_user=user)

    db.commit.assert_awaited_once()
    assert link.original_url == "https://new.example.com/"


async def test_redirect_sets_cache_on_db_hit():
    from src.links.router import redirect
    from fastapi import BackgroundTasks

    link = _mock_link(expires_at=None)
    db = AsyncMock()
    background_tasks = BackgroundTasks()

    with (
        patch("src.links.router.cache_get", return_value=None),
        patch("src.links.router.cache_set", new_callable=AsyncMock) as mock_set,
    ):
        response = await redirect(
            background_tasks=background_tasks, link=link, db=db
        )

    mock_set.assert_awaited_once()
    assert response.status_code == 302
