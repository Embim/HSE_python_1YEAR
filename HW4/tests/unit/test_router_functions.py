import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock

from src.auth.service import hash_password, create_access_token
from src.auth.models import User
from src.auth.schemas import UserCreate


def _make_session(user=None):
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result
    return session


async def test_register_direct_success():
    from src.auth.router import register

    session = AsyncMock()
    none_result = MagicMock()
    none_result.scalar_one_or_none.return_value = None
    session.execute.return_value = none_result

    data = UserCreate(username="newuser", email="new@example.com", password="password123")
    user = await register(data, session)

    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once()


async def test_register_direct_duplicate_username():
    from src.auth.router import register

    existing_user = MagicMock(spec=User)
    session = _make_session(user=existing_user)

    data = UserCreate(username="alice", email="alice@example.com", password="password123")
    with pytest.raises(HTTPException) as exc:
        await register(data, session)
    assert exc.value.status_code == 400
    assert "Username already taken" in exc.value.detail


async def test_register_direct_duplicate_email():
    from src.auth.router import register

    session = AsyncMock()
    none_result = MagicMock()
    none_result.scalar_one_or_none.return_value = None
    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = MagicMock(spec=User)

    session.execute.side_effect = [none_result, existing_result]

    data = UserCreate(username="bob", email="alice@example.com", password="password123")
    with pytest.raises(HTTPException) as exc:
        await register(data, session)
    assert exc.value.status_code == 400
    assert "Email already registered" in exc.value.detail


async def test_login_direct_success():
    from src.auth.router import login

    user = MagicMock(spec=User)
    user.id = 1
    user.hashed_password = hash_password("password123")
    session = _make_session(user=user)

    form_data = MagicMock()
    form_data.username = "alice"
    form_data.password = "password123"

    result = await login(form_data, session)
    assert "access_token" in result
    assert result["token_type"] == "bearer"


async def test_login_direct_wrong_password():
    from src.auth.router import login

    user = MagicMock(spec=User)
    user.id = 1
    user.hashed_password = hash_password("correctpassword")
    session = _make_session(user=user)

    form_data = MagicMock()
    form_data.username = "alice"
    form_data.password = "wrongpassword"

    with pytest.raises(HTTPException) as exc:
        await login(form_data, session)
    assert exc.value.status_code == 401


async def test_login_direct_user_not_found():
    from src.auth.router import login

    session = _make_session(user=None)
    form_data = MagicMock()
    form_data.username = "ghost"
    form_data.password = "anypassword"

    with pytest.raises(HTTPException) as exc:
        await login(form_data, session)
    assert exc.value.status_code == 401


async def test_valid_link_found():
    from src.links.dependencies import valid_link

    link = MagicMock()
    session = _make_session(user=link)

    result = await valid_link("mycode", session)
    assert result is link


async def test_valid_link_not_found_raises_404():
    from src.links.dependencies import valid_link

    session = _make_session(user=None)

    with pytest.raises(HTTPException) as exc:
        await valid_link("noexist", session)
    assert exc.value.status_code == 404
    assert "Link not found" in exc.value.detail


def test_custom_openapi_generates_schema():
    from src.main import app, custom_openapi

    app.openapi_schema = None
    schema = custom_openapi()

    assert schema["info"]["title"] == "URL Shortener"
    assert "BearerAuth" in schema["components"]["securitySchemes"]


def test_custom_openapi_uses_cache():
    from src.main import app, custom_openapi

    app.openapi_schema = None
    schema1 = custom_openapi()
    schema2 = custom_openapi()

    assert schema1 is schema2


async def test_get_db_yields_session():
    from unittest.mock import patch, AsyncMock
    from src.database import get_db

    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.database.AsyncSessionLocal", return_value=mock_ctx):
        gen = get_db()
        session = await gen.__anext__()
        assert session is mock_session
