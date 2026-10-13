
# Installs a DoH DNS fallback (see app.core.dns_fallback). Imported here so the
# patch is active before any database connection resolves a hostname.
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import dns_fallback  # noqa: F401


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "FamilyMan API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = ""

    # JWT
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    # Cloudflare R2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = "familyman-media"
    R2_PUBLIC_URL: str = ""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    # FCM
    FCM_PROJECT_ID: str = ""
    FCM_VAPID_PUBLIC_KEY: str = ""
    FCM_VAPID_PRIVATE_KEY: str = ""
    FCM_SERVICE_ACCOUNT_PATH: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Render
    RENDER_API_KEY: str = ""

    # Forex
    FOREX_API_URL: str = "https://open.er-api.com/v6/latest/USD"


settings = Settings()
