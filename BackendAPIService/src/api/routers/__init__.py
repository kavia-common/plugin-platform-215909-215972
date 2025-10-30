"""
Base routers for the Backend API Service.

This module defines the root API router, a health router, and placeholders for
future domain routers (connectors, connections, tools). The connections router
uses a DI-provided ConnectionsRepository (via get_connections_repo). The concrete
implementation defaults to in-memory, and can be swapped to a persistent backend
via the repository provider without changing router code.
"""
from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends

from ..errors import APIError
from ..models import Connection, ConnectionListResponse
from ..db import get_connections_repo, ConnectionsRepository
from ..security import AuthContext, get_auth_context
from .connectors import router as connectors_router_v1

# Tags used in OpenAPI
TAGS = [
    {"name": "health", "description": "Service health and readiness probes"},
    {"name": "connectors", "description": "Manage available connectors"},
    {"name": "connections", "description": "Tenant-scoped connections to external tools"},
    {"name": "tools", "description": "LLM tools integration endpoints"},
]


health_router = APIRouter(prefix="", tags=["health"])


@health_router.get(
    "/",
    summary="Health Check",
    description="Basic health check to verify the service is running.",
    response_model=dict,
)
def health_check() -> Dict[str, str]:
    """Return service health status."""
    return {"message": "Healthy"}


# Placeholder routers for future expansion
connections_router = APIRouter(prefix="/connections", tags=["connections"])
tools_router = APIRouter(prefix="/tools", tags=["tools"])


@connections_router.get(
    "",
    summary="List connections for a tenant",
    description="Returns all connections for the authenticated tenant.",
    response_model=ConnectionListResponse,
    responses={200: {"description": "A list of connections"}},
)
def list_connections(
    ctx: AuthContext = Depends(get_auth_context),
    repo: ConnectionsRepository = Depends(get_connections_repo),
) -> ConnectionListResponse:
    """List connections for current tenant using the repository dependency."""
    items: List[Connection] = repo.list_for_tenant(ctx.tenant_id or "")
    return ConnectionListResponse(items=items)


@connections_router.post(
    "",
    summary="Create a new connection for a tenant",
    description=(
        "Creates a new connection for the authenticated tenant. "
        "If the provided credentials include a 'plain' field, it will be encrypted using AES-GCM and stored as 'cipher'. "
        "If encryption is not configured, the plain credentials will be stored under 'mock'."
    ),
    status_code=201,
    response_model=Connection,
    responses={
        201: {"description": "Connection created"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
    },
)
def create_connection(
    body: Dict,
    ctx: AuthContext = Depends(get_auth_context),
    repo: ConnectionsRepository = Depends(get_connections_repo),
) -> Connection:
    """Create a connection for the current tenant, encrypting credentials when possible."""
    from ..models import ConnectionCreate
    from ..crypto import encrypt_json

    tenant_id = ctx.tenant_id or ""
    connector = body.get("connector")
    if not connector:
        raise APIError(code="invalid_input", message="connector is required", status_code=400)

    # Accept provided credentials; if body.credentials.plain exists, attempt to encrypt
    credentials = body.get("credentials") or {}
    if "plain" in credentials:
        try:
            cipher = encrypt_json(credentials["plain"])
            credentials = {"cipher": cipher}
        except Exception:
            # Fall back to mock/plain storage for dev environments
            credentials = {"mock": credentials["plain"]}

    display_name = body.get("display_name")
    status = body.get("status", "connected" if ("cipher" in credentials or "mock" in credentials) else "disconnected")
    scopes = body.get("scopes", [])

    entity = repo.create(
        ConnectionCreate(
            tenant_id=tenant_id,
            connector=connector,
            credentials=credentials,
            display_name=display_name,
            status=status,
            scopes=scopes,
        )
    )
    return entity


@connections_router.get(
    "/{connectionId}",
    summary="Get details of a specific connection",
    description="Returns a single connection by id for the authenticated tenant.",
    response_model=Connection,
    responses={
        200: {"description": "Connection details"},
        404: {"description": "Not found"},
        401: {"description": "Unauthorized"},
    },
)
def get_connection(
    connectionId: str,
    ctx: AuthContext = Depends(get_auth_context),
    repo: ConnectionsRepository = Depends(get_connections_repo),
) -> Connection:
    """Get a specific connection for the current tenant."""
    entity = repo.get_by_id(ctx.tenant_id or "", connectionId)
    if not entity:
        raise APIError(code="not_found", message="Connection not found", status_code=404)
    return entity


@connections_router.delete(
    "/{connectionId}",
    summary="Delete a connection",
    description="Deletes a connection by id for the authenticated tenant.",
    status_code=204,
    responses={
        204: {"description": "Deleted"},
        404: {"description": "Not found"},
        401: {"description": "Unauthorized"},
    },
)
def delete_connection(
    connectionId: str,
    ctx: AuthContext = Depends(get_auth_context),
    repo: ConnectionsRepository = Depends(get_connections_repo),
):
    """Delete a connection for the current tenant. Returns 204 on success."""
    ok = repo.delete(ctx.tenant_id or "", connectionId)
    if not ok:
        raise APIError(code="not_found", message="Connection not found", status_code=404)
    return {}


@tools_router.post(
    "/{toolName}/actions",
    summary="Invoke an action on a connector tool",
    description="Invoke an action on a tool for LLM agent integration (stub).",
    responses={200: {"description": "Action result"}},
)
def invoke_tool_action(toolName: str, ctx: AuthContext = Depends(get_auth_context)):
    """Invoke a tool action (stub) returns a placeholder result."""
    # Future: dispatch to registered tool implementation
    if not toolName:
        raise APIError(code="invalid_tool", message="Tool name is required", status_code=400)
    return {"tool": toolName, "tenantId": ctx.tenant_id, "result": "ok"}


# PUBLIC_INTERFACE
def get_api_router() -> APIRouter:
    """Return the root API router with all sub-routers mounted."""
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(connectors_router_v1)
    router.include_router(connections_router)
    router.include_router(tools_router)
    return router
