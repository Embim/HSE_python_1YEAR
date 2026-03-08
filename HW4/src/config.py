from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/shortener"
    REDIS_URL: str = "redis://redis:6379"
    LOG_SQL: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
