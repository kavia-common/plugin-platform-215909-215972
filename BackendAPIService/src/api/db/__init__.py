"""
Database and repository interfaces for the Backend API Service.

Provides:
- ConnectionsRepository Protocol (public interface)
- RepositoryProvider: simple injector/factory for repositories
- get_connections_repo dependency for routers
"""
from __future__ import annotations

from typing import List, Optional, Protocol

from fastapi import Depends

from ..models import Connection, ConnectionCreate, ConnectionUpdate
from .memory import InMemoryConnectionsRepository


# PUBLIC_INTERFACE
class ConnectionsRepository(Protocol):
    """Protocol for tenant-scoped connections persistence."""
    def list_for_tenant(self, tenant_id: str) -> List[Connection]:
        """List all connections for a tenant."""
        ...

    def get_by_id(self, tenant_id: str, connection_id: str) -> Optional[Connection]:
        """Get a connection by id for a tenant."""
        ...

    def create(self, payload: ConnectionCreate) -> Connection:
        """Create a new connection."""
        ...

    def update(self, tenant_id: str, connection_id: str, payload: ConnectionUpdate) -> Optional[Connection]:
        """Update an existing connection."""
        ...

    def delete(self, tenant_id: str, connection_id: str) -> bool:
        """Delete a connection by id for a tenant."""
        ...


class RepositoryProvider:
    """
    Simple provider for repositories.

    For now, always returns in-memory implementations. This will be extended
    to select Mongo-backed repositories when database settings are present.
    """
    def __init__(self) -> None:
        self._connections_repo: Optional[ConnectionsRepository] = None

    def connections(self) -> ConnectionsRepository:
        """Return the singleton ConnectionsRepository instance."""
        if self._connections_repo is None:
            # Initialize default in-memory implementation
            self._connections_repo = InMemoryConnectionsRepository()
        return self._connections_repo


# Singleton provider instance for the app lifetime
_repo_provider = RepositoryProvider()


# PUBLIC_INTERFACE
def get_repository_provider() -> RepositoryProvider:
    """Return the repository provider singleton (for advanced scenarios)."""
    return _repo_provider


# PUBLIC_INTERFACE
def get_connections_repo(provider: RepositoryProvider = Depends(get_repository_provider)) -> ConnectionsRepository:
    """FastAPI dependency that returns the tenant-scoped ConnectionsRepository."""
    return provider.connections()
