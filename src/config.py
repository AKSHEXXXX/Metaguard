from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    om_host: str
    om_token: str
    om_mcp_url: str
    lineage_max_depth: int = 5
    http_timeout: int = 30
    log_level: str = "INFO"


def _read_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} must be set")
    return value


def load_config() -> AppConfig:
    # Support legacy OM_HOST but prefer OPENMETADATA_HOST.
    host = os.getenv("OPENMETADATA_HOST", "").strip() or os.getenv("OM_HOST", "").strip()
    if not host:
        raise ValueError("OPENMETADATA_HOST must be set")

    token = _read_required("OPENMETADATA_TOKEN")
    mcp_url = _read_required("OPENMETADATA_MCP_URL")

    return AppConfig(
        om_host=host,
        om_token=token,
        om_mcp_url=mcp_url,
        lineage_max_depth=int(os.getenv("LINEAGE_MAX_DEPTH", "5")),
        http_timeout=int(os.getenv("HTTP_TIMEOUT_SECONDS", "30")),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip() or "INFO",
    )
