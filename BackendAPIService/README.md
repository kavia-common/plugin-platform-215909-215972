# BackendAPIService

FastAPI backend for the Plugin Platform.

Features:
- Typed configuration (pydantic-settings) with nested BACKEND_ envs
- Structured logging (JSON by default)
- Global error envelope
- Dev auth using a static JWT token with optional X-Tenant-ID override
- In-memory repository for connections (tenant-scoped)
- Connectors router (list/connect, normalized search, projects/spaces, create issue/page)
- OpenAPI with BearerAuth and tags
- CORS with sensible dev default to http://localhost:3000

## Run locally

1) Install deps
   pip install -r BackendAPIService/requirements.txt

2) Start the server
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 --app-dir BackendAPIService

3) Health
   curl http://localhost:8000/

4) Dev auth usage
   curl -H "Authorization: Bearer dev-token" http://localhost:8000/connectors
   # optional tenant override
   curl -H "Authorization: Bearer dev-token" -H "X-Tenant-ID: team-a" http://localhost:8000/connections

## Environment variables (.env provided by orchestrator)

- BACKEND_LOGGING__LEVEL=INFO
- BACKEND_LOGGING__JSON=true
- BACKEND_LOGGING__SERVICE_NAME=backend-api

- BACKEND_SECURITY__DEV_MODE=true
- BACKEND_SECURITY__DEV_JWT=dev-token
- BACKEND_SECURITY__JWT_AUDIENCE=
- BACKEND_SECURITY__JWT_ISSUER=
- BACKEND_SECURITY__JWKS_URL=

- BACKEND_CORS__ALLOW_ORIGINS=http://localhost:3000
  Notes: if unset or wildcard, the app will default to http://localhost:3000 in dev.

- ENCRYPTION_KEY_BASE64=  # base64-encoded 32-byte key for AES-256-GCM
- ENCRYPTION_KEY_ID=      # optional, appears as "kid" in the envelope

Optional OAuth mock/real envs per connector (for later hardening):
- JIRA_CLIENT_ID, JIRA_CLIENT_SECRET, JIRA_AUTH_URL, JIRA_TOKEN_URL, JIRA_REDIRECT_URI
- CONFLUENCE_CLIENT_ID, ...

## Authentication and Security

- Dev mode accepts a static token:
  Authorization: Bearer dev-token
  - configurable via BACKEND_SECURITY__DEV_JWT
- Tenant scoping header (dev mode): X-Tenant-ID: <tenant>
  - If omitted, defaults to "dev-tenant"
- Production: disable dev mode and configure real JWT verification (JWKS, issuer/audience)

## CORS

- Configure with BACKEND_CORS__ALLOW_ORIGINS
- If unset or wildcard ["*"], the service defaults to http://localhost:3000 for local dev

## Crypto helpers

- AES-256-GCM helpers in src/api/crypto.py
- encrypt_json(payload: dict|BaseModel) -> str
- decrypt_json(envelope_json: str) -> dict

## API Overview

- GET / -> health
- GET /ws-help -> websocket usage help
- GET /connectors -> list available connectors (auth required)
- POST /connectors/{id}/oauth/login -> OAuth authorize (mock/real)
- GET /connectors/{id}/oauth/callback -> OAuth callback (mock/real)
- GET /connectors/{id}/search -> normalized search (mocked unless real creds)
- GET /connectors/{id}/projects -> normalized projects (jira mock)
- GET /connectors/{id}/spaces -> normalized spaces (confluence mock)
- POST /connectors/{id}/issues -> normalized create issue (jira mock)
- POST /connectors/{id}/pages -> normalized create page (confluence mock)
- GET /connections -> list connections for tenant
- POST /connections -> create connection; credentials.plain encrypts to credentials.cipher (fallback to mock)
- GET /connections/{connectionId} -> fetch a specific connection
- DELETE /connections/{connectionId} -> delete connection
- POST /tools/{toolName}/actions -> tool action stub

## Quickstart (Dev)

- Install, run, and test with curl commands above.
- OpenAPI: http://localhost:8000/openapi.json
- Swagger UI: http://localhost:8000/docs

## End-to-End Verification Checklist

- GET /connectors returns Jira and Confluence with 200 using dev token.
- POST /connectors/{c}/oauth/login returns authorize_url and state (mode=mock if no real secrets).
- GET /connectors/{c}/oauth/callback returns connected and creates a connection.
- GET /connections returns created connections for the tenant (respects X-Tenant-ID).
- GET /connectors/{id}/search?q=... returns normalized items; if cipher creds present, titles include " • Real".
- POST /connectors/jira/issues creates a mock normalized issue.
- POST /connectors/confluence/pages creates a mock normalized page.
- DELETE /connections/{id} returns 204 and subsequent delete returns 404 with error envelope.

## Hardening TODO

- Implement real JWT validation (JWKS + issuer/audience)
- Persistent storage (Mongo) for connections
- Real connector SDKs and OAuth code exchange
- Tool dispatch registry
