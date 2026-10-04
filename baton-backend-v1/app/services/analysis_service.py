from app.core.config import get_settings
from app.services.github_service import GitHubService
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.utils.file_filters import is_relevant
class AnalysisService:
 def __init__(self,token=None): self.github=GitHubService(token)
 async def analyze(self,owner,repo,branch,folder=""):
  items=await self.github.tree(owner,repo,branch,folder); items=[x for x in items if x.get("type") in {"blob","tree"} and is_relevant(x.get("path",""))]
  blobs=[{"path":x["path"],"type":x["type"],"size":x.get("size")} for x in items]
  contents={}; count=0
  for x in items:
   if x.get("type")=="blob" and count<get_settings().max_files_per_analysis and x.get("size",0)<=get_settings().max_file_size_bytes:
    try: contents[x["path"]]=(await self.github.file(owner,repo,branch,x["path"]))["content"]; count+=1
    except Exception: pass
  return RepositoryAnalyzer().analyze(blobs,contents,{"owner":owner,"repo":repo,"branch":branch,"folder":folder})
