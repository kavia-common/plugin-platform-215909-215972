from fastapi.testclient import TestClient

def test_apierror_envelope_on_not_found(client, auth_headers):
    # Try to fetch a non-existing connection; should raise APIError -> 404 with envelope
    resp = client.get("/connections/does-not-exist", headers=auth_headers)
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body and "code" in body["error"] and "message" in body["error"]
    assert body["error"]["code"] == "not_found"

def test_unexpected_exception_envelope(monkeypatch, auth_headers):
    # Create a temporary route that raises an unhandled exception to exercise 500 envelope
    from src.api.main import app

    async def boom():
        raise RuntimeError("kaboom")

    route_path = "/__boom__"
    # Add route dynamically
    app.get(route_path)(boom)  # type: ignore

    test_client = TestClient(app)
    test_client.headers.update(auth_headers)
    resp = test_client.get(route_path)
    # Our global handler catches Exception and returns 500 with envelope
    assert resp.status_code == 500
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "internal_error"
    assert "message" in data["error"]
