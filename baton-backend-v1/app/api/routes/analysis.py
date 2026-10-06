from fastapi import APIRouter,Depends
from app.api.deps import github_token
from app.schemas.analysis import *
from app.services.analysis_service import AnalysisService
router=APIRouter(prefix="/api/v1/analysis",dependencies=[Depends(__import__("app.core.security",fromlist=["require_access_key"]).require_access_key)])
@router.post("/folder")
async def folder(req:AnalysisRequest,token=Depends(github_token)): return await AnalysisService(token).analyze(req.owner,req.repo,req.branch,req.folder,force_refresh=req.force_refresh)
@router.post("/repository")
async def repository(req:RepositoryAnalysisRequest,token=Depends(github_token)): return await AnalysisService(token).analyze(req.owner,req.repo,req.branch,"",force_refresh=req.force_refresh)
