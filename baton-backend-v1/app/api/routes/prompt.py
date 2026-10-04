from fastapi import APIRouter,Depends
from app.schemas.prompt import PromptRequest
from app.services.prompt_service import create
router=APIRouter(prefix="/api/v1/prompt",dependencies=[Depends(__import__("app.core.security",fromlist=["require_access_key"]).require_access_key)])
@router.post("")
async def prompt(req:PromptRequest): return create(req)
