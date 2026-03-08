import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials
from jose import jwt
from unittest.mock import AsyncMock, MagicMock

from src.auth.config import auth_settings
from src.auth.constants import ALGORITHM
from src.auth.dependencies import get_current_user, get_current_user_basic, get_optional_user
from src.auth.models import User
from src.auth.service import create_access_token, hash_password


def _mock_db(user=None):
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db.execute.return_value = result
    return db


def _mock_user(user_id: int = 1, username: str = "alice") -> MagicMock:
    user = MagicMock(spec=User)
    user.id = user_id
    user.username = username
    user.hashed_password = hash_password("password123")
    return user


async def test_get_current_user_valid_token():
    user = _mock_user()
    db = _mock_db(user=user)
    token = create_access_token({"sub": "1"})

    result = await get_current_user(token, db)
    assert result is user


async def test_get_current_user_invalid_token_raises_401():
    db = _mock_db()
    with pytest.raises(HTTPException) as exc:
        await get_current_user("totally.invalid.token", db)
    assert exc.value.status_code == 401


async def test_get_current_user_missing_sub_claim_raises_401():
    db = _mock_db()
    token = jwt.encode({"data": "no_sub_here"}, auth_settings.SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token, db)
    assert exc.value.status_code == 401


async def test_get_current_user_user_not_in_db_raises_401():
    db = _mock_db(user=None)
    token = create_access_token({"sub": "999"})
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token, db)
    assert exc.value.status_code == 401


async def test_get_optional_user_no_token_returns_none():
    db = _mock_db()
    result = await get_optional_user(None, db)
    assert result is None


async def test_get_optional_user_invalid_token_returns_none():
    db = _mock_db()
    result = await get_optional_user("bad.token.value", db)
    assert result is None


async def test_get_optional_user_no_sub_returns_none():
    db = _mock_db()
    token = jwt.encode({"data": "x"}, auth_settings.SECRET_KEY, algorithm=ALGORITHM)
    result = await get_optional_user(token, db)
    assert result is None


async def test_get_optional_user_valid_token_returns_user():
    user = _mock_user()
    db = _mock_db(user=user)
    token = create_access_token({"sub": "1"})
    result = await get_optional_user(token, db)
    assert result is user


async def test_get_optional_user_user_not_in_db_returns_none():
    db = _mock_db(user=None)
    token = create_access_token({"sub": "42"})
    result = await get_optional_user(token, db)
    assert result is None


async def test_get_current_user_basic_correct_credentials():
    user = _mock_user()
    db = _mock_db(user=user)
    creds = HTTPBasicCredentials(username="alice", password="password123")

    result = await get_current_user_basic(creds, db)
    assert result is user


async def test_get_current_user_basic_wrong_password_raises_401():
    user = _mock_user()
    db = _mock_db(user=user)
    creds = HTTPBasicCredentials(username="alice", password="wrongpass")

    with pytest.raises(HTTPException) as exc:
        await get_current_user_basic(creds, db)
    assert exc.value.status_code == 401


async def test_get_current_user_basic_user_not_found_raises_401():
    db = _mock_db(user=None)
    creds = HTTPBasicCredentials(username="ghost", password="password123")

    with pytest.raises(HTTPException) as exc:
        await get_current_user_basic(creds, db)
    assert exc.value.status_code == 401


async def test_get_current_user_basic_username_mismatch_raises_401():
    user = _mock_user(username="alice")
    db = _mock_db(user=user)
    creds = HTTPBasicCredentials(username="bob", password="password123")

    with pytest.raises(HTTPException) as exc:
        await get_current_user_basic(creds, db)
    assert exc.value.status_code == 401


async def test_get_current_user_basic_www_authenticate_header():
    db = _mock_db(user=None)
    creds = HTTPBasicCredentials(username="ghost", password="pass1234")

    with pytest.raises(HTTPException) as exc:
        await get_current_user_basic(creds, db)
    assert exc.value.headers["WWW-Authenticate"] == "Basic"
