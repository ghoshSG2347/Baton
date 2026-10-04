from app.analyzers.stack_analyzer import analyze as stack
from app.analyzers.structure_analyzer import analyze as structure
from app.analyzers.api_analyzer import analyze as api
from app.analyzers.frontend_analyzer import analyze as frontend
from app.analyzers.handoff_analyzer import analyze as handoffs
class RepositoryAnalyzer:
 def analyze(self,files,contents,metadata=None):
  result={"metadata":metadata or {},"stack":stack(files),**structure(files),**api(contents),**frontend(contents),"handoffs":handoffs(contents),"shared_files":[],"stray_files":[],"analysis_warnings":[]}
  return result
