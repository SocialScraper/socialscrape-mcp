"""Server settings, from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .client import DEFAULT_API_URL


def _flag(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


@dataclass
class Settings:
    api_url: str = DEFAULT_API_URL
    # stdio: the key the process runs with. The hosted server leaves it empty
    # and reads the key from each request instead.
    api_key: str | None = None
    # Ask for trim=true unless the call says otherwise: drops null fields and
    # `extra`, which saves an agent's context.
    trim: bool = True
    # Longest tool answer, in characters (about 25k tokens at the default).
    max_chars: int = 100_000
    timeout: float = 70.0
    # Origins allowed to call the hosted endpoint from a browser; empty means any.
    allowed_origins: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        e = os.environ if env is None else env
        origins = tuple(o.strip() for o in e.get("SOCIALSCRAPE_MCP_ALLOWED_ORIGINS", "").split(",") if o.strip())
        return cls(
            api_url=e.get("SOCIALSCRAPE_API_URL") or DEFAULT_API_URL,
            api_key=e.get("SOCIALSCRAPE_API_KEY") or None,
            trim=_flag(e.get("SOCIALSCRAPE_MCP_TRIM"), True),
            max_chars=int(e.get("SOCIALSCRAPE_MCP_MAX_CHARS") or 100_000),
            timeout=float(e.get("SOCIALSCRAPE_MCP_TIMEOUT") or 70),
            allowed_origins=origins,
        )
