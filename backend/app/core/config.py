from functools import cached_property

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://ofertamestre:ofertamestre@db:5432/ofertamestre"
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"

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
        blocked_values = {"change-me-in-production", "test-secret"}
        if value in blocked_values:
            raise ValueError("SECRET_KEY must be changed to a strong random value")
        return value


settings = Settings()
