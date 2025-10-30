from typing import List, Dict
import hashlib

def _deterministic_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def test_connectors_list(client, auth_headers):
    resp = client.get("/connectors", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Expect jira and confluence present
    names = {c["name"] for c in data}
    assert "jira" in names and "confluence" in names


def test_search_mock_jira_deterministic(client, auth_headers):
    query = "test"
    resp = client.get(f"/connectors/jira/search?q={query}&limit=10", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    items: List[Dict] = body["items"]
    # Default mock returns 3 Jira issues
    assert len(items) == 3
    # Check normalized shape
    for it in items:
        assert set(["id", "title", "url", "type"]).issubset(it.keys())
        assert it["type"] == "issue"
        assert it["url"].startswith("https://example.atlassian.net/browse/")
    # Deterministic: repeated call returns same ids in same order
    resp2 = client.get(f"/connectors/jira/search?q={query}&limit=10", headers=auth_headers)
    assert resp2.status_code == 200
    items2 = resp2.json()["items"]
    assert [i["id"] for i in items] == [i["id"] for i in items2]


def test_search_mock_confluence_deterministic_and_limit(client, auth_headers):
    query = "knowledge"
    # limit=1 should trim results
    resp = client.get(f"/connectors/confluence/search?q={query}&limit=1", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    it = data["items"][0]
    assert it["type"] == "page"
    assert it["url"].startswith("https://example.atlassian.net/wiki/spaces/")

    # Without limit we expect 2 items and deterministic hash id shape (12 hex chars)
    resp_all = client.get(f"/connectors/confluence/search?q={query}", headers=auth_headers)
    assert resp_all.status_code == 200
    items = resp_all.json()["items"]
    assert len(items) == 2
    assert all(len(i["id"]) == 12 for i in items)


def test_search_real_tweak_when_cipher_credentials_present(client, auth_headers):
    # Create a connection with cipher credentials to simulate "real mode" tweak in titles
    payload = {
        "connector": "jira",
        "credentials": {"plain": {"access_token": "x"}},
        "display_name": "Jira Real-ish",
    }
    resp_create = client.post("/connections", headers=auth_headers, json=payload)
    assert resp_create.status_code == 201
    conn = resp_create.json()
    assert "cipher" in conn["credentials"] or "mock" in conn["credentials"]

    # Search again; when cipher present (no mock), titles receive " • Real" suffix
    resp = client.get("/connectors/jira/search?q=alpha", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    # At least one item includes " • Real" suffix (cipher path used in create_connection when encrypt works)
    has_real_suffix = any(" • Real" in it["title"] for it in items)
    # If encryption was not configured for some reason, credentials fell back to 'mock' and suffix will not be present.
    # Given conftest sets ENCRYPTION_KEY_BASE64, we expect suffix True.
    assert has_real_suffix is True
