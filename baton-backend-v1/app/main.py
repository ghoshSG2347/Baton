from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.exceptions import BatonError,baton_exception_handler
from app.api.routes import health,github,analysis,context,prompt,conflicts,integration,workspace
from app.core.response_safety import SafeJSONResponses
from app.core.usage import UsageResponses
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
settings=get_settings()
app=FastAPI(title="Baton Backend",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=False,allow_methods=["*"],allow_headers=["*"],expose_headers=['X-Baton-Usage'])
app.add_exception_handler(BatonError,baton_exception_handler)
@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    return JSONResponse(status_code=422, content={'detail': 'Invalid request. Check required fields, allowed values and size limits.'})
app.add_middleware(SafeJSONResponses)
app.add_middleware(UsageResponses)
for router in (health.router,github.router,analysis.router,context.router,prompt.router,conflicts.router,integration.router,workspace.router): app.include_router(router)
