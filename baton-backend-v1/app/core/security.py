from fastapi import Header, HTTPException, status
from app.core.config import get_settings
from app.core.exceptions import BatonError
from contextvars import ContextVar
from dataclasses import dataclass
import re

@dataclass(repr=False)
class AICredential:
    key: str
    model: str

REQUEST_AI: ContextVar[AICredential | None] = ContextVar('baton_request_ai', default=None)

def provider_credential():
    credential = REQUEST_AI.get()
    if credential and credential.key:
        return credential
    settings = get_settings()
    return AICredential(settings.gemini_api_key.get_secret_value(), settings.gemini_model)

def validate_ai_input(credential):
    if not credential or not credential.key:
        raise BatonError('Gemini API key required. Enter your key in Repository.', 401, 'ai_key_required')
    if len(credential.key) > 512 or any(c.isspace() or ord(c) < 33 or ord(c) > 126 for c in credential.key):
        raise BatonError('Enter a Gemini API key without whitespace.', 422, 'ai_key_invalid')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}', credential.model):
        raise BatonError('Choose a Gemini model identifier before validating.', 422, 'ai_model_required')

def require_access_key(x_baton_key: str|None = Header(default=None), x_github_token: str | None = Header(default=None), x_gemini_key: str | None = Header(default=None)) -> None:
    # User-owned provider credentials authorize their own read-only work.
    # The optional operator key still protects credential-free legacy tools.
    if (isinstance(x_github_token, str) and x_github_token.strip()) or (isinstance(x_gemini_key, str) and x_gemini_key.strip()):
        return
    expected=get_settings().baton_access_key
    if expected and x_baton_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-Baton-Key")


def require_ai_access(x_baton_key: str | None = Header(default=None)) -> None:
    if REQUEST_AI.get() and REQUEST_AI.get().key:
        validate_ai_input(REQUEST_AI.get())
        return
    if not get_settings().baton_access_key:
        raise BatonError('AI chat requires BATON_ACCESS_KEY configured on the backend. Enter that access key in workspace settings.', 503, 'ai_configuration_incomplete')
    require_access_key(x_baton_key)
