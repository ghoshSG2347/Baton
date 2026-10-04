from fastapi import Header
from app.core.config import get_settings

def github_token(x_github_token: str|None = Header(default=None)) -> str|None:
    return x_github_token or get_settings().github_token or None
