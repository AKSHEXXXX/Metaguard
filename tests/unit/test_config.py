from __future__ import annotations

import pytest

from src.config import load_config


def test_load_config_reads_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENMETADATA_HOST", "https://sandbox.open-metadata.org")
    monkeypatch.setenv("OPENMETADATA_TOKEN", "token")
    monkeypatch.setenv("OPENMETADATA_MCP_URL", "https://sandbox.open-metadata.org/mcp")
    monkeypatch.setenv("LINEAGE_MAX_DEPTH", "7")
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "40")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    cfg = load_config()

    assert cfg.om_host == "https://sandbox.open-metadata.org"
    assert cfg.om_token == "token"
    assert cfg.om_mcp_url == "https://sandbox.open-metadata.org/mcp"
    assert cfg.lineage_max_depth == 7
    assert cfg.http_timeout == 40
    assert cfg.log_level == "DEBUG"


def test_load_config_raises_when_required_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENMETADATA_HOST", raising=False)
    monkeypatch.delenv("OM_HOST", raising=False)
    monkeypatch.delenv("OPENMETADATA_TOKEN", raising=False)
    monkeypatch.delenv("OPENMETADATA_MCP_URL", raising=False)

    with pytest.raises(ValueError):
        load_config()


def test_load_config_supports_legacy_om_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENMETADATA_HOST", raising=False)
    monkeypatch.setenv("OM_HOST", "https://legacy-host")
    monkeypatch.setenv("OPENMETADATA_TOKEN", "token")
    monkeypatch.setenv("OPENMETADATA_MCP_URL", "https://legacy-host/mcp")

    cfg = load_config()
    assert cfg.om_host == "https://legacy-host"
