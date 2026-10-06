from fastapi import Header
from app.core.config import get_settings

class ResolvedGitHubToken(str):
    def __new__(cls, value, source):
        instance = super().__new__(cls, value)
        instance.source = source
        return instance

def github_token(x_github_token: str | None = Header(default=None)) -> str | None:
    if x_github_token and x_github_token.strip():
        return ResolvedGitHubToken(x_github_token.strip(), 'request')
    env_token = get_settings().github_token
    if env_token and env_token.strip():
        return ResolvedGitHubToken(env_token.strip(), 'server')
    return None
