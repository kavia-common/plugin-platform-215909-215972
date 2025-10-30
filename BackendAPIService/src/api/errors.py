"""
Error handling utilities and unified error response envelope.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Application-specific error code")
    message: str = Field(..., description="Human-readable error message")
    target: Optional[str] = Field(default=None, description="Target field or entity that caused the error")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Additional error metadata")


class ErrorEnvelope(BaseModel):
    error: ErrorDetail = Field(..., description="Wrapped error detail")


class APIError(Exception):
    """Base API error that can be raised in routes to return a structured envelope."""

    def __init__(self, code: str, message: str, status_code: int = 400, target: Optional[str] = None,
                 meta: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.target = target
        self.meta = meta


# PUBLIC_INTERFACE
def register_exception_handlers(app) -> None:
    """Register global exception handlers that return ErrorEnvelope."""

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError):
        logger.warning(
            "APIError",
            extra={"path": request.url.path, "method": request.method, "code": exc.code, "service": "backend-api"},
        )
        body = ErrorEnvelope(error=ErrorDetail(code=exc.code, message=exc.message, target=exc.target, meta=exc.meta))
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception(
            "Unhandled exception",
            extra={"path": request.url.path, "method": request.method, "service": "backend-api"},
        )
        body = ErrorEnvelope(error=ErrorDetail(code="internal_error", message="Internal server error"))
        return JSONResponse(status_code=500, content=body.model_dump())
