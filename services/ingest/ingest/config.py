from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Attempt to find .env in root directory
        env_file=os.path.join(os.path.dirname(__file__), "../../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: str = "local"
    
    # DB
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "Kevin0371_"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "stockmanager"
    
    # KIS
    KIS_API_KEY: str | None = None
    KIS_API_SECRET_KEY: str | None = None
    KIS_BASE_URL: str = "https://openapi.koreainvestment.com:9443"

    # DART
    DART_API_KEY: str | None = None
    
    # ECOS
    ECOS_API_KEY: str | None = "sample"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()
