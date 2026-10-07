from fastapi import APIRouter, Depends
from app.api.deps import github_token
from app.core.security import require_access_key, require_ai_access
from app.schemas.workspace import WorkspaceRequest, ChatRequest, ArtifactRequest, CompareRequest, SourceRequest
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix='/api/v1/workspace', dependencies=[Depends(require_access_key)])

@router.post('/provider/validate', dependencies=[Depends(require_ai_access)])
async def validate_provider():
    from app.services.ai_provider import GeminiProvider
    return await GeminiProvider().validate()


@router.post('/inspect')
async def inspect(req: WorkspaceRequest, token=Depends(github_token)):
    return await WorkspaceService().inspect(req, token)


@router.post('/chat', dependencies=[Depends(require_ai_access)])
async def chat(req: ChatRequest, token=Depends(github_token)):
    return await WorkspaceService().chat(req, token)


@router.post('/artifacts')
async def artifact(req: ArtifactRequest, token=Depends(github_token)):
    return await WorkspaceService().artifact(req, token)


@router.post('/compare')
async def compare(req: CompareRequest, token=Depends(github_token)):
    return await WorkspaceService().compare(req, token)


@router.post('/source')
async def source(req: SourceRequest, token=Depends(github_token)):
    return await WorkspaceService().source(req, req.path, token, req.start_line)
