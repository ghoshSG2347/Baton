from fastapi import APIRouter
router=APIRouter()
@router.get("/health")
async def health(): return {"status":"ok","service":"baton-backend"}

@router.get("/api/health", include_in_schema=False)
async def api_health(): return {"status":"ok","service":"baton-backend"}
