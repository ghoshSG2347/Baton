import pytest
from app.services.github_service import GitHubService


@pytest.fixture(autouse=True)
def isolated_github_observations():
    # Never share mocked authorization/HEAD observations between test cases.
    GitHubService._observations.clear()
    GitHubService._observation_sizes.clear()
    GitHubService._backoff.clear()
    yield
    GitHubService._observations.clear()
    GitHubService._observation_sizes.clear()
    GitHubService._backoff.clear()
