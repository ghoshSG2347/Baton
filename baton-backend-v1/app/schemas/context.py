from enum import Enum
from pydantic import BaseModel, Field
from app.schemas.analysis import AnalysisRequest


class ContextType(str, Enum):
    PROJECT = 'project'
    ROLE = 'role'
    TASK = 'task'
    AI_HANDOFF = 'ai_handoff'


class MemberContext(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    role: str | None = Field(default=None, max_length=200)
    responsibilities: list[str] = Field(default_factory=list, max_length=100)
    ownership: list[str] = Field(default_factory=list, max_length=100)
    do_not_touch: list[str] = Field(default_factory=list, max_length=100)
    team_scope: list[str] = Field(default_factory=list, max_length=100)


class ContextOptions(BaseModel):
    context_type: ContextType = ContextType.PROJECT
    member: MemberContext | None = None
    task: str | None = Field(default=None, max_length=20000)
    constraints: list[str] = Field(default_factory=list, max_length=100)


class ContextRequest(AnalysisRequest, ContextOptions):
    include_markdown: bool = True
    commit: str | None = Field(default=None, max_length=100)
    max_bytes: int | None = Field(default=None, ge=1024)
