from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.links.models import Link
from src.logger import db_logger


async def increment_click(short_code: str, db: AsyncSession):
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if link:
        link.click_count += 1
        link.last_used_at = datetime.now(UTC)
        await db.commit()
        db_logger.info("DB UPDATE — click_count for %s (total=%d)", short_code, link.click_count)
