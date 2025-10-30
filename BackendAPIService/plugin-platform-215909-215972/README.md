# plugin-platform-215909-215972

This project contains multiple containers. This README highlights BackendAPIService bootstrap status.

## BackendAPIService

FastAPI backend scaffolded with:
- Typed configuration via pydantic-settings
- Structured logging (JSON by default)
- Global error envelope and exception handling
- Security dependency with development JWT stub
- Repository DI for connections (routers depend on get_connections_repo)
- Base routers mounted (health, connectors, connections, tools)
- OpenAPI metadata and tags

### Run locally

1) Ensure environment variables are provided by orchestrator (.env). You may use a `.env.example` guide below.

2) Install dependencies:
   pip install -r BackendAPIService/requirements.txt

3) Start the server:
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 --app-dir BackendAPIService

4) Test health:
   curl http://localhost:8000/

### Auth (bootstrap)

- Development mode is enabled by default. Provide `Authorization: Bearer dev-token` to access protected routes.
- This is controlled by env vars (see below). Do NOT use in production.

### Environment variables

These should be set via .env (do not commit secrets). Example:

```
# Logging
BACKEND_LOGGING__LEVEL=INFO
BACKEND_LOGGING__JSON=true
BACKEND_LOGGING__SERVICE_NAME=backend-api

# CORS
BACKEND_CORS__ALLOW_ORIGINS=*

# Security (bootstrap)
BACKEND_SECURITY__DEV_MODE=true
BACKEND_SECURITY__DEV_JWT=dev-token
BACKEND_SECURITY__JWT_AUDIENCE=
BACKEND_SECURITY__JWT_ISSUER=
BACKEND_SECURITY__JWKS_URL=

# Database (placeholders)
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

Note: Nested envs use the `BACKEND_` prefix and `__` delimiter (pydantic-settings).

### Crypto helpers

- AES-256-GCM helpers live in `src/api/crypto.py`
- Public functions:
  - encrypt_json(payload: dict|BaseModel) -> str  (returns JSON envelope)
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

### API

- OpenAPI JSON: GET /openapi.json
- Docs: /docs

Key routes:
- GET / -> health
- GET /connectors -> requires Authorization in bootstrap mode
- GET /connections -> requires Authorization (uses repo DI)
- POST /tools/{toolName}/actions -> requires Authorization

### Hardening todo

- Replace dev JWT stub with real JWT validation (JWKS, issuer/audience)
- Add persistent storage backend (e.g., Mongo) for repositories
- Add connector registry and tool dispatch
- Implement OAuth flows and token storage (encrypt credentials with AES-GCM)
