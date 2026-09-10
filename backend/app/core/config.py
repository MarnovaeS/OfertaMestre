from functools import cached_property

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"
    mercadolivre_client_id: str | None = None
    mercadolivre_client_secret: str | None = None
    mercadolivre_redirect_uri: str | None = None
    oauth_token_encryption_key: str | None = None
    steam_web_api_key: str | None = None
    steam_web_api_base_url: str = "https://api.steampowered.com"
    steam_store_base_url: str = "https://store.steampowered.com"
    steam_appdetails_enabled: bool = False
    steam_country_code: str = "br"
    steam_price_cache_ttl_seconds: int = Field(default=300, ge=1, le=3600)
    steam_price_cache_max_entries: int = Field(default=1000, ge=1, le=10000)
    amazon_creators_client_id: str | None = None
    amazon_creators_client_secret: str | None = None
    amazon_creators_partner_tag: str | None = None
    amazon_creators_marketplace: str = "www.amazon.com.br"
    amazon_creators_api_base_url: str = "https://creatorsapi.amazon"
    amazon_creators_token_url: str = "https://api.amazon.com/auth/o2/token"
    awin_publisher_id: str | None = None
    awin_api_token: str | None = None
    awin_api_base_url: str = "https://api.awin.com"
    magalu_client_id: str | None = None
    magalu_client_secret: str | None = None
    magalu_redirect_uri: str | None = None

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @computed_field
    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @field_validator("secret_key")
    @classmethod
    def reject_insecure_secret(cls, value: str) -> str:
        blocked_values = {
            "change-me-in-production",
            "test-secret",
            "dev-only-secret-key-change-before-production",
            "replace-with-a-random-secret-of-at-least-32-characters",
        }
        if value in blocked_values:
            raise ValueError("SECRET_KEY must be changed to a strong random value")
        return value


settings = Settings()
