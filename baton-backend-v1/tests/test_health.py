from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings
from app.api.deps import github_token

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "baton-backend"}

def test_api_health_alias():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "baton-backend"}

def test_revision_reports_only_valid_commit_hash(monkeypatch):
    monkeypatch.setenv('RENDER_GIT_COMMIT', 'a' * 40)
    assert client.get('/api/version').json()['revision'] == 'a' * 40
    monkeypatch.setenv('RENDER_GIT_COMMIT', 'not-a-revision')
    assert client.get('/api/version').json()['revision'] is None

def test_access_key_security(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "baton_access_key", "secret-test-key")

    # Health endpoints remain accessible without key
    assert client.get("/health").status_code == 200
    assert client.get("/api/health").status_code == 200

    # Protected endpoint without key fails with 401
    r_unauth = client.post("/api/v1/prompt", json={"task": "do something"})
    assert r_unauth.status_code == 401
    assert "Invalid or missing X-Baton-Key" in r_unauth.json()["detail"]

    # Protected endpoint with invalid key fails with 401
    r_bad = client.post("/api/v1/prompt", json={"task": "do something"}, headers={"X-Baton-Key": "wrong-key"})
    assert r_bad.status_code == 401

    # Protected endpoint with valid key succeeds
    r_good = client.post("/api/v1/prompt", json={"task": "do something"}, headers={"X-Baton-Key": "secret-test-key"})
    assert r_good.status_code == 200

def test_github_token_precedence(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "github_token", "env-token-123")

    # Request token takes precedence over env token
    assert github_token("request-token-456") == "request-token-456"

    import pytest
    from app.core.exceptions import BatonError
    with pytest.raises(BatonError) as failure:
        github_token(None)
    assert failure.value.code == 'github_token_required'
