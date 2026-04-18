from __future__ import annotations

import pytest

from src.providers.jwt_auth import AuthConfigError, JWTAuthProvider


def test_missing_env_var_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OM_JWT_TOKEN", raising=False)
    provider = JWTAuthProvider()
    with pytest.raises(AuthConfigError):
        provider.get_token()


def test_present_env_var_returns_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OM_JWT_TOKEN", "test.jwt.token")
    provider = JWTAuthProvider()
    assert provider.get_token() == "test.jwt.token"

