from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://localhost:5432/railway"
    db_pool_min: int = 5
    db_pool_max: int = 15
    db_pool_max_idle: float = 300.0

    # Auth
    gpt_api_key: str = "change-me-in-production"

    # API
    api_base_url: str = "https://your-app.up.railway.app"
    api_version: str = "3.0.0"
    environment: str = "production"

    # Sentry
    sentry_dsn: str = ""

    # Cache
    cache_ttl_seconds: int = 3600  # 1 hora
    cache_enabled: bool = True

    # Rate Limiting
    rate_limit_global: str = "60/minute"
    rate_limit_game: str = "30/minute"
    rate_limit_admin: str = "5/minute"

    # Logging
    log_level: str = "INFO"
    log_slow_threshold_ms: float = 1000.0

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
