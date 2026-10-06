import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings
from app.api.deps import github_token
from app.services.github_service import GitHubService

client = TestClient(app)

def test_github_token_precedence_rules(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "github_token", "env-secret-token")

    # 1. Request token takes precedence over GITHUB_TOKEN
    assert github_token("request-user-token") == "request-user-token"

    # 2. No request token -> fallback to GITHUB_TOKEN
    assert github_token(None) == "env-secret-token"
    assert github_token("") == "env-secret-token"
    assert github_token("   ") == "env-secret-token"

    # 3. No request token + no GITHUB_TOKEN -> unauthenticated request (None)
    monkeypatch.setattr(settings, "github_token", "")
    assert github_token(None) is None
    assert github_token("") is None
    assert github_token("   ") is None


@pytest.mark.anyio
async def test_authorization_header_when_token_exists(monkeypatch):
    # 4. Authorization header is created correctly when token exists
    settings = get_settings()
    monkeypatch.setattr(settings, "github_token", "")

    captured_headers = {}

    async def mock_request(self, method, path, headers=None, **kwargs):
        nonlocal captured_headers
        captured_headers = headers or {}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {"full_name": "owner/repo", "default_branch": "main", "visibility": "public"}
        return mock_resp

    with patch("httpx.AsyncClient.request", new=mock_request):
        # Authenticated service instance
        service = GitHubService(token="user-pat-token")
        await service.repository("owner", "repo")
        assert captured_headers.get("Authorization") == "Bearer user-pat-token"
        assert captured_headers.get("Accept") == "application/vnd.github+json"
        assert captured_headers.get("X-GitHub-Api-Version") == "2022-11-28"

        # Unauthenticated service instance (no token)
        captured_headers = {}
        service_unauth = GitHubService(token=None)
        await service_unauth.repository("owner", "repo")
        assert "Authorization" not in captured_headers


def test_validate_repository_public_unauthenticated():
    # 6. /api/v1/github/validate-repository works for public repo without token
    mock_repo_data = {
        "id": 123456,
        "name": "Collaboration",
        "full_name": "Mondrita-Dutta/Collaboration",
        "default_branch": "main",
        "visibility": "public",
        "private": False,
    }

    with patch.object(GitHubService, "repository", new_callable=AsyncMock) as mock_repo:
        mock_repo.return_value = mock_repo_data
        response = client.post(
            "/api/v1/github/validate-repository",
            json={"repo_url": "https://github.com/Mondrita-Dutta/Collaboration"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["owner"] == "Mondrita-Dutta"
        assert data["repository"] == "Collaboration"
        assert data["default_branch"] == "main"
        assert data["visibility"] == "public"
        assert data["accessible"] is True


def test_validate_repository_with_request_token_and_no_token_leak():
    # 5. Token is never included in response payloads
    mock_repo_data = {
        "id": 999999,
        "name": "PrivateRepo",
        "full_name": "TestOrg/PrivateRepo",
        "default_branch": "main",
        "visibility": "private",
        "private": True,
    }

    user_token = "ghp_secure_operator_pat_value"

    with patch.object(GitHubService, "repository", new_callable=AsyncMock) as mock_repo:
        mock_repo.return_value = mock_repo_data
        response = client.post(
            "/api/v1/github/validate-repository",
            json={"repo_url": "https://github.com/TestOrg/PrivateRepo.git"},
            headers={"X-GitHub-Token": user_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["owner"] == "TestOrg"
        assert data["repository"] == "PrivateRepo"
        assert data["visibility"] == "private"
        assert data["accessible"] is True

        # Verify token is NEVER leaked in response payload
        assert "token" not in data
        assert "github_token" not in data
        assert "Authorization" not in data
        assert user_token not in str(data)


def test_validate_repository_url_normalization():
    # Tests trailing slash and .git normalization
    assert GitHubService.validate_repo_url("https://github.com/owner/repo") == ("owner", "repo")
    assert GitHubService.validate_repo_url("https://github.com/owner/repo/") == ("owner", "repo")
    assert GitHubService.validate_repo_url("https://github.com/owner/repo.git") == ("owner", "repo")
    assert GitHubService.validate_repo_url("https://github.com/owner/repo.git/") == ("owner", "repo")


@pytest.mark.parametrize("status,headers,message,expected_status,code", [
    (401, {}, "Bad credentials", 401, "github_authentication_failure"),
    (403, {}, "Resource not accessible", 403, "github_permission_failure"),
    (403, {"x-ratelimit-remaining": "0"}, "API rate limit exceeded", 429, "github_rate_limit"),
    (403, {"retry-after": "60"}, "secondary rate limit", 429, "github_rate_limit"),
    (429, {}, "Too many requests", 429, "github_rate_limit"),
    (404, {}, "Not Found", 404, "github_not_found"),
    (503, {}, "Unavailable", 502, "github_api_failure"),
])
def test_github_failure_propagation(monkeypatch, status, headers, message, expected_status, code):
    monkeypatch.setattr(get_settings(), "baton_access_key", "")
    async def response(self, method, path, **kwargs):
        assert path == "/repos/ghoshSG2347/No-Way-Home3"
        return httpx.Response(status, headers=headers, json={"message": message + " ghp_upstream_secret"})
    with patch("httpx.AsyncClient.request", new=response):
        result = client.post("/api/v1/github/validate-repository",
                             json={"repo_url": "https://github.com/ghoshSG2347/No-Way-Home3"},
                             headers={"X-GitHub-Token": "ghp_request_secret"})
    assert result.status_code == expected_status
    assert result.json()["code"] == code
    assert "ghp_" not in result.text
    assert "GitHub request failed" not in result.text


@pytest.mark.parametrize("url", ["https://example.com/owner/repo", "https://github.com/owner/.git", "https://github.com/owner/../"])
def test_invalid_repository_error(url):
    result = client.post("/api/v1/github/validate-repository", json={"repo_url": url})
    assert result.status_code == 400
    assert result.json()["code"] == "invalid_repository_url"


@pytest.mark.parametrize("invalid_json", [False, True])
def test_github_network_and_invalid_response(monkeypatch, invalid_json):
    monkeypatch.setattr(get_settings(), "baton_access_key", "")
    async def response(self, method, path, **kwargs):
        if invalid_json:
            return httpx.Response(200, text="not json ghp_upstream_secret")
        raise httpx.ConnectError("connection error ghp_request_secret")
    with patch("httpx.AsyncClient.request", new=response):
        result = client.post("/api/v1/github/validate-repository", json={"repo_url": "https://github.com/owner/repo"})
    assert result.status_code == 502
    assert result.json()["code"] == ("github_api_failure" if invalid_json else "github_network_failure")
    assert "ghp_" not in result.text
