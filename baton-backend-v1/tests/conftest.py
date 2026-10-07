import pytest
from app.services.github_service import GitHubService


@pytest.fixture(autouse=True)
def isolated_github_observations(monkeypatch):
    from app.core.config import get_settings
    # Legacy collector fixtures measure the bounded fallback. Archive tests opt in.
    monkeypatch.setattr(get_settings(), 'github_archive_analysis', False)
    # Never share mocked authorization/HEAD observations between test cases.
    GitHubService._observations.clear()
    GitHubService._observation_sizes.clear()
    GitHubService._backoff.clear()
    yield
    GitHubService._observations.clear()
    GitHubService._observation_sizes.clear()
    GitHubService._backoff.clear()
