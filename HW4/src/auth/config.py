from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"


auth_settings = AuthConfig()
