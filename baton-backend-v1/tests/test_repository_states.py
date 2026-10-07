"""Actual canonical collection -> cache -> inspection transitions."""
from copy import deepcopy
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.intelligence.snapshot import MemorySnapshotStore
from app.schemas.workspace import WorkspaceRequest
from app.services.context_service import ContextService
from app.services.context_snapshot import ContextSnapshotService
from app.services.github_service import GitHubService
from app.services.workspace_service import WorkspaceService
from tests.test_intelligence_service import service_for
from tests.test_ai_workspace import service, request
from tests.test_intelligence import analyze, FIXTURES

@pytest.fixture
def anyio_backend(): return 'asyncio'

@pytest.mark.anyio
async def test_first_analysis_refresh_and_changed_head_use_one_canonical_store():
    analyzer = service_for({'main.py': 'def first(): pass'})
    snapshots = ContextSnapshotService(store=analyzer.store)
    snapshots.github = analyzer.github
    workspace = WorkspaceService(ContextService(snapshots))
    req = WorkspaceRequest(owner='o', repo='r', branch='main')
    before = await workspace.inspect(req)
    assert before['state'] == 'NOT_ANALYZED' and not before['available']
    assert before['identity']['current_head'] == 'commit-sha'
    await analyzer.analyze('o', 'r', 'main')
    current = await workspace.inspect(req)
    assert current['state'] == 'READY' and current['available']
    assert current['identity']['commit'] == current['identity']['current_head']
    await analyzer.analyze('o', 'r', 'main', force_refresh=True)
    refreshed = await workspace.inspect(req)
    assert refreshed['state'] == 'READY'
    assert refreshed['identity']['analysis_timestamp'] != current['identity']['analysis_timestamp']
    assert analyzer.github.tree_snapshot.await_count == 2
    analyzer.github.commit.return_value = {'sha': 'new-head'}
    stale = await workspace.inspect(req)
    assert stale['state'] == 'STALE' and not stale['available']
    assert stale['identity']['current_head'] == 'new-head'
    await analyzer.analyze('o', 'r', 'main', force_refresh=True)
    assert (await workspace.inspect(req))['identity']['commit'] == 'new-head'
    for changed in [req.model_copy(update={'branch': 'feature'}), req.model_copy(update={'repo': 'another'})]:
        result = await workspace.inspect(changed)
        assert result['state'] == 'NOT_ANALYZED' and not result['sections']

@pytest.mark.anyio
async def test_inspection_of_empty_repository_is_normal_state():
    workspace = service()
    workspace.contexts.snapshots.github.commit.side_effect = BatonError('No commits', 409, 'empty_repository')
    result = await workspace.inspect(request())
    assert result['state'] == 'EMPTY_REPOSITORY'
    assert not result['available'] and not result['identity']['current_head']
    assert not result['sections']

@pytest.mark.anyio
async def test_empty_tree_and_specification_are_reported_from_canonical_evidence():
    empty = service(analyze({}))
    assert (await empty.inspect(request()))['state'] == 'EMPTY_REPOSITORY'
    documentation = service(analyze(FIXTURES['specification']))
    result = await documentation.inspect(request())
    assert result['state'] == 'READY'
    assert 'Documentation / Specification Only' in result['project_types']

@pytest.mark.anyio
async def test_invalid_cached_identity_is_not_stale_or_ready():
    workspace = service()
    store = workspace.contexts.snapshots.store
    valid = store.load('example', 'project', 'main', 'commit-1')
    invalid = deepcopy(valid); invalid.branch = 'other'
    store.load = lambda *args: invalid
    result = await workspace.inspect(request())
    assert result['state'] == 'SNAPSHOT_INVALID' and not result['available']
    assert not result['sections']

@pytest.mark.anyio
async def test_analysis_cannot_report_success_when_store_rejects_snapshot():
    analyzer = service_for({'main.py': 'pass'})
    analyzer.store = MemorySnapshotStore(max_bytes=1)
    with pytest.raises(BatonError) as error:
        await analyzer.analyze('o', 'r', 'main', force_refresh=True)
    assert error.value.code == 'snapshot_not_stored'

@pytest.mark.anyio
async def test_refresh_failure_preserves_previous_canonical_snapshot():
    analyzer = service_for({'main.py': 'pass'})
    old = await analyzer.analyze_intelligence('o', 'r', 'main')
    analyzer.github.tree_snapshot.side_effect = BatonError('Rate limit', 429, 'github_rate_limit')
    with pytest.raises(BatonError):
        await analyzer.analyze_intelligence('o', 'r', 'main', force_refresh=True)
    assert analyzer.store.load('o', 'r', 'main', 'commit-sha') == old

@pytest.mark.anyio
async def test_real_github_empty_status_reaches_existing_analysis_handling(monkeypatch):
    monkeypatch.setattr(get_settings(), 'github_token', '')
    async def response(self, method, path, **kwargs):
        return httpx.Response(409, json={'message': 'Git Repository is empty.'})
    with patch('httpx.AsyncClient.request', new=response):
        with pytest.raises(BatonError) as error:
            await GitHubService('fixture-credential').commit('o', 'empty', 'main')
    assert error.value.status_code == 409 and error.value.code == 'empty_repository'

@pytest.mark.parametrize('endpoint,folder', [('repository', ''), ('folder', 'client')])
def test_force_refresh_contract_reaches_existing_analyzer(monkeypatch, endpoint, folder):
    from app.services.analysis_service import AnalysisService
    monkeypatch.setattr(get_settings(), 'baton_access_key', '')
    mock = AsyncMock(return_value={'metadata': {'commit': 'same-head'}})
    monkeypatch.setattr(AnalysisService, 'analyze', mock)
    payload = {'owner': 'o', 'repo': 'r', 'branch': 'main', 'force_refresh': True}
    if folder: payload['folder'] = folder
    result = TestClient(app, headers={'X-GitHub-Token': 'fixture-credential'}).post('/api/v1/analysis/' + endpoint, json=payload)
    assert result.status_code == 200
    mock.assert_awaited_once_with('o', 'r', 'main', folder, force_refresh=True)
