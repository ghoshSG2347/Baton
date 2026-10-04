from pydantic import BaseModel
class AnalysisRequest(BaseModel): owner: str; repo: str; branch: str; folder: str = ""
class RepositoryAnalysisRequest(BaseModel): owner: str; repo: str; branch: str = ""
