# plugin-platform-215909-215972

This project contains multiple containers. This README highlights BackendAPIService bootstrap status.

## BackendAPIService

FastAPI backend scaffolded with:
- Typed configuration via pydantic-settings
- Structured logging (JSON by default)
- Global error envelope and exception handling
- Security dependency with development JWT stub
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
```

Note: Nested envs use the `BACKEND_` prefix and `__` delimiter (pydantic-settings).

### API

- OpenAPI JSON: GET /openapi.json
- Docs: /docs

Key routes:
- GET / -> health
- GET /connectors -> requires Authorization in bootstrap mode
- GET /connections -> requires Authorization
- POST /tools/{toolName}/actions -> requires Authorization

### Hardening todo

- Replace dev JWT stub with real JWT validation (JWKS, issuer/audience)
- Add persistence layer and repositories
- Add connector registry and tool dispatch
- Implement OAuth flows and token storage
