from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_path: Path = Path("data/solar-sites.sqlite3")
    frontend_path: Path | None = None

    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "::1"]
    allowed_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    cookie_secure: bool = False
    session_age_seconds: int = Field(default=8 * 60 * 60, ge=60, le=30 * 24 * 60 * 60)
    max_body_bytes: int = Field(default=16_384, ge=1024, le=1_048_576)

    pvgis_loss: float = Field(default=14, ge=0, lt=100, allow_inf_nan=False)
    pvgis_year: int = Field(default=2023, ge=2005, le=2100)
    pvgis_timeout_seconds: float = Field(default=20, ge=1, le=60, allow_inf_nan=False)
    pvgis_concurrency: int = Field(default=8, ge=1, le=32)
    pvgis_angle: float | None = Field(default=None, ge=0, le=90, allow_inf_nan=False)
    pvgis_aspect: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    pvgis_optimalangles: Literal[0, 1] | None = None
    pvgis_raddatabase: Literal["PVGIS-SARAH3", "PVGIS-ERA5"] | None = None
    pvgis_pvtechchoice: Literal["crystSi", "crystSi2025", "CIS", "CdTe", "Unknown"] | None = None
    pvgis_mountingplace: Literal["free", "building"] | None = None

    @field_validator("allowed_origins")
    @classmethod
    def origins_are_exact(cls, origins: list[str]) -> list[str]:
        if not origins:
            raise ValueError("At least one origin is required")
        for origin in origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.username is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("Origins must be exact HTTP(S) origins without paths")
        return origins

    @field_validator("allowed_hosts")
    @classmethod
    def hosts_are_exact(cls, hosts: list[str]) -> list[str]:
        if not hosts or any(not host or "*" in host or "/" in host for host in hosts):
            raise ValueError("At least one exact host is required")
        return hosts
