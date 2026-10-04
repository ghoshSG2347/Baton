from datetime import datetime, timezone
from app.core.config import get_settings
from app.services.github_service import GitHubService
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.utils.file_filters import is_relevant
class AnalysisService:
 def __init__(self,token=None): self.github=GitHubService(token)
 async def analyze(self,owner,repo,branch,folder=""):
  snapshot=await self.github.tree_snapshot(owner,repo,branch)
  all_items=snapshot.get("tree",[]); prefix=folder.strip("/")
  items=[x for x in all_items if (not prefix or x.get("path","")==prefix or x.get("path","").startswith(prefix+"/")) and x.get("type") in {"blob","tree"} and is_relevant(x.get("path",""))]
  blobs=[{"path":x["path"],"type":x["type"],"size":x.get("size")} for x in items]
  contents={}; count=0; skipped=[]
  for x in items:
   if x.get("type")=="blob" and count<get_settings().max_files_per_analysis and x.get("size",0)<=get_settings().max_file_size_bytes:
    try: contents[x["path"]]=(await self.github.file(owner,repo,branch,x["path"]))["content"]; count+=1
    except Exception: skipped.append(x["path"])
   elif x.get("type")=="blob": skipped.append(x["path"])
  metadata={"owner":owner,"repo":repo,"branch":branch,"folder":folder,"commit":snapshot.get("sha"),"generated":datetime.now(timezone.utc).isoformat(),"files_analyzed":count}
  result=RepositoryAnalyzer().analyze(blobs,contents,metadata)
  result["metadata"]["skipped_files"]=skipped
  if skipped: result["analysis_warnings"].append(f"{len(skipped)} relevant files were omitted by analysis limits or could not be read.")
  if not blobs: result["analysis_warnings"].append("Not started: no relevant files detected in the selected folder.")
  return result
