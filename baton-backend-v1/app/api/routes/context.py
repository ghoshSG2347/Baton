from fastapi import APIRouter,Depends
from app.api.deps import github_token
from app.schemas.context import ContextRequest
from app.services.context_service import ContextService
router=APIRouter(prefix="/api/v1/context",dependencies=[Depends(__import__("app.core.security",fromlist=["require_access_key"]).require_access_key)])
@router.post("")
async def context(req:ContextRequest,token=Depends(github_token)): return await ContextService().create(req,token)
