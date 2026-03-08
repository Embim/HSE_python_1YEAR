import pytest
from httpx import AsyncClient


async def register(
    client: AsyncClient,
    username: str = "alice",
    email: str = "alice@example.com",
    password: str = "password123",
):
    return await client.post(
        "/register",
        json={"username": username, "email": email, "password": password},
    )


async def login(
    client: AsyncClient,
    username: str = "alice",
    password: str = "password123",
):
    return await client.post(
        "/login",
        data={"username": username, "password": password},
    )


async def get_token(
    client: AsyncClient,
    username: str = "alice",
    password: str = "password123",
) -> str:
    resp = await login(client, username, password)
    return resp.json()["access_token"]


async def test_register_success(client):
    resp = await register(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data
    assert "password" not in data


async def test_register_duplicate_username(client):
    await register(client)
    resp = await register(client, email="other@example.com")
    assert resp.status_code == 400
    assert "Username already taken" in resp.json()["detail"]


async def test_register_duplicate_email(client):
    await register(client)
    resp = await register(client, username="bob")
    assert resp.status_code == 400
    assert "Email already registered" in resp.json()["detail"]


async def test_register_invalid_email(client):
    resp = await register(client, email="not-an-email")
    assert resp.status_code == 422


async def test_register_password_too_short(client):
    resp = await register(client, password="short")
    assert resp.status_code == 422


async def test_register_username_too_short(client):
    resp = await register(client, username="ab")
    assert resp.status_code == 422


async def test_register_username_with_spaces(client):
    resp = await register(client, username="alice bob")
    assert resp.status_code == 422


async def test_login_success(client):
    await register(client)
    resp = await login(client)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


async def test_login_wrong_password(client):
    await register(client)
    resp = await login(client, password="wrongpassword")
    assert resp.status_code == 401


async def test_login_nonexistent_user(client):
    resp = await login(client, username="ghost", password="doesntmatter123")
    assert resp.status_code == 401


async def test_login_returns_bearer_token_type(client):
    await register(client)
    resp = await login(client)
    assert resp.json()["token_type"] == "bearer"


async def test_users_me_success(client):
    await register(client)
    resp = await client.get("/users/me", auth=("alice", "password123"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "hashed_password" not in data


async def test_users_me_wrong_password(client):
    await register(client)
    resp = await client.get("/users/me", auth=("alice", "wrongpass"))
    assert resp.status_code == 401


async def test_users_me_nonexistent_user(client):
    resp = await client.get("/users/me", auth=("ghost", "password123"))
    assert resp.status_code == 401


async def test_users_me_no_credentials(client):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


async def test_get_current_user_invalid_token(client):
    resp = await client.delete(
        "/links/cleanup",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401


async def test_get_current_user_no_token(client):
    resp = await client.delete("/links/cleanup")
    assert resp.status_code == 401


async def test_get_current_user_malformed_bearer(client):
    resp = await client.delete(
        "/links/cleanup",
        headers={"Authorization": "NotBearer sometoken"},
    )
    assert resp.status_code == 401


async def test_get_current_user_expired_token(client):
    from datetime import timedelta
    from unittest.mock import patch

    with patch("src.auth.service.timedelta", return_value=timedelta(minutes=-1)):
        await register(client)
        token_resp = await login(client)

    from jose import jwt
    from src.auth.config import auth_settings
    from src.auth.constants import ALGORITHM
    from datetime import datetime

    payload = {"sub": "1", "exp": datetime(2000, 1, 1).timestamp()}
    expired_token = jwt.encode(payload, auth_settings.SECRET_KEY, algorithm=ALGORITHM)

    resp = await client.delete(
        "/links/cleanup",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401


async def test_register_returns_user_out_fields(client):
    resp = await register(client)
    assert resp.status_code == 201
    data = resp.json()
    expected_fields = {"id", "username", "email", "created_at"}
    assert expected_fields.issubset(data.keys())
