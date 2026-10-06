from fastapi import APIRouter,Depends
from app.schemas.integration import IntegrationRequest
from app.api.deps import github_token
from app.services.analysis_service import AnalysisService
from app.services.integration_service import compare
router=APIRouter(prefix="/api/v1/integration",dependencies=[Depends(__import__("app.core.security",fromlist=["require_access_key"]).require_access_key)])
@router.post("")
async def integration(req:IntegrationRequest,token=Depends(github_token)):
 if req.frontend_branch and req.backend_branch:
  service=AnalysisService(token)
  frontend=await service.analyze(req.owner,req.repo,req.frontend_branch)
  backend=await service.analyze(req.owner,req.repo,req.backend_branch)
  return {"owner":req.owner,"repo":req.repo,"branch":req.branch,"status":"analyzed","comparison":compare(frontend,backend),"frontend_metadata":frontend.get("metadata"),"backend_metadata":backend.get("metadata")}
 return {"owner":req.owner,"repo":req.repo,"branch":req.branch,"status":"ready","message":"Provide frontend_branch and backend_branch to run a real integration comparison."}
