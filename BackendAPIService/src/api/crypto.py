"""
Cryptography utilities for encrypting and decrypting sensitive data at rest.

Provides AES-256-GCM based helpers that use a base64-encoded key sourced from
environment variables. This module is intentionally small and stateless to make
testing and migration to KMS/HSM straightforward later.

Environment variables (configured by orchestrator via .env):
- ENCRYPTION_KEY_BASE64: Base64-encoded 32-byte (256-bit) key used for AES-GCM
- ENCRYPTION_KEY_ID: Optional identifier for the active key (for rotation support)

The ciphertext envelope is JSON with the following fields:
{
  "kid": "key-id-or-null",
  "alg": "AES-256-GCM",
  "nonce": "base64",
  "ciphertext": "base64"  # includes the GCM tag appended to the end
}

Security notes:
- AES-GCM requires a unique nonce (IV) per encryption under the same key.
  This module generates a random 12-byte nonce per call.
- Associated data (AAD) can be added later if we need integrity bound metadata.
"""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, ValidationError

try:
    # We use the widely adopted 'cryptography' package for AES-GCM primitives.
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
except Exception:  # pragma: no cover
    # Defer import errors to runtime so that services which don't exercise crypto
    # aren't blocked during bootstrap tasks. Routes using crypto should clearly
    # surface a helpful error if the package is unavailable.
    AESGCM = None  # type: ignore


ALG = "AES-256-GCM"


class CipherEnvelope(BaseModel):
    """JSON-serializable envelope for AES-GCM ciphertext."""
    kid: Optional[str] = Field(default=None, description="Key identifier (for rotation)")
    alg: str = Field(default=ALG, description="Algorithm used")
    nonce: str = Field(..., description="Base64-encoded 12-byte AES-GCM nonce")
    ciphertext: str = Field(..., description="Base64-encoded ciphertext with tag appended")


@dataclass(frozen=True)
class CryptoContext:
    """Holds the AES-GCM key and optional key id."""
    key: bytes
    key_id: Optional[str]


def _load_context_from_env() -> CryptoContext:
    """Load AES key and optional key_id from environment variables."""
    key_b64 = os.getenv("ENCRYPTION_KEY_BASE64")
    if not key_b64:
        raise RuntimeError("ENCRYPTION_KEY_BASE64 is not set. Please provide a base64-encoded 32-byte key.")

    try:
        key = base64.b64decode(key_b64)
    except Exception as e:
        raise RuntimeError("ENCRYPTION_KEY_BASE64 must be valid base64") from e

    if len(key) != 32:
        raise RuntimeError("ENCRYPTION_KEY_BASE64 must decode to 32 bytes for AES-256-GCM")

    key_id = os.getenv("ENCRYPTION_KEY_ID")
    return CryptoContext(key=key, key_id=key_id)


def _get_aesgcm(ctx: CryptoContext) -> "AESGCM":
    """Create an AESGCM instance from the context."""
    if AESGCM is None:  # pragma: no cover
        raise RuntimeError(
            "Cryptography backend not available. Ensure 'cryptography' package is installed."
        )
    return AESGCM(ctx.key)


def _random_nonce() -> bytes:
    """Return a random 12-byte nonce suitable for AES-GCM."""
    return os.urandom(12)


# PUBLIC_INTERFACE
def encrypt_json(payload: Union[Dict[str, Any], BaseModel]) -> str:
    """
    Encrypt a JSON-serializable payload using AES-256-GCM and return an envelope JSON string.

    The function:
    - Loads key and optional key_id from environment variables
    - Serializes the payload to bytes (UTF-8 JSON)
    - Generates a random 12-byte nonce
    - Encrypts using AESGCM without AAD
    - Returns a JSON string containing kid, alg, nonce, ciphertext (all safe for storage)

    Parameters:
        payload: Dict or Pydantic model to be encrypted

    Returns:
        str: JSON string of CipherEnvelope
    """
    ctx = _load_context_from_env()
    aesgcm = _get_aesgcm(ctx)

    if isinstance(payload, BaseModel):
        data = payload.model_dump()
    else:
        data = payload
    plaintext = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    nonce = _random_nonce()
    ct = aesgcm.encrypt(nonce=nonce, data=plaintext, associated_data=None)

    env = CipherEnvelope(
        kid=ctx.key_id,
        alg=ALG,
        nonce=base64.b64encode(nonce).decode("utf-8"),
        ciphertext=base64.b64encode(ct).decode("utf-8"),
    )
    return env.model_dump_json()


# PUBLIC_INTERFACE
def decrypt_json(envelope_json: str) -> Dict[str, Any]:
    """
    Decrypt a JSON envelope produced by encrypt_json and return the original payload as a dict.

    Parameters:
        envelope_json: JSON string representing CipherEnvelope

    Returns:
        dict: Decrypted payload

    Raises:
        RuntimeError: if configuration is missing/invalid
        ValueError: if the envelope is invalid or decryption fails
    """
    ctx = _load_context_from_env()
    aesgcm = _get_aesgcm(ctx)

    try:
        env = CipherEnvelope.model_validate_json(envelope_json)
    except ValidationError as ve:
        raise ValueError(f"Invalid cipher envelope: {ve}") from ve

    if env.alg != ALG:
        raise ValueError(f"Unsupported algorithm: {env.alg}")

    try:
        nonce = base64.b64decode(env.nonce)
        ciphertext = base64.b64decode(env.ciphertext)
    except Exception as e:
        raise ValueError("Envelope fields must be valid base64") from e

    try:
        plaintext = aesgcm.decrypt(nonce=nonce, data=ciphertext, associated_data=None)
    except Exception as e:
        raise ValueError("Decryption failed") from e

    try:
        return json.loads(plaintext.decode("utf-8"))
    except Exception as e:
        raise ValueError("Decrypted payload is not valid JSON") from e
