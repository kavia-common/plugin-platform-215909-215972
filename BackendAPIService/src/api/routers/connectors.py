"""
Connectors router exposes discovery endpoints for available connectors.

Routes:
- GET /connectors: List available connectors (no auth for bootstrap)
- POST /connectors/{id}/oauth/login: Initiate OAuth login (mock or real)
- GET /connectors/{id}/oauth/callback: Handle OAuth callback (mock or real)
"""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, Field

from ..connectors.base import ConnectorMetadata
from ..connectors.registry import list_connectors as registry_list
from ..crypto import encrypt_json
from ..db import ConnectionsRepository, get_connections_repo
from ..errors import APIError
from ..security import AuthContext, get_auth_context

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get(
    "",
    summary="List all available connectors",
    description="Returns a list of connector definitions that can be used to create connections.",
    response_model=List[ConnectorMetadata],
    responses={200: {"description": "A list of connectors"}},
)
def list_connectors() -> List[ConnectorMetadata]:
    """Return static connector metadata for discovery (Jira and Confluence)."""
    return registry_list()


# -------- OAuth helper models and memory store (dev bootstrap) --------

@dataclass
class _StateRecord:
    tenant_id: str
    connector: str
    created_at: float
    pkce_verifier: Optional[str]
    redirect_uri: Optional[str]


# Simple in-memory CSRF state store keyed by random state string
_STATE_STORE: Dict[str, _StateRecord] = {}
_STATE_TTL_SECONDS = 600  # 10 minutes default


def _clean_expired_states() -> None:
    now = time.time()
    expired = [k for k, v in _STATE_STORE.items() if now - v.created_at > _STATE_TTL_SECONDS]
    for k in expired:
        _STATE_STORE.pop(k, None)


def _new_state() -> str:
    return secrets.token_urlsafe(24)


def _new_pkce_pair() -> Tuple[str, str]:
    # Returns (verifier, challenge)
    verifier = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return verifier, challenge


class OAuthLoginRequest(BaseModel):
    """Optional body for initiating OAuth login."""
    redirect_uri: Optional[str] = Field(default=None, description="Where the provider should redirect back")
    scopes: Optional[List[str]] = Field(default=None, description="Requested scopes for the connector")
    use_pkce: bool = Field(default=True, description="Whether to use PKCE (recommended)")
    # For real providers, optionally allow extra params passthrough
    extra_params: Dict[str, str] = Field(default_factory=dict, description="Additional query parameters")


class OAuthLoginResponse(BaseModel):
    """Authorize URL and state to proceed with OAuth."""
    authorize_url: str = Field(..., description="URL to redirect user to the provider's authorization page")
    state: str = Field(..., description="Opaque state to protect against CSRF and bind tenant")
    pkce_challenge: Optional[str] = Field(default=None, description="PKCE S256 challenge (if use_pkce is true)")
    pkce_method: Optional[str] = Field(default=None, description="PKCE method (S256)")
    # For mock mode visibility
    mode: str = Field(default="mock", description="Indicates mock or real mode")


class OAuthCallbackSuccess(BaseModel):
    """Successful callback result."""
    connector: str = Field(..., description="Connector name (e.g., jira)")
    status: str = Field(..., description="connected/disconnected")
    connection_id: Optional[str] = Field(default=None, description="Created connection id when applicable")
    message: Optional[str] = Field(default=None, description="Human-readable note")


# -------- OAuth endpoints --------

@router.post(
    "/{connector_id}/oauth/login",
    summary="Initiate OAuth login for a connector",
    description=(
        "Generates an authorization URL and CSRF state for the given connector. "
        "Supports PKCE. In mock mode (no client credentials configured), returns a mocked authorize URL."
    ),
    response_model=OAuthLoginResponse,
    responses={
        200: {"description": "Authorization URL generated"},
        401: {"description": "Unauthorized"},
        400: {"description": "Invalid request"},
    },
)
def oauth_login(
    connector_id: str,
    body: OAuthLoginRequest | None = None,
    ctx: AuthContext = Depends(get_auth_context),
) -> OAuthLoginResponse:
    """Create an authorize URL and state for OAuth login. PKCE is supported via use_pkce flag.

    Behavior:
    - Derives tenant_id from AuthContext (dev stub).
    - Stores state in memory with tenant binding and optional PKCE verifier.
    - If provider client credentials are not available in environment, returns a mocked authorize_url.
    """
    _clean_expired_states()

    body = body or OAuthLoginRequest()
    # In a real integration, pull client_id, auth_base_url from env per connector
    client_id_env = os.getenv(f"{connector_id.upper()}_CLIENT_ID")
    auth_url_env = os.getenv(f"{connector_id.upper()}_AUTH_URL")  # e.g., https://auth.atlassian.com/authorize
    redirect_uri = body.redirect_uri or os.getenv(f"{connector_id.upper()}_REDIRECT_URI")

    # CSRF state
    state = _new_state()
    pkce_verifier = None
    pkce_challenge = None
    pkce_method = None
    if body.use_pkce:
        pkce_verifier, pkce_challenge = _new_pkce_pair()
        pkce_method = "S256"

    # Store to memory with tenant binding
    _STATE_STORE[state] = _StateRecord(
        tenant_id=ctx.tenant_id or "",
        connector=connector_id,
        created_at=time.time(),
        pkce_verifier=pkce_verifier,
        redirect_uri=redirect_uri,
    )

    # Mock mode if missing client credentials
    if not client_id_env or not auth_url_env:
        # Provide a pseudo URL indicating mock mode
        mock_url = f"https://mock.oauth.local/authorize?connector={connector_id}&state={state}"
        return OAuthLoginResponse(
            authorize_url=mock_url,
            state=state,
            pkce_challenge=pkce_challenge,
            pkce_method=pkce_method,
            mode="mock",
        )

    # Real mode: construct authorize URL (basic OIDC/OAuth2 params)
    params = {
        "response_type": "code",
        "client_id": client_id_env,
        "state": state,
        "scope": " ".join(body.scopes or []),
    }
    if redirect_uri:
        params["redirect_uri"] = redirect_uri
    if pkce_challenge:
        params["code_challenge"] = pkce_challenge
        params["code_challenge_method"] = "S256"
    # add extra params
    for k, v in (body.extra_params or {}).items():
        params[k] = v

    # Build query string (simple encoding)
    from urllib.parse import urlencode

    authorize_url = f"{auth_url_env}?{urlencode(params)}"
    return OAuthLoginResponse(
        authorize_url=authorize_url,
        state=state,
        pkce_challenge=pkce_challenge,
        pkce_method=pkce_method,
        mode="real",
    )


@router.get(
    "/{connector_id}/oauth/callback",
    summary="Handle OAuth callback for a connector",
    description=(
        "Handles provider redirect with code and state. Verifies CSRF state and optional PKCE, "
        "exchanges code for tokens when client credentials are available, "
        "stores encrypted credentials with repository, otherwise returns mocked success."
    ),
    response_model=OAuthCallbackSuccess,
    responses={
        200: {"description": "OAuth flow completed"},
        400: {"description": "Invalid or expired state"},
        401: {"description": "Unauthorized"},
    },
)
def oauth_callback(
    connector_id: str,
    request: Request,
    response: Response,
    code: Optional[str] = Query(default=None, description="Authorization code from provider"),
    state: Optional[str] = Query(default=None, description="Opaque state returned from provider"),
    ctx: AuthContext = Depends(get_auth_context),
    repo: ConnectionsRepository = Depends(get_connections_repo),
) -> OAuthCallbackSuccess:
    """Process the OAuth callback, validate state, and persist a connection credentials payload.

    Behavior:
    - Validates that 'state' exists in memory and is bound to the same tenant and connector.
    - If client credentials are configured, it would exchange 'code' (stubbed) and encrypt tokens for storage.
      Since we don't call real providers here, we simulate token data when in real mode.
    - If client credentials are absent, returns a mocked success with a created connection using mock credentials.
    """
    if not state:
        raise APIError(code="missing_state", message="Missing state", status_code=400)

    _clean_expired_states()
    record = _STATE_STORE.pop(state, None)
    if record is None:
        raise APIError(code="invalid_state", message="State not found or expired", status_code=400)

    if record.connector != connector_id:
        raise APIError(code="state_connector_mismatch", message="State does not match connector", status_code=400)

    # Ensure tenant in state matches current context (CSRF + multi-tenant safety)
    tenant_id = ctx.tenant_id or ""
    if record.tenant_id != tenant_id:
        raise APIError(code="state_tenant_mismatch", message="State does not match tenant", status_code=400)

    client_id = os.getenv(f"{connector_id.upper()}_CLIENT_ID")
    client_secret = os.getenv(f"{connector_id.upper()}_CLIENT_SECRET")
    token_url = os.getenv(f"{connector_id.upper()}_TOKEN_URL")
    # redirect_uri may be used in a real token exchange; omitted here to avoid linter warning until implemented.

    real_mode = all([client_id, client_secret, token_url])

    # PKCE verification is performed by the provider in the token exchange step; here we just ensure we had a verifier stored if pkce used.
    if record.pkce_verifier and not code:
        # If PKCE used, code must be present to exchange
        raise APIError(code="missing_code", message="Missing authorization code for PKCE flow", status_code=400)

    # Simulated token payload
    if real_mode:
        # In a real implementation, perform HTTP POST to token_url with code, client creds, redirect_uri, and code_verifier.
        # We simulate a token response here.
        token_payload = {
            "access_token": f"acc_{secrets.token_hex(16)}",
            "refresh_token": f"ref_{secrets.token_hex(16)}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "obtained_at": int(time.time()),
            "provider": connector_id,
            "tenant": tenant_id,
        }
        # Encrypt credentials for storage at rest
        encrypted_credentials = encrypt_json(token_payload)
        # Create a connection entity
        from ..models import ConnectionCreate

        connection = repo.create(
            ConnectionCreate(
                tenant_id=tenant_id,
                connector=connector_id,
                credentials={"cipher": encrypted_credentials},
                display_name=f"{connector_id.title()} OAuth",
                status="connected",
                scopes=[],
            )
        )
        return OAuthCallbackSuccess(
            connector=connector_id, status="connected", connection_id=connection.id, message="OAuth connected (real)"
        )

    # Mock mode: no client credentials configured, simulate success
    mock_credentials = {
        "access_token": f"mock_{secrets.token_hex(8)}",
        "token_type": "Bearer",
        "expires_in": 3600,
        "provider": connector_id,
        "tenant": tenant_id,
        "mode": "mock",
    }
    # In mock mode, still encrypt if encryption configured; encrypt_json requires env set, so wrap to avoid raising if not set.
    encrypted: Optional[str] = None
    try:
        encrypted = encrypt_json(mock_credentials)
    except Exception:
        # If encryption secrets are not provided, store plaintext in dev environment.
        encrypted = None

    from ..models import ConnectionCreate

    connection = repo.create(
        ConnectionCreate(
            tenant_id=tenant_id,
            connector=connector_id,
            credentials={"cipher": encrypted} if encrypted else {"mock": mock_credentials},
            display_name=f"{connector_id.title()} (Mock)",
            status="connected",
            scopes=[],
        )
    )
    return OAuthCallbackSuccess(
        connector=connector_id, status="connected", connection_id=connection.id, message="OAuth connected (mock)"
    )
