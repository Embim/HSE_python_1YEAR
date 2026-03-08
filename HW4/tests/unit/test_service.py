import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from jose import jwt

from src.auth.config import auth_settings
from src.auth.constants import ALGORITHM
from src.auth.service import create_access_token, hash_password, verify_password


def test_hash_password_returns_bcrypt_hash():
    hashed = hash_password("mysecretpassword")
    assert hashed.startswith("$2b$")


def test_hash_password_different_salts():
    password = "samepassword"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2


def test_hash_password_non_empty_output():
    hashed = hash_password("short")
    assert len(hashed) > 20


def test_verify_password_correct():
    password = "correcthorse"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("rightpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_verify_password_empty_vs_nonempty():
    hashed = hash_password("somepassword")
    assert verify_password("", hashed) is False


def test_verify_password_case_sensitive():
    hashed = hash_password("Password")
    assert verify_password("password", hashed) is False


def test_create_access_token_returns_string():
    token = create_access_token({"sub": "42"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_has_sub_claim():
    token = create_access_token({"sub": "99"})
    payload = jwt.decode(token, auth_settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "99"


def test_create_access_token_has_exp_claim():
    token = create_access_token({"sub": "1"})
    payload = jwt.decode(token, auth_settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert "exp" in payload


def test_create_access_token_exp_in_future():
    token = create_access_token({"sub": "1"})
    payload = jwt.decode(token, auth_settings.SECRET_KEY, algorithms=[ALGORITHM])
    now = datetime.now(UTC).timestamp()
    assert payload["exp"] > now


def test_create_access_token_different_data_different_tokens():
    token1 = create_access_token({"sub": "1"})
    token2 = create_access_token({"sub": "2"})
    assert token1 != token2


def test_create_access_token_extra_data_preserved():
    token = create_access_token({"sub": "5", "role": "admin"})
    payload = jwt.decode(token, auth_settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["role"] == "admin"
    assert payload["sub"] == "5"


@pytest.mark.asyncio
async def test_increment_click_increments_count():
    from src.links.service import increment_click
    from src.links.models import Link

    mock_link = MagicMock(spec=Link)
    mock_link.click_count = 3
    mock_link.last_used_at = None

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_link
    mock_db.execute.return_value = mock_result

    await increment_click("abc123", mock_db)

    assert mock_link.click_count == 4
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_increment_click_sets_last_used_at():
    from src.links.service import increment_click
    from src.links.models import Link

    mock_link = MagicMock(spec=Link)
    mock_link.click_count = 0
    mock_link.last_used_at = None

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_link
    mock_db.execute.return_value = mock_result

    before = datetime.now(UTC)
    await increment_click("abc123", mock_db)

    assert mock_link.last_used_at is not None
    assert isinstance(mock_link.last_used_at, datetime)


@pytest.mark.asyncio
async def test_increment_click_calls_commit():
    from src.links.service import increment_click
    from src.links.models import Link

    mock_link = MagicMock(spec=Link)
    mock_link.click_count = 0

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_link
    mock_db.execute.return_value = mock_result

    await increment_click("xyz", mock_db)

    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_increment_click_link_not_found():
    from src.links.service import increment_click

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    await increment_click("notexist", mock_db)

    mock_db.commit.assert_not_awaited()
