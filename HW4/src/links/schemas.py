from datetime import UTC, datetime

from pydantic import AnyHttpUrl, Field, field_validator

from src.models import AppModel


class LinkCreate(AppModel):
    original_url: AnyHttpUrl
    custom_alias: str | None = Field(
        default=None, min_length=3, max_length=20, pattern=r"^[A-Za-z0-9_-]+$"
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Срок действия ссылки в формате UTC. Должен быть в будущем. "
                    "Если не указан — по умолчанию now (UTC) + 1 день.",
        examples=["2026-03-09T12:00:00Z"],
    )

    @field_validator("expires_at")
    @classmethod
    def expires_at_must_be_future(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        aware = v if v.tzinfo is not None else v.replace(tzinfo=UTC)
        if aware <= datetime.now(UTC):
            raise ValueError("expires_at must be in the future")
        return v


class LinkUpdate(AppModel):
    original_url: AnyHttpUrl


class LinkOut(AppModel):
    id: int
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: datetime | None
    click_count: int
    last_used_at: datetime | None


class LinkStats(AppModel):
    original_url: str
    short_code: str
    created_at: datetime
    click_count: int
    last_used_at: datetime | None
    expires_at: datetime | None
