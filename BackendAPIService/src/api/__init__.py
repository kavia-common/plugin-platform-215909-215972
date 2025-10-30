"""
Backend API Service package.

This package exposes commonly used submodules (models, db) for convenience.
"""
from __future__ import annotations

# PUBLIC_INTERFACE
def package_info() -> str:
    """Return brief information about this package."""
    return "Plugin Platform Backend API - package init"


# Re-export commonly used modules for convenience
from . import models  # noqa: F401,E402
from . import db  # noqa: F401,E402
