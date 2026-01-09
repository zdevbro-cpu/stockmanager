from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: str = "local"
    TZ: str = "Asia/Seoul"

    DATABASE_URL: str

    FIREBASE_PROJECT_ID: str | None = None

    # Upstream keys (optional at API tier; typically used by workers)
    KIS_APP_KEY: str | None = None
    KIS_APP_SECRET: str | None = None
    DART_API_KEY: str | None = None
    ECOS_API_KEY: str | None = None

    GCS_BUCKET: str | None = None
    GOOGLE_API_KEY: str | None = None
    LOG_LEVEL: str = "INFO"


settings = Settings()
