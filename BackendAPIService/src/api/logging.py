"""
Logging utilities for the Backend API Service.

Provides a standardized logging configurator that supports JSON logging and
contextual enrichment through uvicorn and FastAPI middlewares.
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, Optional

from .config import get_settings


class JsonFormatter(logging.Formatter):
    """A simple JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }
        # Attach common extras if present
        for attr in ("request_id", "path", "method", "status_code", "service", "module", "funcName"):
            if hasattr(record, attr):
                payload[attr] = getattr(record, attr)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


# PUBLIC_INTERFACE
def configure_logging(extra_handlers: Optional[list[logging.Handler]] = None) -> None:
    """Configure root logging based on settings."""
    settings = get_settings()
    level = getattr(logging, settings.logging.level.upper(), logging.INFO)

    # Reset existing handlers to avoid duplicate logs in reloads
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    handler: logging.Handler
    if settings.logging.json:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(JsonFormatter())
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)

    root.setLevel(level)
    root.addHandler(handler)

    # Uvicorn loggers
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(logger_name).handlers = []
        logging.getLogger(logger_name).propagate = True
        logging.getLogger(logger_name).setLevel(level)

    if extra_handlers:
        for h in extra_handlers:
            root.addHandler(h)

    logging.getLogger(__name__).info("Logging configured", extra={"service": settings.logging.service_name})
