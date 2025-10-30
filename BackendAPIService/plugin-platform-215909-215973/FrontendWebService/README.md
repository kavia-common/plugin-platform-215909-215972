# FrontendWebService

Next.js frontend for the Plugin Platform.

Environment variables (copy .env.example to .env):
- NEXT_PUBLIC_API_URL: Base URL of Backend API Service (e.g., http://localhost:3001)
- NEXT_PUBLIC_APP_ORIGIN: The origin of this frontend (e.g., http://localhost:3000)

CORS setup (coordination with backend):
- Ensure BackendAPIService sets BACKEND_CORS__ALLOW_ORIGINS to include NEXT_PUBLIC_APP_ORIGIN.
- Default dev setup:
  - Backend: http://localhost:3001
  - Frontend: http://localhost:3000

Notes:
- Authentication is bootstrapped with a development token. Use Authorization: Bearer dev-token when calling backend during development.
