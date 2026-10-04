from pydantic import BaseModel, Field

class RepositoryRequest(BaseModel): repo_url: str
class RepositoryInfo(BaseModel): owner: str; repository: str; default_branch: str|None=None; visibility: str|None=None; accessible: bool
class Branch(BaseModel): name: str; sha: str
class BranchResponse(BaseModel): branches: list[Branch]
class TreeItem(BaseModel): path: str; type: str; size: int|None=None; sha: str|None=None
class TreeResponse(BaseModel): items: list[TreeItem]
class FileResponse(BaseModel): path: str; size: int; content: str; language: str|None=None
