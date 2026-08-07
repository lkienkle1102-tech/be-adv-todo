import os

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ENV = os.getenv("APP_ENV", "dev")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=f".env.{APP_ENV}", extra="ignore")

    app_env: str = APP_ENV
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/adv_todo"
    jwt_secret: str = "change-me"
    jwt_lifetime_seconds: int = 3600

    google_client_id: str = ""
    google_client_secret: str = ""

    frontend_origin: str = "http://localhost:3000"


settings = Settings()
