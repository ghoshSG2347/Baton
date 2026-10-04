from fastapi import Request
from fastapi.responses import JSONResponse

class BatonError(Exception):
    def __init__(self, detail: str, status_code: int=400): self.detail, self.status_code=detail, status_code

async def baton_exception_handler(request: Request, exc: BatonError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
