from fastapi import Header, HTTPException, status
from app.core.config import get_settings
from app.core.exceptions import BatonError

def require_access_key(x_baton_key: str|None = Header(default=None)) -> None:
    expected=get_settings().baton_access_key
    if expected and x_baton_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-Baton-Key")


def require_ai_access(x_baton_key: str | None = Header(default=None)) -> None:
    if not get_settings().baton_access_key:
        raise BatonError('AI chat requires BATON_ACCESS_KEY configured on the backend. Enter that access key in workspace settings.', 503, 'ai_configuration_incomplete')
    require_access_key(x_baton_key)
