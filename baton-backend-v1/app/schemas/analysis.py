from pydantic import BaseModel
class AnalysisRequest(BaseModel): owner: str; repo: str; branch: str; folder: str = ""; force_refresh: bool = False
class RepositoryAnalysisRequest(BaseModel): owner: str; repo: str; branch: str = ""; force_refresh: bool = False
