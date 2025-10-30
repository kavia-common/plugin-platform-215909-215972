"""
Domain models for the Backend API Service.

Defines Pydantic models used across routers and repositories, starting with
tenant-scoped connections to external tools.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TimestampedModel(BaseModel):
    """Base model providing created/updated timestamps."""
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp (UTC)")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp (UTC)")

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        object.__setattr__(self, "updated_at", datetime.utcnow())


class ConnectionBase(BaseModel):
    """Base fields shared by connection variants."""
    connector: str = Field(..., description="Connector name (e.g., jira, confluence)")
    # Credentials will later be encrypted at-rest; in-memory store keeps them as-is.
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Connector credentials/payload")
    display_name: Optional[str] = Field(default=None, description="Human-friendly name for the connection")
    status: str = Field(default="disconnected", description="Connection status (connected, disconnected, error)")
    scopes: List[str] = Field(default_factory=list, description="Granted scopes/capabilities for this connection")


class ConnectionCreate(ConnectionBase):
    """Payload to create a new connection."""
    tenant_id: str = Field(..., description="Tenant ID to which the connection belongs")


class ConnectionUpdate(BaseModel):
    """Payload to update an existing connection."""
    display_name: Optional[str] = Field(default=None, description="Human-friendly name")
    status: Optional[str] = Field(default=None, description="Connection lifecycle status")
    credentials: Optional[Dict[str, Any]] = Field(default=None, description="Updated credentials payload")
    scopes: Optional[List[str]] = Field(default=None, description="Updated scopes")


class Connection(ConnectionBase, TimestampedModel):
    """Represents a stored connection entity."""
    id: str = Field(..., description="Unique connection identifier")
    tenant_id: str = Field(..., description="Tenant ID owning this connection")


# PUBLIC_INTERFACE
class ConnectionListResponse(BaseModel):
    """Response wrapper for listing connections."""
    items: List[Connection] = Field(default_factory=list, description="Connections list")
