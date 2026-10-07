from fastapi import APIRouter
import os
import re
router=APIRouter()
@router.get("/health")
async def health(): return {"status":"ok","service":"baton-backend"}

@router.get("/api/health", include_in_schema=False)
async def api_health(): return {"status":"ok","service":"baton-backend"}

@router.get('/api/version')
async def version():
    revision = os.environ.get('RENDER_GIT_COMMIT', '')
    return {'service': 'baton-backend', 'revision': revision if re.fullmatch(r'[0-9a-f]{40}', revision) else None}
