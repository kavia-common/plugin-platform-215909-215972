import json
from src.api.crypto import encrypt_json, decrypt_json

def test_encrypt_decrypt_roundtrip_simple_dict():
    payload = {"access_token": "abc", "count": 3, "nested": {"k": "v"}}
    envelope_json = encrypt_json(payload)
    # Envelope is JSON string; must contain required fields
    env = json.loads(envelope_json)
    assert env["alg"] == "AES-256-GCM"
    assert "nonce" in env and "ciphertext" in env
    # Decrypt
    out = decrypt_json(envelope_json)
    assert out == payload

def test_encrypt_decrypt_roundtrip_empty_object():
    payload = {}
    envelope = encrypt_json(payload)
    assert isinstance(envelope, str) and len(envelope) > 0
    out = decrypt_json(envelope)
    assert out == {}
