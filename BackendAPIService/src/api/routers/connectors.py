"""
Connectors router exposes discovery endpoints for available connectors.

Routes:
- GET /connectors: List available connectors (no auth for bootstrap)
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..connectors.base import ConnectorMetadata
from ..connectors.registry import list_connectors as registry_list

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
