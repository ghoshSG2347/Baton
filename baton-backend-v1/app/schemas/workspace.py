from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.context import ContextRequest


class WorkspaceRequest(ContextRequest):
    model_config = ConfigDict(extra='forbid')
    context_type: Literal['project', 'role', 'task', 'ai_handoff'] = 'ai_handoff'
    continue_snapshot: bool = False


class ChatRequest(WorkspaceRequest):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    revision: int | None = Field(default=None, ge=0, le=20)

    @model_validator(mode='after')
    def conversation_revision(self):
        if (self.conversation_id and self.revision is None) or (not self.conversation_id and self.revision not in (None, 0)):
            raise ValueError('Follow-ups require the returned conversation revision; new chats start at zero.')
        return self


class ArtifactRequest(WorkspaceRequest):
    artifact_type: Literal['context', 'handoff', 'prd', 'technical_design', 'tasks', 'implementation_plan', 'review', 'prompt', 'onboarding'] = 'context'
    target: str = Field(default='Coding agent', max_length=100)


class CompareRequest(WorkspaceRequest):
    compare_branch: str = Field(min_length=1, max_length=200)
    compare_commit: str | None = Field(default=None, max_length=100)


class SourceRequest(WorkspaceRequest):
    path: str = Field(min_length=1, max_length=500)
    start_line: int = Field(default=1, ge=1, le=100000)


class EvidenceAction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['inspect', 'verify', 'resolve_conflict']
    evidence_id: str = Field(max_length=500)
    target_path: str = Field(max_length=500)


class EvidenceSelection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['grounded', 'unknown', 'out_of_scope']
    evidence_ids: list[str] = Field(default_factory=list, max_length=8)
    actions: list[EvidenceAction] = Field(default_factory=list, max_length=5)
    reasoning: list['Reasoning'] = Field(default_factory=list, max_length=4)


class Reasoning(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: Literal['INFERRED', 'RECOMMENDATION', 'GENERAL_EXPLANATION']
    text: str = Field(min_length=1, max_length=1500)
    evidence_ids: list[str] = Field(default_factory=list, max_length=8)
