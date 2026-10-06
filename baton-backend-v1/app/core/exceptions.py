from fastapi import Request
from fastapi.responses import JSONResponse

class BatonError(Exception):
    def __init__(self, detail: str, status_code: int=400, code: str | None=None, *, metadata: dict | None=None):
        self.detail, self.status_code, self.code = detail, status_code, code
        self.metadata = metadata or {}

async def baton_exception_handler(request: Request, exc: BatonError):
    content = {"detail": exc.detail}
    if exc.code:
        content["code"] = exc.code
    # Only explicitly constructed, credential-free metadata is allowed here.
    for name in ('upstream_status', 'rate_limit', 'rate_limit_kind', 'retry_after',
                 'token_present', 'authorization_present', 'token_source'):
        if name in exc.metadata:
            content[name] = exc.metadata[name]
    return JSONResponse(status_code=exc.status_code, content=content)
