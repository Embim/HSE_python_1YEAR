from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models import Base
from logger import log

engine = None
AsyncSessionLocal = None

async def create_pool():
    global engine, AsyncSessionLocal

    log.info("Подключение к PostgreSQL через SQLAlchemy")

    db_url = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

    engine = create_async_engine(
        db_url,
        echo=False,
        pool_size=10,
        max_overflow=20
    )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    log.info("Подключение к БД установлено")

async def close_pool():
    global engine
    if engine:
        await engine.dispose()
        log.info("Подключение к БД закрыто")

def get_session():
    return AsyncSessionLocal()
