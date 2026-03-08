import json
import pytest
from datetime import datetime, timedelta, UTC
from httpx import AsyncClient


async def register_and_login(
    client: AsyncClient,
    username: str = "alice",
    email: str = "alice@example.com",
    password: str = "password123",
) -> dict:
    await client.post(
        "/register",
        json={"username": username, "email": email, "password": password},
    )
    resp = await client.post(
        "/login",
        data={"username": username, "password": password},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def create_link(
    client: AsyncClient,
    url: str = "https://example.com",
    alias: str | None = None,
    expires_at: str | None = None,
    headers: dict | None = None,
):
    body: dict = {"original_url": url}
    if alias:
        body["custom_alias"] = alias
    if expires_at:
        body["expires_at"] = expires_at
    return await client.post("/links/shorten", json=body, headers=headers or {})


async def test_shorten_anonymous(client):
    resp = await create_link(client)
    assert resp.status_code == 201
    data = resp.json()
    assert "short_code" in data
    assert len(data["short_code"]) == 6
    assert data.get("user_id") is None or "user_id" not in data


async def test_shorten_authenticated(client):
    headers = await register_and_login(client)
    resp = await create_link(client, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "short_code" in data
    assert "id" in data


async def test_shorten_custom_alias(client):
    resp = await create_link(client, alias="myalias")
    assert resp.status_code == 201
    assert resp.json()["short_code"] == "myalias"


async def test_shorten_duplicate_alias(client):
    await create_link(client, alias="dupalias")
    resp = await create_link(client, alias="dupalias")
    assert resp.status_code == 400
    assert "Alias already in use" in resp.json()["detail"]


async def test_shorten_invalid_url(client):
    resp = await create_link(client, url="not-a-url")
    assert resp.status_code == 422


async def test_shorten_with_expires_at(client):
    future = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    resp = await create_link(client, expires_at=future)
    assert resp.status_code == 201
    assert resp.json()["expires_at"] is not None


async def test_shorten_returns_link_out_fields(client):
    resp = await create_link(client)
    assert resp.status_code == 201
    data = resp.json()
    for field in ("id", "original_url", "short_code", "created_at", "click_count"):
        assert field in data


async def test_shorten_ftp_url_rejected(client):
    resp = await create_link(client, url="ftp://example.com")
    assert resp.status_code == 422


async def test_redirect_success(client):
    resp = await create_link(client, url="https://example.com/target")
    short_code = resp.json()["short_code"]

    redirect_resp = await client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_resp.status_code == 302
    assert "example.com" in redirect_resp.headers["location"]


async def test_redirect_not_found(client):
    resp = await client.get("/nonexistent", follow_redirects=False)
    assert resp.status_code == 404


async def test_redirect_deleted_link(client):
    headers = await register_and_login(client)
    resp = await create_link(client, headers=headers)
    short_code = resp.json()["short_code"]

    await client.delete(f"/links/{short_code}", headers=headers)
    redirect_resp = await client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_resp.status_code == 404


async def test_redirect_expired_link(client, db_session):
    from src.links.models import Link
    past = datetime.now(UTC) - timedelta(days=1)
    link = Link(
        original_url="https://example.com/expired",
        short_code="expiredtest",
        expires_at=past,
    )
    db_session.add(link)
    await db_session.commit()

    redirect_resp = await client.get("/expiredtest", follow_redirects=False)
    assert redirect_resp.status_code == 410


async def test_redirect_cache_hit(client, cache):
    resp = await create_link(client, url="https://example.com/cached")
    short_code = resp.json()["short_code"]

    cache[f"link:{short_code}"] = "https://cached-url.example.com"

    redirect_resp = await client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_resp.status_code == 302
    assert "cached-url.example.com" in redirect_resp.headers["location"]


async def test_redirect_clears_cache_on_expired(client, cache):
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    resp = await create_link(client, expires_at=past)
    short_code = resp.json()["short_code"]

    cache[f"link:{short_code}"] = "https://example.com/old"

    redirect_resp = await client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_resp.status_code == 410
    assert f"link:{short_code}" not in cache


async def test_redirect_increments_click_count(client):
    resp = await create_link(client, url="https://example.com")
    short_code = resp.json()["short_code"]
    original_count = resp.json()["click_count"]

    await client.get(f"/{short_code}", follow_redirects=False)

    stats_resp = await client.get(f"/links/{short_code}/stats")
    assert stats_resp.json()["click_count"] >= original_count


async def test_stats_success(client):
    resp = await create_link(client, url="https://example.com/stats-test")
    short_code = resp.json()["short_code"]

    stats_resp = await client.get(f"/links/{short_code}/stats")
    assert stats_resp.status_code == 200
    data = stats_resp.json()
    for field in ("original_url", "short_code", "created_at", "click_count"):
        assert field in data
    assert data["short_code"] == short_code


async def test_stats_not_found(client):
    resp = await client.get("/links/doesnotexist/stats")
    assert resp.status_code == 404


async def test_stats_cache_hit(client, cache):
    resp = await create_link(client, url="https://example.com/cache-stats")
    short_code = resp.json()["short_code"]

    resp1 = await client.get(f"/links/{short_code}/stats")
    assert resp1.status_code == 200

    assert f"stats:{short_code}" in cache

    resp2 = await client.get(f"/links/{short_code}/stats")
    assert resp2.status_code == 200
    assert resp1.json()["short_code"] == resp2.json()["short_code"]


async def test_stats_returns_correct_url(client):
    resp = await create_link(client, url="https://specific-url.com/path")
    short_code = resp.json()["short_code"]

    stats_resp = await client.get(f"/links/{short_code}/stats")
    assert "specific-url.com" in stats_resp.json()["original_url"]


async def test_delete_owner(client):
    headers = await register_and_login(client)
    resp = await create_link(client, headers=headers)
    short_code = resp.json()["short_code"]

    del_resp = await client.delete(f"/links/{short_code}", headers=headers)
    assert del_resp.status_code == 204


async def test_delete_not_owner(client):
    alice_headers = await register_and_login(client, username="alice", email="alice@example.com")
    bob_headers = await register_and_login(
        client, username="bob", email="bob@example.com"
    )

    resp = await create_link(client, headers=alice_headers)
    short_code = resp.json()["short_code"]

    del_resp = await client.delete(f"/links/{short_code}", headers=bob_headers)
    assert del_resp.status_code == 403


async def test_delete_not_found(client):
    headers = await register_and_login(client)
    resp = await client.delete("/links/doesnotexist", headers=headers)
    assert resp.status_code == 404


async def test_delete_requires_auth(client):
    resp = await create_link(client)
    short_code = resp.json()["short_code"]

    del_resp = await client.delete(f"/links/{short_code}")
    assert del_resp.status_code == 401


async def test_delete_invalidates_cache(client, cache):
    headers = await register_and_login(client)
    resp = await create_link(client, headers=headers)
    short_code = resp.json()["short_code"]

    cache[f"link:{short_code}"] = "https://example.com"
    cache[f"stats:{short_code}"] = json.dumps({"short_code": short_code})

    await client.delete(f"/links/{short_code}", headers=headers)

    assert f"link:{short_code}" not in cache
    assert f"stats:{short_code}" not in cache


async def test_update_owner(client):
    headers = await register_and_login(client)
    resp = await create_link(client, url="https://old-url.com", headers=headers)
    short_code = resp.json()["short_code"]

    update_resp = await client.put(
        f"/links/{short_code}",
        json={"original_url": "https://new-url.com"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert "new-url.com" in update_resp.json()["original_url"]


async def test_update_not_owner(client):
    alice_headers = await register_and_login(client, username="alice", email="alice@example.com")
    bob_headers = await register_and_login(
        client, username="bob", email="bob@example.com"
    )

    resp = await create_link(client, headers=alice_headers)
    short_code = resp.json()["short_code"]

    update_resp = await client.put(
        f"/links/{short_code}",
        json={"original_url": "https://new-url.com"},
        headers=bob_headers,
    )
    assert update_resp.status_code == 403


async def test_update_not_found(client):
    headers = await register_and_login(client)
    resp = await client.put(
        "/links/doesnotexist",
        json={"original_url": "https://new-url.com"},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_update_requires_auth(client):
    resp = await create_link(client)
    short_code = resp.json()["short_code"]

    update_resp = await client.put(
        f"/links/{short_code}",
        json={"original_url": "https://new-url.com"},
    )
    assert update_resp.status_code == 401


async def test_update_invalidates_cache(client, cache):
    headers = await register_and_login(client)
    resp = await create_link(client, url="https://original.com", headers=headers)
    short_code = resp.json()["short_code"]

    cache[f"link:{short_code}"] = "https://original.com"
    cache[f"stats:{short_code}"] = json.dumps({"short_code": short_code})

    await client.put(
        f"/links/{short_code}",
        json={"original_url": "https://updated.com"},
        headers=headers,
    )

    assert f"link:{short_code}" not in cache
    assert f"stats:{short_code}" not in cache


async def test_update_with_invalid_url(client):
    headers = await register_and_login(client)
    resp = await create_link(client, headers=headers)
    short_code = resp.json()["short_code"]

    update_resp = await client.put(
        f"/links/{short_code}",
        json={"original_url": "not-a-valid-url"},
        headers=headers,
    )
    assert update_resp.status_code == 422


async def test_search_returns_active_links(client):
    url = "https://example.com/search-test"
    await create_link(client, url=url)
    await create_link(client, url=url, alias="second1")

    resp = await client.get("/links/search", params={"original_url": url})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


async def test_search_excludes_deleted(client):
    headers = await register_and_login(client)
    url = "https://example.com/deleted-search"
    resp = await create_link(client, url=url, headers=headers)
    short_code = resp.json()["short_code"]

    await client.delete(f"/links/{short_code}", headers=headers)

    search_resp = await client.get("/links/search", params={"original_url": url})
    assert search_resp.status_code == 200
    assert len(search_resp.json()) == 0


async def test_search_excludes_expired(client):
    url = "https://example.com/expired-search"
    past = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    future = (datetime.now(UTC) + timedelta(days=7)).isoformat()

    await create_link(client, url=url, alias="active1", expires_at=future)
    await create_link(client, url=url, alias="expired1", expires_at=past)

    search_resp = await client.get("/links/search", params={"original_url": url})
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) == 1
    assert results[0]["short_code"] == "active1"


async def test_search_empty(client):
    resp = await client.get(
        "/links/search", params={"original_url": "https://nonexistent.example.com"}
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_search_missing_param(client):
    resp = await client.get("/links/search")
    assert resp.status_code == 422


async def test_expired_links(client):
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    resp = await create_link(client, expires_at=past)
    short_code = resp.json()["short_code"]

    expired_resp = await client.get("/links/expired")
    assert expired_resp.status_code == 200
    codes = [link["short_code"] for link in expired_resp.json()]
    assert short_code in codes


async def test_expired_links_empty(client):
    await create_link(client)

    resp = await client.get("/links/expired")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_expired_links_includes_only_expired(client):
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    future = (datetime.now(UTC) + timedelta(days=7)).isoformat()

    expired_resp = await create_link(client, expires_at=past)
    active_resp = await create_link(client, expires_at=future, alias="activenow")

    resp = await client.get("/links/expired")
    codes = [link["short_code"] for link in resp.json()]

    assert expired_resp.json()["short_code"] in codes
    assert "activenow" not in codes


async def test_cleanup_requires_auth(client):
    resp = await client.delete("/links/cleanup")
    assert resp.status_code == 401


async def test_cleanup_removes_old_unused_links(client, db_session):
    from src.links.models import Link

    old_date = datetime(2020, 1, 1)
    link = Link(original_url="https://old.example.com", short_code="oldone", created_at=old_date)
    db_session.add(link)
    await db_session.commit()

    headers = await register_and_login(client)
    resp = await client.delete("/links/cleanup", params={"days": 30}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1


async def test_cleanup_keeps_recent_links(client):
    headers = await register_and_login(client)

    await create_link(client, url="https://recent.example.com", headers=headers)

    resp = await client.delete("/links/cleanup", params={"days": 30}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0


async def test_cleanup_custom_days_parameter(client, db_session):
    from src.links.models import Link

    ten_days_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=10)
    link = Link(
        original_url="https://old10.example.com",
        short_code="old10d",
        created_at=ten_days_ago,
    )
    db_session.add(link)
    await db_session.commit()

    headers = await register_and_login(client)

    resp = await client.delete("/links/cleanup", params={"days": 5}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1


async def test_cleanup_returns_deleted_count(client):
    headers = await register_and_login(client)
    resp = await client.delete("/links/cleanup", headers=headers)
    assert resp.status_code == 200
    assert "deleted" in resp.json()
    assert isinstance(resp.json()["deleted"], int)


async def test_cleanup_skips_already_deleted_links(client, db_session):
    from src.links.models import Link

    old_date = datetime(2020, 1, 1)
    link = Link(
        original_url="https://already-deleted.example.com",
        short_code="alrdel",
        created_at=old_date,
        is_deleted=True,
    )
    db_session.add(link)
    await db_session.commit()

    headers = await register_and_login(client)
    resp = await client.delete("/links/cleanup", params={"days": 30}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0
