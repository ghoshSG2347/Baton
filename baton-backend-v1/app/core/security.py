from fastapi import Header, HTTPException, status
from app.core.config import get_settings

def require_access_key(x_baton_key: str|None = Header(default=None)) -> None:
    expected=get_settings().baton_access_key
    if expected and x_baton_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-Baton-Key")
