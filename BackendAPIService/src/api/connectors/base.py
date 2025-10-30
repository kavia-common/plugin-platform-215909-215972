"""
Base connector definitions for the Plugin Platform.

Defines a lightweight abstract interface and Pydantic models that describe connector
metadata. This enables a consistent registry that can statically or dynamically
list available connectors.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel, Field


class ConnectorCapability(BaseModel):
    """Represents a capability the connector supports (e.g., search, create_issue)."""
    key: str = Field(..., description="Unique key for the capability")
    description: Optional[str] = Field(default=None, description="Human-readable description")


class ConnectorMetadata(BaseModel):
    """Metadata describing a connector that can be displayed in UIs/docs."""
    name: str = Field(..., description="Programmatic name of the connector (e.g., jira)")
    title: str = Field(..., description="Human-friendly title")
    description: str = Field(..., description="Description of the connector")
    status: str = Field(default="beta", description="Lifecycle status (alpha, beta, ga)")
    categories: List[str] = Field(default_factory=list, description="Categories for grouping in UI")
    capabilities: List[ConnectorCapability] = Field(default_factory=list, description="Supported capabilities")
    docs_url: Optional[str] = Field(default=None, description="Link to documentation")


class BaseConnector(ABC):
    """Abstract base class that all connectors will implement in the future."""

    # PUBLIC_INTERFACE
    @abstractmethod
    def metadata(self) -> ConnectorMetadata:
        """Return metadata for this connector."""
        raise NotImplementedError
