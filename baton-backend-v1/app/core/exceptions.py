from fastapi import Request
from fastapi.responses import JSONResponse

class BatonError(Exception):
    def __init__(self, detail: str, status_code: int=400, code: str | None=None):
        self.detail, self.status_code, self.code = detail, status_code, code

async def baton_exception_handler(request: Request, exc: BatonError):
    content = {"detail": exc.detail}
    if exc.code:
        content["code"] = exc.code
    return JSONResponse(status_code=exc.status_code, content=content)
