"""
Configuration module for Backend API Service.

Loads environment variables using pydantic settings and exposes a typed Settings
object to the rest of the application. This allows consistent configuration
across environments without hardcoding secrets.

Environment variables should be provided via a .env file by the orchestrator.
See README for details.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CORSSettings(BaseSettings):
    """CORS configuration settings."""
    allow_origins: List[str] = Field(default_factory=lambda: ["*"], description="List of allowed origins")
    allow_credentials: bool = True
    allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    allow_headers: List[str] = Field(default_factory=lambda: ["*"])


class SecuritySettings(BaseSettings):
    """Security-related configuration settings."""
    # NOTE: For initial bootstrap we support a dev token. Do not use in production.
    dev_mode: bool = Field(default=True, description="If True, allow DEV_JWT to authenticate requests")
    dev_jwt: Optional[str] = Field(default="dev-token", description="Development JWT to bypass validation")
    jwt_audience: Optional[str] = Field(default=None, description="Expected JWT audience")
    jwt_issuer: Optional[str] = Field(default=None, description="Expected JWT issuer")
    jwks_url: Optional[AnyUrl] = Field(default=None, description="JWKS endpoint for JWT signature verification")


class AppMetadata(BaseSettings):
    """Application metadata for OpenAPI docs."""
    title: str = "Plugin Platform Backend API"
    description: str = (
        "REST API for managing connectors, connections, tokens, and LLM tool integration."
    )
    version: str = "1.0.0"
    contact_name: Optional[str] = None
    contact_url: Optional[str] = None
    contact_email: Optional[str] = None


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    json: bool = Field(default=True, description="Enable JSON formatted logs when True")
    service_name: str = Field(default="backend-api", description="Name of the service for logs/metrics")


class Settings(BaseSettings):
    """Top-level application settings model."""
    model_config = SettingsConfigDict(env_prefix="BACKEND_", env_nested_delimiter="__", extra="ignore")

    app: AppMetadata = AppMetadata()
    cors: CORSSettings = CORSSettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()

    # Placeholder for later database settings (Mongo, etc.)
    mongo_url: Optional[str] = Field(default=None, description="MongoDB connection string")
    mongo_db: Optional[str] = Field(default=None, description="MongoDB database name")


# PUBLIC_INTERFACE
@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings loaded from environment variables."""
    return Settings()
