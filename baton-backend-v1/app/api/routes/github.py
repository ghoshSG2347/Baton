from fastapi import APIRouter,Depends,Query
from app.api.deps import github_token
from app.services.github_service import GitHubService
from app.schemas.github import *
router=APIRouter(prefix="/api/v1/github",dependencies=[Depends(__import__("app.core.security",fromlist=["require_access_key"]).require_access_key)])
@router.post("/validate-repository")
async def validate(req:RepositoryRequest,token=Depends(github_token)):
 o,r=GitHubService.validate_repo_url(req.repo_url); d=await GitHubService(token).repository(o,r); return {"owner":o,"repository":r,"default_branch":d.get("default_branch"),"visibility":d.get("visibility"),"accessible":True}
@router.get("/branches")
async def branches(owner:str,repo:str,token=Depends(github_token)): return {"branches":[{"name":x["name"],"sha":x["commit"]["sha"]} for x in await GitHubService(token).branches(owner,repo)]}
@router.get("/tree")
async def tree(owner:str,repo:str,branch:str,path:str="",token=Depends(github_token)): return {"items":await GitHubService(token).tree(owner,repo,branch,path)}
@router.get("/file")
async def file(owner:str,repo:str,branch:str,path:str,token=Depends(github_token)): return await GitHubService(token).file(owner,repo,branch,path)
