"""
Base routers for the Backend API Service.

This module defines the root API router, a health router, and placeholders for
future domain routers (connectors, connections, tools).
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
