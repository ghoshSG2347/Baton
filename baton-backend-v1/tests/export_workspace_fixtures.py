"""Generate browser-test responses through real Part 1/2/3 services; no live AI."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import AsyncMock
from app.intelligence.snapshot import MemorySnapshotStore
from app.schemas.workspace import ArtifactRequest, ChatRequest, CompareRequest, WorkspaceRequest
from app.services.context_service import ContextService
from app.services.context_snapshot import ContextSnapshotService
from app.services.workspace_service import WorkspaceService
from tests.test_ai_workspace import choose_api
from tests.test_intelligence import analyze, FIXTURES


async def main():
    base = analyze(FIXTURES['bookos'])
    base.commit = '9c47a3e4a9e721109a6d7f4a0e6594d162409856'
    other = deepcopy(base); other.branch = 'feature/ask-book'; other.commit = '6ab21ff64b8f3e0d191bb0f10fd1b6b52f548437'
    next(f for f in other.file_tree if f['path'] == 'server/routes.ts')['sha'] = 'changed-blob'
    other.api_endpoints[0].response_shape = 'ChangedResponse'
    store = MemorySnapshotStore(); store.save(base); store.save(other)
    snapshots = ContextSnapshotService(store=store)
    snapshots.github.commit = AsyncMock(side_effect=lambda owner, repo, branch: {'sha': other.commit if branch == other.branch else base.commit})
    provider = type('FixtureSelector', (), {})(); provider.select = AsyncMock(side_effect=choose_api)
    workspace = WorkspaceService(ContextService(snapshots), provider)
    fields = {'owner': 'example', 'repo': 'project', 'branch': 'main', 'context_type': 'project'}
    project = await workspace.inspect(WorkspaceRequest(**fields)); project['provider']['configured'] = True
    role_fields = {**fields, 'context_type': 'role', 'member': {'name': 'Frontend developer', 'role': 'Frontend Developer', 'responsibilities': ['Maintain Ask Book UI'], 'ownership': ['client/'], 'do_not_touch': ['server/', 'shared/'], 'team_scope': []}}
    role = await workspace.inspect(WorkspaceRequest(**role_fields)); role['provider']['configured'] = True
    feature = await workspace.inspect(WorkspaceRequest(**{**fields, 'branch': other.branch})); feature['provider']['configured'] = True
    response = await workspace.chat(ChatRequest(**role_fields, message='What is the Ask Book API?'))
    artifact = await workspace.artifact(ArtifactRequest(**role_fields, artifact_type='context'))
    comparison = await workspace.compare(CompareRequest(**role_fields, compare_branch=other.branch))
    chat_artifact = await workspace.chat(ChatRequest(**role_fields, message='Generate a technical design'))
    snapshots.github.commit = AsyncMock(return_value={'sha': 'new-fixture-head'})
    stale = await workspace.inspect(WorkspaceRequest(**role_fields))
    continued = await workspace.inspect(WorkspaceRequest(**role_fields, commit=base.commit, continue_snapshot=True))
    continued['provider']['configured'] = True
    continued_chat = await workspace.chat(ChatRequest(**role_fields, commit=base.commit, continue_snapshot=True, message='What is the Ask Book API?'))
    unavailable = await workspace.inspect(WorkspaceRequest(**{**fields, 'branch': 'missing'}))
    output = Path(__file__).parents[2] / 'baton-frontend/.test-output'
    output.mkdir(exist_ok=True)
    (output / 'workspace-fixtures.json').write_text(json.dumps({'project': project, 'role': role, 'feature': feature, 'chat': response, 'artifact': artifact, 'comparison': comparison,
                                                             'chat_artifact': chat_artifact, 'stale': stale, 'continued': continued,
                                                             'continued_chat': continued_chat, 'unavailable': unavailable}), encoding='utf-8')
    print('Exported canonical fixture responses for isolated browser tests.')


if __name__ == '__main__': asyncio.run(main())
