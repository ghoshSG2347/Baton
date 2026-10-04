from fastapi import Header
from app.core.config import get_settings

def github_token(x_github_token: str | None = Header(default=None)) -> str | None:
    if x_github_token and x_github_token.strip():
        return x_github_token.strip()
    env_token = get_settings().github_token
    if env_token and env_token.strip():
        return env_token.strip()
    return None
