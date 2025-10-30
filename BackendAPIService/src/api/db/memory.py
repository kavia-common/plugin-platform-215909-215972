"""
In-memory repository implementations.

Implements an in-memory ConnectionsRepository useful for development and tests.
Backed by process-local dicts keyed by tenant_id for clear multi-tenant isolation.
"""
from __future__ import annotations

import threading
import uuid
from typing import Dict, List, Optional

from ..models import Connection, ConnectionCreate, ConnectionUpdate


class _IdGenerator:
    """Thread-safe ID generator for in-memory entities."""
    def __init__(self) -> None:
        self._lock = threading.Lock()

    def new_id(self) -> str:
        with self._lock:
            return uuid.uuid4().hex


class InMemoryConnectionsRepository:
    """
    In-memory implementation of ConnectionsRepository.

    Storage structure:
    {
        "<tenant_id>": {
            "<connection_id>": Connection(...),
            ...
        },
        ...
    }
    """
    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Connection]] = {}
        self._id = _IdGenerator()
        self._lock = threading.RLock()

    # PUBLIC_INTERFACE
    def list_for_tenant(self, tenant_id: str) -> List[Connection]:
        """Return all connections for a given tenant_id."""
        with self._lock:
            bucket = self._store.get(tenant_id, {})
            return list(bucket.values())

    # PUBLIC_INTERFACE
    def get_by_id(self, tenant_id: str, connection_id: str) -> Optional[Connection]:
        """Get a specific connection by id for the given tenant_id."""
        with self._lock:
            return self._store.get(tenant_id, {}).get(connection_id)

    # PUBLIC_INTERFACE
    def create(self, payload: ConnectionCreate) -> Connection:
        """Create a new connection within the payload.tenant_id and return it."""
        with self._lock:
            conn_id = self._id.new_id()
            entity = Connection(
                id=conn_id,
                tenant_id=payload.tenant_id,
                connector=payload.connector,
                credentials=payload.credentials,
                display_name=payload.display_name,
                status=payload.status,
                scopes=payload.scopes,
            )
            entity.touch()
            tenant_bucket = self._store.setdefault(payload.tenant_id, {})
            tenant_bucket[conn_id] = entity
            return entity

    # PUBLIC_INTERFACE
    def update(self, tenant_id: str, connection_id: str, payload: ConnectionUpdate) -> Optional[Connection]:
        """Update an existing connection; returns None if not found."""
        with self._lock:
            current = self._store.get(tenant_id, {}).get(connection_id)
            if not current:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            if "display_name" in update_data and update_data["display_name"] is not None:
                current.display_name = update_data["display_name"]
            if "status" in update_data and update_data["status"] is not None:
                current.status = update_data["status"]
            if "credentials" in update_data and update_data["credentials"] is not None:
                current.credentials = update_data["credentials"]
            if "scopes" in update_data and update_data["scopes"] is not None:
                current.scopes = update_data["scopes"]

            current.touch()
            return current

    # PUBLIC_INTERFACE
    def delete(self, tenant_id: str, connection_id: str) -> bool:
        """Delete a connection by id for the given tenant; returns True if deleted."""
        with self._lock:
            bucket = self._store.get(tenant_id)
            if not bucket:
                return False
            return bucket.pop(connection_id, None) is not None
