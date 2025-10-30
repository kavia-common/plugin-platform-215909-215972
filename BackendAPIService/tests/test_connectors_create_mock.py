def test_create_issue_mock(client, auth_headers):
    body = {"title": "Bug in login", "project_key": "PP"}
    resp = client.post("/connectors/jira/issues", headers=auth_headers, json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "issue"
    assert data["title"] == body["title"]
    assert data["key"].startswith("PP-")
    assert data["url"].startswith("https://example.atlassian.net/browse/")
    assert len(data["id"]) == 12  # deterministic hash length


def test_create_issue_missing_title_returns_error_envelope(client, auth_headers):
    body = {"project_key": "PP"}
    resp = client.post("/connectors/jira/issues", headers=auth_headers, json=body)
    assert resp.status_code == 400
    data = resp.json()
    # Error envelope shape
    assert "error" in data and "code" in data["error"] and "message" in data["error"]
    assert data["error"]["code"] == "invalid_input"


def test_create_page_mock(client, auth_headers):
    body = {"title": "Onboarding Guide", "project_key": "SPACE"}
    resp = client.post("/connectors/confluence/pages", headers=auth_headers, json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "page"
    assert data["title"] == body["title"]
    assert data["key"] == "SPACE"
    assert data["url"].startswith("https://example.atlassian.net/wiki/spaces/SPACE/pages/")
    assert len(data["id"]) == 12


def test_create_page_wrong_connector_error(client, auth_headers):
    body = {"title": "Wrong", "project_key": "X"}
    resp = client.post("/connectors/jira/pages", headers=auth_headers, json=body)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "unsupported_connector"
