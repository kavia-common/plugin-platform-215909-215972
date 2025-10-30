# plugin-platform-215909-215972

This project contains multiple containers. This README highlights BackendAPIService bootstrap status and how to run it locally.

## BackendAPIService

FastAPI backend scaffolded with:
- Typed configuration via pydantic-settings
- Structured logging (JSON by default)
- Global error envelope and exception handling
- Security dependency with development JWT stub (Bearer token)
- Repository DI for connections (routers depend on get_connections_repo)
- Base routers mounted (health, connectors, connections, tools)
- OpenAPI metadata and tags with BearerAuth security scheme

### Ports

- Default: 8000 (configurable via process manager or deployment tooling)
- Examples:
  - API root (health): http://localhost:8000/
  - Docs (Swagger UI): http://localhost:8000/docs
  - OpenAPI JSON: http://localhost:8000/openapi.json

### Run locally

1) Ensure environment variables are provided by orchestrator (.env). You may use the `.env.example` guide below.

2) Install dependencies:
   pip install -r BackendAPIService/requirements.txt

3) Start the server from repository root:
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 --app-dir BackendAPIService

4) Test health:
   curl http://localhost:8000/

5) Test with dev token (bootstrap):
   curl -H "Authorization: Bearer dev-token" http://localhost:8000/connectors

### Authentication and Security

- BearerAuth security is defined in OpenAPI. In development mode, a static dev token is accepted:
  - Authorization: Bearer dev-token (configurable with BACKEND_SECURITY__DEV_JWT)
- Production should disable dev mode and configure real JWT validation (JWKS + issuer/audience).
- Security environment variables:
  - BACKEND_SECURITY__DEV_MODE=true|false
  - BACKEND_SECURITY__DEV_JWT=dev-token
  - BACKEND_SECURITY__JWT_ISSUER=https://issuer.example.com/
  - BACKEND_SECURITY__JWT_AUDIENCE=your-audience
  - BACKEND_SECURITY__JWKS_URL=https://issuer.example.com/.well-known/jwks.json
- CORS: configure allowed origins with BACKEND_CORS__ALLOW_ORIGINS (comma- or space-separated list supported by pydantic list parsing depending on env loader).

### Environment variables

These should be set via .env (do not commit secrets). Example:

```
# Logging
BACKEND_LOGGING__LEVEL=INFO
BACKEND_LOGGING__JSON=true
BACKEND_LOGGING__SERVICE_NAME=backend-api

# CORS
BACKEND_CORS__ALLOW_ORIGINS=*

# Security (bootstrap/dev) - use dev token locally, disable in production
BACKEND_SECURITY__DEV_MODE=true
BACKEND_SECURITY__DEV_JWT=dev-token

# JWT verification settings (for production hardening)
BACKEND_SECURITY__JWT_AUDIENCE=
BACKEND_SECURITY__JWT_ISSUER=
BACKEND_SECURITY__JWKS_URL=

# Database (placeholders for future persistence)
BACKEND_MONGO_URL=
BACKEND_MONGO_DB=

# Crypto (AES-256-GCM). Required for encrypt/decrypt helpers in src/api/crypto.py
# 32-byte key base64-encoded. Generate securely (example command below creates a random key):
# python - <<'PY'
# import os, base64; print(base64.b64encode(os.urandom(32)).decode())
# PY
ENCRYPTION_KEY_BASE64=
# Optional key id to support rotation; included in ciphertext envelope as "kid"
ENCRYPTION_KEY_ID=
```

Notes:
- Nested envs use the `BACKEND_` prefix and `__` delimiter (pydantic-settings).
- ENCRYPTION_KEY_BASE64 must decode to exactly 32 bytes (256-bit).

### Crypto helpers

- AES-256-GCM helpers live in `BackendAPIService/src/api/crypto.py`
- Public functions:
  - encrypt_json(payload: dict|BaseModel) -> str  (returns JSON envelope string)
  - decrypt_json(envelope_json: str) -> dict
- Cipher envelope: `{"kid": "...", "alg": "AES-256-GCM", "nonce": "<b64>", "ciphertext": "<b64>"}`

Usage example:

```python
from src.api.crypto import encrypt_json, decrypt_json

secret = {"access_token": "redacted", "refresh_token": "redacted"}
enveloped = encrypt_json(secret)
original = decrypt_json(enveloped)
```

Ensure `ENCRYPTION_KEY_BASE64` is set to a base64-encoded 32-byte key; optionally set `ENCRYPTION_KEY_ID` to annotate envelopes for key rotation.

### API Overview

- OpenAPI JSON: GET /openapi.json
- Docs: /docs

Key routes (all protected with BearerAuth except health):
- GET / -> health
- GET /ws-help -> websocket usage help (static)
- GET /connectors -> list available connectors
- POST /connectors/{id}/oauth/login -> mock/real OAuth authorize URL (PKCE supported)
- GET /connectors/{id}/oauth/callback -> mock/real callback and connection creation
- GET /connectors/{id}/search?q=... -> normalized search (mocked unless real creds)
- GET /connectors/{id}/projects -> normalized projects (jira mock)
- GET /connectors/{id}/spaces -> normalized spaces (confluence mock)
- POST /connectors/{id}/issues -> normalized create issue (jira mock)
- POST /connectors/{id}/pages -> normalized create page (confluence mock)
- GET /connections -> list connections (tenant-scoped)
- POST /connections -> create connection; if body.credentials.plain provided, it will be encrypted as credentials.cipher using AES-GCM (fallback to mock)
- GET /connections/{connectionId} -> fetch a specific connection
- DELETE /connections/{connectionId} -> delete connection
- POST /tools/{toolName}/actions -> tool action stub

### Hardening TODO

- Replace dev JWT stub with real JWT validation (JWKS, issuer/audience checks)
- Add persistent storage backend (e.g., Mongo) for repositories
- Add connector registry and tool dispatch implementations
- Implement real OAuth code exchange and token storage (encrypt credentials with AES-GCM)
