from fastapi import APIRouter,Depends
from app.schemas.conflict import ConflictRequest
from app.services.conflict_service import detect
router=APIRouter(prefix="/api/v1/conflicts",dependencies=[Depends(__import__("app.core.security",fromlist=["require_access_key"]).require_access_key)])
@router.post("")
async def conflicts(req:ConflictRequest): return detect(req.files,req.branches)
