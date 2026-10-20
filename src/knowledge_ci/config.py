"""Local application configuration; domain contracts belong to T02."""

import shutil
import subprocess
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KNOWLEDGE_CI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: Literal["127.0.0.1", "::1", "localhost"] = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["critical", "error", "warning", "info", "debug"] = "info"
    pilot_repository: Path | None = None
    pilot_commit: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    pilot_language: str | None = Field(default=None, min_length=1)
    pilot_owner: str | None = Field(default=None, min_length=1)
    model_provider: Literal["mock"] = "mock"
    allow_source_egress: bool = False
    model_budget_usd: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator(
        "pilot_repository",
        "pilot_commit",
        "pilot_language",
        "pilot_owner",
        mode="before",
    )
    @classmethod
    def normalize_optional_fields(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @model_validator(mode="after")
    def enforce_t01_model_boundary(self) -> "Settings":
        if self.allow_source_egress or self.model_budget_usd != 0:
            raise ValueError(
                "T01 uses mock responses only; source egress and model spend are disabled"
            )
        return self

    @property
    def pilot_configured(self) -> bool:
        return all(
            (
                self.pilot_repository,
                self.pilot_commit,
                self.pilot_language,
                self.pilot_owner,
            )
        )


def load_settings(env_file: Path | str | None = ".env") -> Settings:
    """Load settings and anchor relative pilot_repository to the configuration file directory."""
    settings = Settings(_env_file=env_file)
    if (
        settings.pilot_repository is not None
        and not settings.pilot_repository.is_absolute()
    ):
        if env_file is None or env_file == ".env":
            anchor = Path.cwd()
        else:
            anchor = Path(env_file).resolve().parent
        settings.pilot_repository = anchor / settings.pilot_repository
    return settings


def verify_pilot(settings: Settings) -> dict[str, str]:
    """Check a configured local Git commit without checkout or executing repository code."""
    required = {
        "PILOT_REPOSITORY": settings.pilot_repository,
        "PILOT_COMMIT": settings.pilot_commit,
        "PILOT_LANGUAGE": settings.pilot_language,
        "PILOT_OWNER": settings.pilot_owner,
    }
    missing = [f"KNOWLEDGE_CI_{name}" for name, value in required.items() if not value]
    if missing:
        raise ValueError("Missing pilot configuration: " + ", ".join(missing))

    git = shutil.which("git")
    if git is None:
        raise ValueError("Git executable was not found on PATH")
    assert settings.pilot_repository is not None
    try:
        repository = settings.pilot_repository.resolve(strict=True)
    except OSError as exc:
        raise ValueError("Pilot repository path is missing or not accessible") from exc
    if not repository.is_dir():
        raise ValueError("Pilot repository must be a directory")

    try:
        root = subprocess.run(
            [git, "-C", str(repository), "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=True,
            timeout=10,
        )
        if Path(root.stdout.decode("utf-8").strip()).resolve() != repository:
            raise ValueError("Pilot repository must point to the Git worktree root")
        result = subprocess.run(
            [
                git,
                "-C",
                str(repository),
                "rev-parse",
                "--verify",
                f"{settings.pilot_commit}^{{commit}}",
            ],
            capture_output=True,
            check=True,
            timeout=10,
        )
        commit = result.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ValueError(
            "Git returned repository metadata with an invalid encoding"
        ) from exc
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError(
            "Pilot path is not a Git repository containing the configured commit"
        ) from exc
    if commit != settings.pilot_commit:
        raise ValueError("Resolved pilot commit differs from the configured commit")
    return {
        "repository": str(repository),
        "commit": commit,
        "language": str(settings.pilot_language),
        "owner": str(settings.pilot_owner),
    }
