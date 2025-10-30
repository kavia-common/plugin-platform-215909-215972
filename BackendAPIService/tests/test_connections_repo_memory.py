from typing import List
from src.api.db.memory import InMemoryConnectionsRepository
from src.api.models import ConnectionCreate, ConnectionUpdate

def _mk_create(tenant: str, connector: str = "jira", creds=None, name=None, status="connected"):
    creds = creds or {"mock": {"t": "x"}}
    return ConnectionCreate(
        tenant_id=tenant,
        connector=connector,
        credentials=creds,
        display_name=name,
        status=status,
        scopes=["search"],
    )

def test_memory_repo_basic_crud_and_tenant_isolation():
    repo = InMemoryConnectionsRepository()

    # Create two tenants
    a1 = repo.create(_mk_create("tenant-a", name="A-1"))
    a2 = repo.create(_mk_create("tenant-a", connector="confluence", name="A-2"))
    b1 = repo.create(_mk_create("tenant-b", name="B-1"))

    # List per-tenant
    la: List = repo.list_for_tenant("tenant-a")
    lb: List = repo.list_for_tenant("tenant-b")
    assert {c.id for c in la} == {a1.id, a2.id}
    assert {c.id for c in lb} == {b1.id}

    # Get by id respects tenant scoping
    assert repo.get_by_id("tenant-a", a1.id) is not None
    assert repo.get_by_id("tenant-b", a1.id) is None

    # Update
    updated = repo.update("tenant-a", a1.id, ConnectionUpdate(display_name="A-1 updated", status="connected"))
    assert updated is not None
    assert updated.display_name == "A-1 updated"
    # Touch updated_at (cannot assert exact, but ensure attribute exists and changed logically)
    assert hasattr(updated, "updated_at")

    # Delete with tenant scoping
    assert repo.delete("tenant-b", a1.id) is False
    assert repo.delete("tenant-a", a1.id) is True
    assert repo.get_by_id("tenant-a", a1.id) is None

def test_repo_update_nonexistent_returns_none():
    repo = InMemoryConnectionsRepository()
    assert repo.update("t", "missing", ConnectionUpdate(display_name="x")) is None
