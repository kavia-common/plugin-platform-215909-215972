def test_create_connection_encrypts_plain_or_falls_back_to_mock(client, auth_headers):
    # With conftest setting ENCRYPTION_KEY_BASE64, encrypt_json should work and store under 'cipher'
    payload = {
        "connector": "jira",
        "credentials": {"plain": {"secret": "sensitive"}},
        "display_name": "My Jira",
        "scopes": ["search"],
    }
    resp = client.post("/connections", headers=auth_headers, json=payload)
    assert resp.status_code == 201
    conn = resp.json()
    creds = conn["credentials"]
    assert "cipher" in creds and isinstance(creds["cipher"], str) and len(creds["cipher"]) > 0

    # Retrieve by id
    gid = conn["id"]
    resp_get = client.get(f"/connections/{gid}", headers=auth_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == gid

def test_list_and_delete_connections(client, auth_headers):
    # Ensure list works and delete returns 204 then 404
    resp_list = client.get("/connections", headers=auth_headers)
    assert resp_list.status_code == 200

    # Create one
    payload = {"connector": "confluence", "credentials": {"plain": {"k": "v"}}}
    resp_create = client.post("/connections", headers=auth_headers, json=payload)
    assert resp_create.status_code == 201
    cid = resp_create.json()["id"]

    # List should include new id
    resp_list2 = client.get("/connections", headers=auth_headers)
    assert resp_list2.status_code == 200
    ids2 = [c["id"] for c in resp_list2.json()["items"]]
    assert cid in ids2

    # Delete
    resp_del = client.delete(f"/connections/{cid}", headers=auth_headers)
    assert resp_del.status_code == 204

    # Deleting again should yield error envelope with 404
    resp_del2 = client.delete(f"/connections/{cid}", headers=auth_headers)
    assert resp_del2.status_code == 404
    assert resp_del2.json()["error"]["code"] == "not_found"
