"""Central configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_name: str = "Prediqo"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "prediqo"
    postgres_user: str = "prediqo"
    postgres_password: str = "change-me"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # "firebase" verifies real Firebase ID tokens. "dev" accepts a single
    # static token and is only honoured when environment == "development".
    auth_mode: str = "firebase"
    firebase_project_id: str = ""
    dev_auth_token: str = "prediqo-dev-token"
    database_url: str | None = None  # override for tests (e.g. in-memory SQLite)

    # --- Sports data provider ---
    football_data_provider: str = "sample"  # "sample" (dev only) or "api-football"
    football_data_api_key: str = ""
    football_data_base_url: str = "https://v3.football.api-sports.io"
    allow_sample_data: bool = True  # must be false outside development

    # --- Google Play Billing ---
    google_play_package_name: str = "com.prediqo.app"
    google_play_service_account_json: str = ""
    token_unlock_cost: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def async_database_url(self) -> str:
        url = self.effective_database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
