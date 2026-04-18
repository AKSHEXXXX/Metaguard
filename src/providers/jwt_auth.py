from __future__ import annotations

import os


class AuthConfigError(RuntimeError):
    """Raised when required auth configuration is missing or invalid."""


class JWTAuthProvider:
    ENV_VAR = "OM_JWT_TOKEN"

    def get_token(self) -> str:
        token = os.getenv(self.ENV_VAR)
        if token is None or not token.strip():
            raise AuthConfigError(f"Missing required environment variable: {self.ENV_VAR}")
        return token

