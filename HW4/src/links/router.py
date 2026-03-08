import json
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, get_optional_user
from src.auth.models import User
from src.cache.client import cache_delete, cache_get, cache_set
from src.database import get_db
from src.links.constants import BEARER_AUTH
from src.links.dependencies import valid_link
from src.links.models import Link
from src.links.schemas import LinkCreate, LinkOut, LinkStats, LinkUpdate
from src.links.service import increment_click
from src.logger import api_logger, db_logger

router = APIRouter(tags=["links"])


@router.post(
    "/links/shorten",
    response_model=LinkOut,
    status_code=status.HTTP_201_CREATED,
    summary="Сократить ссылку",
    description=(
        "Создаёт короткую ссылку для переданного URL."
    ),
)
async def shorten_link(
    data: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    if data.custom_alias:
        result = await db.execute(select(Link).where(Link.short_code == data.custom_alias))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Alias already in use")
        short_code = data.custom_alias
    else:
        while True:
            short_code = secrets.token_urlsafe(4)[:6]
            result = await db.execute(select(Link).where(Link.short_code == short_code))
            if not result.scalar_one_or_none():
                break

    expires_at = data.expires_at if data.expires_at is not None else datetime.now(UTC) + timedelta(days=1)

    link = Link(
        original_url=str(data.original_url),
        short_code=short_code,
        user_id=current_user.id if current_user else None,
        expires_at=expires_at,
    )
    db.add(link)
    db_logger.info(
        "DB INSERT — link: %s → %s (user_id=%s)",
        short_code,
        data.original_url,
        current_user.id if current_user else None,
    )
    await db.commit()
    await db.refresh(link)
    return link


@router.get(
    "/links/search",
    response_model=list[LinkOut],
    summary="Поиск по оригинальному URL",
    description="Возвращает все активные короткие ссылки, созданные для указанного 'original_url'.",
)
async def search_links(
    original_url: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(UTC)
    db_logger.info("DB SELECT — search links by original_url: %s", original_url)
    result = await db.execute(
        select(Link).where(
            Link.original_url == original_url,
            Link.is_deleted.is_(False),
            (Link.expires_at.is_(None)) | (Link.expires_at > now),
        )
    )
    links = result.scalars().all()
    db_logger.info("DB — found %d link(s) for url: %s", len(links), original_url)
    return links


@router.get(
    "/links/expired",
    response_model=list[LinkOut],
    summary="История истёкших ссылок",
    description="Возвращает все ссылки, у которых 'expires_at' меньше текущего времени.",
)
async def get_expired_links(db: AsyncSession = Depends(get_db)):
    now = datetime.now(UTC)
    db_logger.info("DB SELECT — expired links (before %s)", now.isoformat())
    result = await db.execute(
        select(Link).where(Link.expires_at.isnot(None), Link.expires_at < now)
    )
    links = result.scalars().all()
    db_logger.info("DB — found %d expired link(s)", len(links))
    return links


@router.delete(
    "/links/cleanup",
    summary="Очистка неиспользуемых ссылок",
    openapi_extra=BEARER_AUTH,
    description=(
        "Помечает как удалённые ссылки без переходов за последние 'days' дней. "
    ),
)
async def cleanup_unused_links(
    days: int = Query(default=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cutoff = datetime.now(UTC) - timedelta(days=days)
    result = await db.execute(
        select(Link).where(
            Link.is_deleted.is_(False),
            (Link.last_used_at < cutoff) | (Link.last_used_at.is_(None)),
            Link.created_at < cutoff,
        )
    )
    links = result.scalars().all()
    for lnk in links:
        lnk.is_deleted = True
        await cache_delete(f"link:{lnk.short_code}")
        await cache_delete(f"stats:{lnk.short_code}")

    await db.commit()
    db_logger.info("DB UPDATE — soft-deleted %d link(s) (user_id=%s)", len(links), current_user.id)
    return {"deleted": len(links)}


@router.get(
    "/links/{short_code}/stats",
    response_model=LinkStats,
    summary="Статистика по ссылке",
    description=(
        "Возвращает статистику короткой ссылки. "
        "Результат кэшируется в Redis на 5 минут."
    ),
)
async def get_link_stats(link: Link = Depends(valid_link)):
    cached = await cache_get(f"stats:{link.short_code}")
    if cached:
        api_logger.info("CACHE HIT — stats:%s", link.short_code)
        return json.loads(cached)

    api_logger.info("CACHE MISS — stats:%s → fetching from DB", link.short_code)
    stats = LinkStats.model_validate(link)
    await cache_set(f"stats:{link.short_code}", stats.model_dump_json(), ttl=300)
    return stats


@router.delete(
    "/links/{short_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить ссылку",
    openapi_extra=BEARER_AUTH,
    description="Мягко удаляет короткую ссылку. Доступно только владельцу.",
)
async def delete_link(
    link: Link = Depends(valid_link),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if link.user_id != current_user.id:
        db_logger.warning(
            "DB — delete forbidden: short_code=%s user_id=%s (owner=%s)",
            link.short_code,
            current_user.id,
            link.user_id,
        )
        raise HTTPException(status_code=403, detail="Not your link")

    link.is_deleted = True
    await db.commit()
    await cache_delete(f"link:{link.short_code}")
    await cache_delete(f"stats:{link.short_code}")
    db_logger.info("DB UPDATE — soft-deleted link: %s (user_id=%s)", link.short_code, current_user.id)


@router.put(
    "/links/{short_code}",
    response_model=LinkOut,
    summary="Обновить оригинальный URL",
    openapi_extra=BEARER_AUTH,
    description="Меняет оригинальный URL короткой ссылки.",
)
async def update_link(
    data: LinkUpdate,
    link: Link = Depends(valid_link),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if link.user_id != current_user.id:
        db_logger.warning(
            "DB — update forbidden: short_code=%s user_id=%s (owner=%s)",
            link.short_code,
            current_user.id,
            link.user_id,
        )
        raise HTTPException(status_code=403, detail="Not your link")

    link.original_url = str(data.original_url)
    await db.commit()
    await db.refresh(link)
    await cache_delete(f"link:{link.short_code}")
    await cache_delete(f"stats:{link.short_code}")
    db_logger.info("DB UPDATE — link %s → %s (user_id=%s)", link.short_code, link.original_url, current_user.id)
    return link


@router.get(
    "/{short_code}",
    summary="Редирект по короткой ссылке",
    description=(
        "Перенаправляет на оригинальный URL. Не работает в Swagger UI, используйте браузер."
    ),
    response_class=RedirectResponse,
)
async def redirect(
    background_tasks: BackgroundTasks,
    link: Link = Depends(valid_link),
    db: AsyncSession = Depends(get_db),
):
    if link.expires_at and link.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        api_logger.info("CACHE DELETE — expired link: %s", link.short_code)
        await cache_delete(f"link:{link.short_code}")
        raise HTTPException(status_code=410, detail="Link has expired")

    cached_url = await cache_get(f"link:{link.short_code}")
    if cached_url:
        api_logger.info("CACHE HIT — redirect %s → %s", link.short_code, cached_url)
        background_tasks.add_task(increment_click, link.short_code, db)
        return RedirectResponse(url=cached_url, status_code=302)

    api_logger.info("CACHE MISS — redirect %s → fetching from DB", link.short_code)
    link.click_count += 1
    link.last_used_at = datetime.now(UTC)
    db_logger.info("DB UPDATE — click_count for %s (total=%d)", link.short_code, link.click_count)
    await db.commit()

    await cache_set(f"link:{link.short_code}", link.original_url, ttl=3600)
    api_logger.info("CACHE SET — link:%s (ttl=3600)", link.short_code)
    return RedirectResponse(url=link.original_url, status_code=302)
