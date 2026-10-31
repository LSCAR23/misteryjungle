from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalizar_url(url: str) -> str:
    """Render entrega postgresql://; SQLAlchemy necesita el driver psycopg 3."""
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str | None = None
    jwt_secret: str
    jwt_expire_hours: int = 12
    cors_origins: str = "http://localhost:3000"
    seed_mock_data: bool = True

    @field_validator("database_url", "test_database_url")
    @classmethod
    def _normalizar(cls, v: str | None) -> str | None:
        return normalizar_url(v) if v else v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
