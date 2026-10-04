from pydantic import BaseModel
class TeamMember(BaseModel): name: str; branch: str|None=None
