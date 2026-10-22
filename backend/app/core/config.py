"""Typed, validated runtime configuration.

Precedence (highest first): real environment variables > backend/.env (personal, git-ignored)
> backend/env/<APP_ENV>.env (committed, non-secret defaults per environment). Set ENV_FILE to
point at a different environment file (used by the browser-test backend).

Unsafe combinations are rejected at start-up in production so that a misconfigured deployment
fails loudly instead of running with demo behaviour. Secrets are never committed: production
values come from the deployment's secret store as environment variables.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://school_app:school_app_dev_password@localhost:5432/school_erp"
    log_level: str = "INFO"

    # Sessions & cookies
    session_cookie_name: str = "erp_session"
    csrf_cookie_name: str = "erp_csrf"
    cookie_secure: bool = False
    session_ttl_hours: int = Field(default=8, ge=1, le=24)
    session_idle_minutes: int = Field(default=60, ge=5, le=480)
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Tenant resolution
    default_school_slug: str | None = "demo"
    tenant_fallback_to_default: bool = True
    trust_proxy_headers: bool = True

    # Login protection
    login_window_minutes: int = 15
    login_max_failures_per_identifier: int = 5
    login_max_failures_per_ip: int = 50

    # Credential lifecycle
    enforce_password_change: bool = False
    demo_auth_mode: bool = True
    password_hash_profile: Literal["standard", "fast-test"] = "standard"
    min_password_length: int = 10

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, url: str) -> str:
        # Hosting platforms (e.g. Render) hand out postgres:// or postgresql:// URLs.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url

    @model_validator(mode="after")
    def _production_guards(self) -> "Settings":
        if self.app_env == "production":
            problems = []
            if not self.cookie_secure:
                problems.append("COOKIE_SECURE must be true")
            if self.demo_auth_mode:
                problems.append("DEMO_AUTH_MODE must be false")
            if self.tenant_fallback_to_default:
                problems.append("TENANT_FALLBACK_TO_DEFAULT must be false")
            if not self.enforce_password_change:
                problems.append("ENFORCE_PASSWORD_CHANGE must be true")
            if self.password_hash_profile != "standard":
                problems.append("PASSWORD_HASH_PROFILE must be 'standard'")
            if "school_app_dev_password" in self.database_url:
                problems.append("DATABASE_URL uses the development password")
            if problems:
                raise ValueError("Unsafe production configuration: " + "; ".join(problems))
        return self


BACKEND_DIR = Path(__file__).resolve().parents[2]


def env_files() -> tuple[Path, ...]:
    """Environment files to load, lowest precedence first (missing files are skipped)."""
    app_env = os.environ.get("APP_ENV", "development")
    base = Path(os.environ.get("ENV_FILE") or f"env/{app_env}.env")
    candidates = [p if p.is_absolute() else BACKEND_DIR / p for p in (base, Path(".env"))]
    return tuple(p for p in candidates if p.exists())


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=env_files())  # type: ignore[call-arg]
