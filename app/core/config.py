# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,  # biar JWT_SECRET kebaca untuk field jwt_secret
    )

    app_name: str = Field(default="PPOB Backend", alias="APP_NAME")
    env: str = Field(default="development", alias="ENV")

    database_url: str = Field(default="sqlite:///./app.db", alias="DATABASE_URL")

    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    cors_origins_raw: str = Field(default='["*"]', alias="CORS_ORIGINS")
    admin_api_key: str = Field(default="change-me-admin-key", alias="ADMIN_API_KEY")
    # tambahkan field berikut di class Settings
    enable_jobs: bool = Field(default=True, alias="ENABLE_JOBS")
    
    # Jobs interval (detik)
    job_sync_pricelist_interval_sec: int = Field(default=6 * 60 * 60, alias="JOB_SYNC_PRICELIST_INTERVAL_SEC")  # 6 jam
    job_poll_pending_interval_sec: int = Field(default=60, alias="JOB_POLL_PENDING_INTERVAL_SEC")              # 60 detik
    job_poll_pending_batch_size: int = Field(default=10, alias="JOB_POLL_PENDING_BATCH_SIZE")
    
    # Rate limit (MVP)
    rate_limit_login_per_minute: int = Field(default=10, alias="RATE_LIMIT_LOGIN_PER_MINUTE")
    rate_limit_pin_per_minute: int = Field(default=10, alias="RATE_LIMIT_PIN_PER_MINUTE")

    @property
    def cors_origins(self) -> list[str]:
        # CORS_ORIGINS disimpan sebagai JSON string di env
        try:
            return json.loads(self.cors_origins_raw)
        except Exception:
            return ["*"]


settings = Settings()