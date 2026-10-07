from fastapi import Header
from app.core.exceptions import BatonError

class ResolvedGitHubToken(str):
    def __new__(cls, value, source):
        instance = super().__new__(cls, value)
        instance.source = source
        return instance

def github_token(x_github_token: str | None = Header(default=None)) -> str | None:
    if x_github_token and x_github_token.strip():
        return ResolvedGitHubToken(x_github_token.strip(), 'request')
    raise BatonError('GitHub token required. Enter your Fine-grained GitHub token with Metadata: Read and Contents: Read for this repository.', 401, 'github_token_required')
