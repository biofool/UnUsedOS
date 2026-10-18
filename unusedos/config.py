"""Load UnusedOS settings from environment and optional .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list[str]:
    raw = os.environ.get(name, "")
    if not raw.strip():
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class Settings:
    anonymize: bool = False
    anonymize_host: str = "redacted-host"
    anonymize_replacement: str = "/redacted"
    anonymize_segments: list[str] = field(default_factory=list)
    stale_age_days: int = 45
    filesystem: str = "ext4"
    protected_packages: list[str] = field(default_factory=lambda: ["base-files", "coreutils"])

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> Settings:
        if load_dotenv is not None:
            load_dotenv(PACKAGE_ROOT / ".env")
            if env_file:
                load_dotenv(env_file, override=True)
        return cls(
            anonymize=_env_bool("UNUSEDOS_ANONYMIZE", False),
            anonymize_host=os.environ.get("UNUSEDOS_ANONYMIZE_HOST", "redacted-host"),
            anonymize_replacement=os.environ.get("UNUSEDOS_ANONYMIZE_REPLACEMENT", "/redacted"),
            anonymize_segments=_env_list("UNUSEDOS_ANONYMIZE_SEGMENTS"),
            stale_age_days=int(os.environ.get("UNUSEDOS_STALE_AGE_DAYS", "45")),
            filesystem=os.environ.get("UNUSEDOS_FILESYSTEM", "ext4"),
            protected_packages=_env_list("UNUSEDOS_PROTECTED_PACKAGES")
            or ["base-files", "coreutils"],
        )
