from pydantic import BaseModel
from app.schemas.analysis import AnalysisRequest
class ContextRequest(AnalysisRequest): include_markdown: bool = True
