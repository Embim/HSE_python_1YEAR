import pytest
from datetime import datetime, UTC
from pydantic import ValidationError, AnyHttpUrl

from src.auth.schemas import UserCreate
from src.links.schemas import LinkCreate, LinkUpdate


class TestUserCreateValidation:
    def test_valid_user(self):
        user = UserCreate(username="alice_99", email="alice@example.com", password="securepass")
        assert user.username == "alice_99"
        assert user.email == "alice@example.com"
        assert user.password == "securepass"

    def test_username_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="ab", email="a@example.com", password="password1")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    def test_username_too_long(self):
        long_name = "a" * 51
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username=long_name, email="a@example.com", password="password1")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    def test_username_with_spaces_pattern_violation(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="alice bob", email="a@example.com", password="password1")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    def test_username_with_special_chars_pattern_violation(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="alice@bob", email="a@example.com", password="password1")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    def test_invalid_email_format(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="alice", email="not-an-email", password="password1")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_password_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="alice", email="alice@example.com", password="short")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_password_exactly_8_chars_valid(self):
        user = UserCreate(username="alice", email="alice@example.com", password="12345678")
        assert user.password == "12345678"

    def test_username_exactly_3_chars_valid(self):
        user = UserCreate(username="ali", email="ali@example.com", password="password1")
        assert user.username == "ali"

    def test_username_with_numbers_valid(self):
        user = UserCreate(username="user123", email="u@example.com", password="password1")
        assert user.username == "user123"

    def test_username_with_underscore_valid(self):
        user = UserCreate(username="user_name", email="u@example.com", password="password1")
        assert user.username == "user_name"


class TestLinkCreateValidation:
    def test_valid_link_https(self):
        link = LinkCreate(original_url="https://example.com")
        assert "example.com" in str(link.original_url)

    def test_valid_link_http(self):
        link = LinkCreate(original_url="http://example.com/path")
        assert "example.com" in str(link.original_url)

    def test_invalid_url_no_scheme(self):
        with pytest.raises(ValidationError) as exc_info:
            LinkCreate(original_url="not-a-url")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("original_url",) for e in errors)

    def test_invalid_url_ftp_scheme(self):
        with pytest.raises(ValidationError) as exc_info:
            LinkCreate(original_url="ftp://example.com")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("original_url",) for e in errors)

    def test_custom_alias_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            LinkCreate(original_url="https://example.com", custom_alias="ab")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("custom_alias",) for e in errors)

    def test_custom_alias_too_long(self):
        with pytest.raises(ValidationError) as exc_info:
            LinkCreate(original_url="https://example.com", custom_alias="a" * 21)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("custom_alias",) for e in errors)

    def test_custom_alias_with_spaces_pattern_violation(self):
        with pytest.raises(ValidationError) as exc_info:
            LinkCreate(original_url="https://example.com", custom_alias="my alias")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("custom_alias",) for e in errors)

    def test_custom_alias_valid(self):
        link = LinkCreate(original_url="https://example.com", custom_alias="my-alias")
        assert link.custom_alias == "my-alias"

    def test_custom_alias_with_underscore_valid(self):
        link = LinkCreate(original_url="https://example.com", custom_alias="my_alias")
        assert link.custom_alias == "my_alias"

    def test_custom_alias_exactly_3_chars_valid(self):
        link = LinkCreate(original_url="https://example.com", custom_alias="abc")
        assert link.custom_alias == "abc"

    def test_custom_alias_exactly_20_chars_valid(self):
        alias = "a" * 20
        link = LinkCreate(original_url="https://example.com", custom_alias=alias)
        assert link.custom_alias == alias

    def test_expires_at_can_be_none(self):
        link = LinkCreate(original_url="https://example.com", expires_at=None)
        assert link.expires_at is None

    def test_expires_at_can_be_set(self):
        future_dt = datetime(2030, 1, 1, 12, 0, 0)
        link = LinkCreate(original_url="https://example.com", expires_at=future_dt)
        assert link.expires_at == future_dt

    def test_expires_at_in_past_raises(self):
        from pydantic import ValidationError
        from datetime import UTC, timedelta
        past = datetime.now(UTC) - timedelta(hours=1)
        with pytest.raises(ValidationError):
            LinkCreate(original_url="https://example.com", expires_at=past)

    def test_original_url_normalized_trailing_slash(self):
        link = LinkCreate(original_url="https://example.com")
        assert str(link.original_url) == "https://example.com/"

    def test_custom_alias_none_by_default(self):
        link = LinkCreate(original_url="https://example.com")
        assert link.custom_alias is None

    def test_custom_alias_with_special_chars_violation(self):
        with pytest.raises(ValidationError) as exc_info:
            LinkCreate(original_url="https://example.com", custom_alias="my@alias")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("custom_alias",) for e in errors)


class TestLinkUpdateValidation:
    def test_valid_update(self):
        update = LinkUpdate(original_url="https://new-url.com/path")
        assert "new-url.com" in str(update.original_url)

    def test_invalid_url_update(self):
        with pytest.raises(ValidationError) as exc_info:
            LinkUpdate(original_url="not-a-valid-url")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("original_url",) for e in errors)

    def test_update_normalizes_url(self):
        update = LinkUpdate(original_url="https://example.com")
        assert str(update.original_url) == "https://example.com/"

    def test_update_with_path(self):
        update = LinkUpdate(original_url="https://example.com/some/path?q=1")
        assert "example.com" in str(update.original_url)
