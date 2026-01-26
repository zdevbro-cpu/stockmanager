from pydantic_settings import BaseSettings, SettingsConfigDict


import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: str = "local"
    TZ: str = "Asia/Seoul"

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_USER and self.DB_PASSWORD and self.DB_HOST:
             return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return os.environ.get("DATABASE_URL", "")

    FIREBASE_PROJECT_ID: str | None = None
    
    # DB Settings (loaded from .env)
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: str | int = 5432
    DB_NAME: str | None = None

    # Upstream keys (optional at API tier; typically used by workers)
    KIS_APP_KEY: str | None = None
    KIS_APP_SECRET: str | None = None
    DART_API_KEY: str | None = None
    ECOS_API_KEY: str | None = None

    GCS_BUCKET: str | None = None
    GOOGLE_API_KEY: str | None = None
    LOG_LEVEL: str = "INFO"


settings = Settings()
