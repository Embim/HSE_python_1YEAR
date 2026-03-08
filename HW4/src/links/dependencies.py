from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.links.models import Link


async def valid_link(short_code: str, db: AsyncSession = Depends(get_db)) -> Link:
    result = await db.execute(
        select(Link).where(Link.short_code == short_code, Link.is_deleted.is_(False))
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link
