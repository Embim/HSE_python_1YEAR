import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.auth.models import User
from src.auth.service import hash_password
from src.database import AsyncSessionLocal
from src.links.models import Link

USERS = [
    {"username": "alice", "email": "alice@example.com", "password": "alice123"},
    {"username": "bob", "email": "bob@example.com", "password": "bob123"},
]

LINKS = [
    {
        "owner": "alice",
        "original_url": "https://github.com",
        "short_code": "github",
    },
    {
        "owner": "alice",
        "original_url": "https://fastapi.tiangolo.com",
        "short_code": "fastapi",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
    },
    {
        "owner": "bob",
        "original_url": "https://docs.sqlalchemy.org",
        "short_code": "sqla",
    },
    {
        "owner": "bob",
        "original_url": "https://redis.io",
        "short_code": "redis",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
    },
    {
        "owner": None,
        "original_url": "https://python.org",
        "short_code": "python",
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        user_map: dict[str, User] = {}
        for u in USERS:
            result = await db.execute(select(User).where(User.username == u["username"]))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    username=u["username"],
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                )
                db.add(user)
                await db.flush()
                print(f"[+] user  {u['username']}")
            else:
                print(f"[=] user  {u['username']} already exists")
            user_map[u["username"]] = user

        for l in LINKS:
            result = await db.execute(select(Link).where(Link.short_code == l["short_code"]))
            if result.scalar_one_or_none():
                print(f"[=] link  /{l['short_code']} already exists")
                continue

            owner = user_map.get(l["owner"]) if l["owner"] else None
            link = Link(
                original_url=l["original_url"],
                short_code=l["short_code"],
                user_id=owner.id if owner else None,
                expires_at=l.get("expires_at"),
            )
            db.add(link)
            print(f"[+] link  /{l['short_code']} -> {l['original_url']}")

        await db.commit()
        print("\nDone.")


if __name__ == "__main__":
    asyncio.run(seed())
