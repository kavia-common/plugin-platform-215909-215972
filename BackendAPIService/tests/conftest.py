import os
import base64
import pytest
from fastapi.testclient import TestClient

# Ensure test runtime picks dev auth and consistent settings
os.environ.setdefault("BACKEND_SECURITY__DEV_MODE", "true")
os.environ.setdefault("BACKEND_SECURITY__DEV_JWT", "dev-token")
# Configure logging to non-JSON to simplify debugging (optional)
os.environ.setdefault("BACKEND_LOGGING__JSON", "false")

# Provide a static 32-byte key for AES-256-GCM round-trip tests
# 32 zero bytes base64
STATIC_KEY_B64 = base64.b64encode(b"\x00" * 32).decode("utf-8")
os.environ.setdefault("ENCRYPTION_KEY_BASE64", STATIC_KEY_B64)
# Optional key id
os.environ.setdefault("ENCRYPTION_KEY_ID", "test-key")

# Import app after env is set
from src.api.main import app  # noqa: E402

@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI test client with default Authorization header (dev mode)."""
    c = TestClient(app)
    c.headers.update({"Authorization": "Bearer dev-token"})
    return c


@pytest.fixture
def auth_headers() -> dict:
    """Headers including Authorization bearer dev token."""
    return {"Authorization": "Bearer dev-token", "Content-Type": "application/json"}


@pytest.fixture
def tenant_id() -> str:
    # In dev auth stub, tenant_id resolves to 'dev-tenant'
    return "dev-tenant"
