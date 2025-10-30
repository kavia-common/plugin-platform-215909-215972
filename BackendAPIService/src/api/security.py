"""
Security dependencies and JWT validation stubs.

For bootstrap, we allow a development token path to simplify initial integration.
This MUST be hardened later with real JWT validation (JWKS, audience/issuer checks).
"""
from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from .config import get_settings


class AuthContext(BaseModel):
    """Represents authenticated user/tenant context extracted from JWT."""
    subject: str
    tenant_id: Optional[str] = None
    scopes: list[str] = []


def _parse_bearer(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    parts = token.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return token


# PUBLIC_INTERFACE
def get_auth_context(
    authorization: Optional[str] = Header(default=None),
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-ID"),
) -> AuthContext:
    """
    Dependency that validates Authorization bearer token and returns AuthContext.

    Bootstrap behavior:
    - If BACKEND_SECURITY__DEV_MODE is True and token equals BACKEND_SECURITY__DEV_JWT,
      accept it and mint a default AuthContext. If X-Tenant-ID header is provided,
      it overrides the default tenant id for scoping (useful for multi-tenant dev/testing).
    - Otherwise, raise 401 (real validation to be implemented later).
    """
    settings = get_settings()
    token = _parse_bearer(authorization)

    if settings.security.dev_mode:
        dev_token = settings.security.dev_jwt
        if token and dev_token and token == dev_token:
            # In dev mode, accept the token and return a stub context with optional tenant override
            tenant = x_tenant_id or "dev-tenant"
            return AuthContext(subject="dev-user", tenant_id=tenant, scopes=["*"])

    # Placeholder for future JWT validation (JWKS verify, claims checks)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )
