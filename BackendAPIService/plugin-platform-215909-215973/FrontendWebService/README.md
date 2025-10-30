# FrontendWebService

Next.js frontend for the Plugin Platform.

## Environment

Create .env.local with:
- NEXT_PUBLIC_API_URL=http://localhost:8000
- NEXT_PUBLIC_APP_ORIGIN=http://localhost:3000
- NEXT_PUBLIC_DEV_JWT=dev-token
- NEXT_PUBLIC_TENANT_ID=dev-tenant  # optional; can point to team-a, etc.

CORS:
- Ensure BackendAPIService allows http://localhost:3000; it defaults to this when unset or wildcard.

## Usage

- Integrations page calls GET /connections and shows list states.
- QuickActionModal can create Jira issues or Confluence pages.
- All requests include Authorization dev token and X-Tenant-ID (if provided).

## Verification checklist (end-to-end)

- Load Integrations page: shows "No connections yet." initially.
- Connect mock flow (via backend POST /connectors/{id}/oauth/login then GET /connectors/{id}/oauth/callback) and return to Integrations; connection appears with status.
- Use QuickActionModal to create an issue/page; success banner shows link to resource.
- Change NEXT_PUBLIC_TENANT_ID and verify Integrations reflects a different tenant scope.
