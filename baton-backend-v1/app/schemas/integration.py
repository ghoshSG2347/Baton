from pydantic import BaseModel
class IntegrationRequest(BaseModel): owner: str; repo: str; branch: str; frontend_branch: str|None=None; backend_branch: str|None=None
