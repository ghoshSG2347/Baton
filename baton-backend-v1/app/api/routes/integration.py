from fastapi import APIRouter,Depends
from app.schemas.integration import IntegrationRequest
router=APIRouter(prefix="/api/v1/integration",dependencies=[Depends(__import__("app.core.security",fromlist=["require_access_key"]).require_access_key)])
@router.post("")
async def integration(req:IntegrationRequest): return {"owner":req.owner,"repo":req.repo,"branch":req.branch,"status":"ready","message":"Analyze frontend and backend branches separately to compare integration contracts."}
