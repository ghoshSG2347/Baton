from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.exceptions import BatonError,baton_exception_handler
from app.api.routes import health,github,analysis,context,prompt,conflicts,integration
settings=get_settings()
app=FastAPI(title="Baton Backend",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
app.add_exception_handler(BatonError,baton_exception_handler)
for router in (health.router,github.router,analysis.router,context.router,prompt.router,conflicts.router,integration.router): app.include_router(router)
