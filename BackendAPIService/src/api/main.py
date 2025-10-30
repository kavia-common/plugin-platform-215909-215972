"""
FastAPI application entrypoint.

Sets up:
- App metadata and OpenAPI tags
- Structured logging
- CORS
- Exception handlers with error envelope
- Security placeholders
- Base routers for health, connectors, connections, tools
- WebSocket usage help route (placeholder for future real-time features)
"""
from __future__ import annotations

import logging
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .errors import register_exception_handlers
from .logging import configure_logging
from .routers import TAGS, get_api_router

# Configure logging as early as possible
configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    openapi_tags=TAGS,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# Exceptions
register_exception_handlers(app)

# Routers
app.include_router(get_api_router())


@app.get(
    "/ws-help",
    summary="WebSocket usage help",
    description="This service may expose WebSocket endpoints in the future. Currently, there are none.",
    tags=["health"],
    response_description="Static WebSocket help",
)
def websocket_help() -> Dict[str, str]:
    """Provide a human-readable note about WebSocket usage."""
    return {"message": "No WebSocket endpoints available yet."}
