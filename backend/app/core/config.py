from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    app_env: str = "development"
    # Empty is the safe default when the UI and API share an origin. Configure
    # explicit origins when they are deployed on separate hosts.
    backend_cors_origins: str = ""
    # Inject in production from approved secret storage. A missing secret keeps
    # privacy endpoints fail-closed instead of accepting unauthenticated access.
    auth_jwt_secret: SecretStr | None = None
    auth_jwt_issuer: str = ""
    auth_jwt_audience: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
