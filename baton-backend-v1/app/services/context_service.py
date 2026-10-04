from app.services.analysis_service import AnalysisService
from app.generators.context_generator import generate
from app.core.config import get_settings
class ContextService:
 async def create(self,req,token=None):
  a=await AnalysisService(token).analyze(req.owner,req.repo,req.branch,req.folder); return {"analysis":a,**generate(a,get_settings().max_total_context_bytes)}
