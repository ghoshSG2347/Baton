import pytest
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
