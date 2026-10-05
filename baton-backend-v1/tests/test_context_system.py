"""Part 2: canonical truth, boundary closure, projection budgets and no rescans."""
from copy import deepcopy
from dataclasses import asdict
import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.generators.context_generator import generate
from app.generators.context_relevance import in_scope
from app.intelligence.models import DirectoryRole, SnapshotStatus, UserOverride
from app.intelligence.snapshot import MemorySnapshotStore
from app.main import app
from app.schemas.context import ContextRequest
from app.services.analysis_service import AnalysisService
from app.services.context_service import ContextService
from app.services.context_snapshot import ContextSnapshotService, REFRESH_MESSAGE
from tests.test_intelligence import analyze, FIXTURES


@pytest.fixture
def anyio_backend():
    return 'asyncio'


def briefing(intel, view='project', **options):
    return generate(intel, 2_000_000, options={'context_type': view, **options}, generated_at='2026-10-05T01:00:00Z')


def loader(intel=None):
    store = MemorySnapshotStore()
    if intel is not None:
        store.save(intel)
    service = ContextSnapshotService(store=store)
    service.github.commit = AsyncMock(return_value={'sha': 'commit-1'})
    service.github.repository = AsyncMock(return_value={'default_branch': 'main'})
    service.github.tree_snapshot = AsyncMock(side_effect=AssertionError('Context must not scan'))
    service.github.file = AsyncMock(side_effect=AssertionError('Context must not read files'))
    return service


def test_twenty_sections_and_real_contracts_are_a_briefing():
    intel = analyze(FIXTURES['bookos'])
    result = briefing(intel)
    md = result['markdown']
    assert len(result['context']['sections']) == 20
    for section in result['context']['sections']:
        assert f"## {section['number']}. {section['title']}" in md
    for term in ('Inputs:', 'Outputs:', 'Dependents:', 'POST /api/ask-book', 'AskRequest', 'bookId', 'question', 'server/retrieval.ts', 'Keep retrieval separate', 'NOT_DETECTED', 'confidence', 'DOCUMENTED', 'UNKNOWN'):
        assert term.lower() in md.lower()
    assert result['context']['identity']['commit'] == intel.commit
    assert result['context']['identity']['analysis_timestamp'] == intel.generated
    assert not result['context']['completeness']['budget_omitted_blocks']


@pytest.mark.parametrize('view', ['project', 'role', 'task', 'ai_handoff'])
def test_views_share_identity_and_never_mutate_canonical_truth(view):
    intel = analyze(FIXTURES['bookos'])
    before = deepcopy(asdict(intel))
    result = briefing(intel, view, member={'role': 'Frontend Developer', 'ownership': ['client/']}, task='Improve askBook')
    assert result['context']['identity']['snapshot_id'] == briefing(intel)['context']['identity']['snapshot_id']
    assert result['context']['identity']['context_type'] == view
    assert asdict(intel) == before
    for req in intel.requirements:
        assert req.id in result['markdown']
    assert result['context']['task']['source'] == 'USER'


def test_frontend_keeps_protected_backend_types_data_and_ai_connections():
    result = briefing(analyze(FIXTURES['bookos']), 'role', member={
        'name': 'A Developer', 'role': 'Frontend Developer', 'responsibilities': ['Build Ask Book UI'],
        'ownership': ['client/'], 'do_not_touch': ['server/', 'shared/'], 'team_scope': ['client/']})
    selected = result['context']['relevance']
    assert set(selected['editable_files']) == {'client/AskBook.tsx', 'client/package.json'}
    assert {'server/routes.ts', 'server/retrieval.ts', 'server/ai.ts', 'shared/contracts.ts', 'data/books.json'} <= set(selected['dependency_files'])
    assert 'shared/contracts.ts' in selected['protected_files']
    assert 'server/routes.ts' in selected['cross_boundary_files']
    assert 'POST /api/ask-book' in result['markdown']
    assert result['context']['member']['ownership'] == ['client/']
    assert result['context']['member']['source'] == 'USER'


def test_protection_wins_overlap_and_does_not_hide_files():
    result = briefing(analyze(FIXTURES['bookos']), 'role', member={'ownership': ['server/'], 'do_not_touch': ['server/routes.ts']})
    relevance = result['context']['relevance']
    assert 'server/routes.ts' in relevance['selected_files']
    assert 'server/routes.ts' not in relevance['editable_files']
    assert any('takes precedence' in w for w in relevance['warnings'])


def test_team_scope_and_role_relevance_do_not_assign_ownership():
    result = briefing(analyze(FIXTURES['frontend']), 'role', member={'role': 'Frontend Developer', 'team_scope': ['odd_name/']})
    assert 'Ownership configuration was not provided.' in result['markdown']
    assert not result['context']['relevance']['editable_files']
    assert 'odd_name/App.tsx' in result['context']['relevance']['primary_files']


def test_unfamiliar_role_falls_back_without_guessing_architecture():
    intel = analyze(FIXTURES['ambiguous'])
    result = briefing(intel, 'role', member={'role': 'Arbitrary steward', 'ownership': ['missing/']})
    assert result['context']['relevance']['status'] == 'UNKNOWN'
    assert set(result['context']['relevance']['selected_files']) == {f['path'] for f in intel.file_tree}
    assert any('no matching' in w for w in result['context']['relevance']['warnings'])
    assert 'Ambiguous / Mixed' in result['markdown']


def test_user_role_override_is_visible_and_preserves_original():
    intel = analyze(FIXTURES['ambiguous'])
    original = intel.directory_classifications[0].role
    intel.user_overrides.append(UserOverride(target='core', field='role', value=DirectoryRole.FRONTEND.value, original_value=original.value, reason='Team supplied correction'))
    result = briefing(intel, 'role', member={'role': 'Frontend Developer'})
    assert 'USER correction' in result['markdown']
    assert original.value in result['markdown']
    assert intel.directory_classifications[0].role == original
    assert result['context']['relevance']['status'] == 'INFERRED'


def test_task_selects_canonical_symbols_without_creating_requirements():
    intel = analyze({'one.py': 'def frobnicate(value):\n    return value\n', 'two.py': 'def unrelated():\n    return 1\n'})
    result = briefing(intel, 'task', task='Update frobnicate for a USER-requested leaderboard')
    assert result['context']['relevance']['primary_files'] == ['one.py']
    assert 'two.py' not in result['context']['relevance']['selected_files']
    assert not intel.requirements
    assert 'No requirement-derived next product work' in result['markdown']
    assert 'leaderboard' in result['context']['task']['text']
    assert 'USER' in result['markdown']


@pytest.mark.parametrize('fixture', ['ml', 'scripts', 'mixed', 'readme', 'specification', 'backend', 'frontend'])
def test_universal_views_do_not_force_web_or_completed_work(fixture):
    intel = analyze(FIXTURES[fixture])
    md = briefing(intel)['markdown']
    if not intel.api_endpoints and not intel.api_consumers:
        assert 'No API or shared-type contract was detected' in md or intel.data_models
    assert 'No percentages are calculated.' in md
    assert 'NOT_IMPLEMENTED' not in md.replace('NOT_DETECTED is not proof of NOT_IMPLEMENTED', '').replace('NOT_DETECTED does not authorize claiming NOT_IMPLEMENTED', '')
    if fixture == 'ml':
        assert 'Dataset Loading' in md and 'Training' in md
        assert 'model.pth' in md
    if fixture == 'specification':
        assert 'NOT_DETECTED' in md
        assert 'No parsed source components' in md


def test_empty_snapshot_is_honest_unknown():
    result = briefing(analyze({}))
    assert result['context']['completeness']['documentation_coverage']['status'] == 'UNKNOWN'
    assert result['context']['completeness']['requirement_coverage']['status'] == 'UNKNOWN'
    assert 'NOT SPECIFIED' in result['markdown']


def test_typescript_properties_live_in_canonical_snapshot_not_view_parser():
    intel = analyze({'types.ts': 'export type Request = { readonly bookId: string; question?: string; };'})
    model = intel.data_models[0]
    assert model['fields'] == [{'name': 'bookId', 'annotation': 'string', 'optional': False}, {'name': 'question', 'annotation': 'string', 'optional': True}]
    assert model['field_extraction'] == 'flat_declared_properties_only'
    assert 'bookId' in briefing(intel)['markdown']


def test_nested_typescript_shapes_remain_unknown():
    intel = analyze({'types.ts': 'export interface Request { payload: { deep: string }; }'})
    assert 'fields' not in intel.data_models[0]
    assert 'fields were not retained' in briefing(intel)['markdown']


@pytest.mark.parametrize('state', [SnapshotStatus.STALE, 'no_commit'])
def test_direct_builder_refuses_unanchored_or_stale_snapshot(state):
    intel = analyze(FIXTURES['frontend'])
    if state == 'no_commit':
        intel.commit = ''
    else:
        intel.snapshot_status = state
    with pytest.raises(ValueError, match='must be refreshed'):
        briefing(intel)


def test_budget_omits_whole_records_but_preserves_boundaries_contracts_rules():
    intel = analyze(FIXTURES['bookos'])
    result = generate(intel, 18_000, options={'context_type': 'role', 'member': {'ownership': ['client'], 'do_not_touch': ['server', 'shared']}})
    assert result['context']['usable']
    assert len(result['markdown'].encode()) <= 18_000
    assert result['context']['completeness']['status'] == 'PARTIAL'
    assert result['context']['completeness']['budget_omitted_blocks'] > 0
    for term in ('POST /api/ask-book', 'AskRequest', 'Always preserve shared contracts', 'DO NOT TOUCH', 'Omitted record identifiers'):
        assert term.lower() in result['markdown'].lower()
    omitted = [o for o in result['context']['omission_manifest'] if o['category'] == 'context_budget']
    for item in omitted:
        assert item['record'] in result['markdown']
    assert not result['markdown'].endswith('CONTEXT TRUNCATED')


@pytest.mark.parametrize('budget', [0, 1, 80, 1024])
def test_impossible_budget_reports_unusable_incomplete(budget):
    result = generate(analyze(FIXTURES['bookos']), budget)
    assert len(result['markdown'].encode()) <= budget
    assert not result['context']['usable']
    assert result['context']['completeness']['status'] == 'INCOMPLETE'


def test_source_omissions_are_distinct_from_view_and_budget_exclusions():
    intel = analyze({'a.py': 'def main(): pass', 'b.py': 'def other(): pass'})
    intel.completeness.omitted_paths = ['b.py']
    intel.completeness.omission_reasons = {'b.py': 'file_size_limit'}
    intel.completeness.files_omitted = 1
    intel.completeness.status = 'PARTIAL'
    result = briefing(intel, 'role', member={'ownership': ['a.py']})
    categories = {o['category'] for o in result['context']['omission_manifest']}
    assert categories == {'snapshot_collection', 'view_relevance'}
    assert 'file_size_limit' in result['markdown']
    assert result['context']['completeness']['status'] == 'PARTIAL'


def test_redaction_and_markdown_injection_do_not_break_utf8_budget():
    token = 'private-value-unique'
    result = generate(analyze(FIXTURES['frontend']), 14_000, options={'context_type': 'ai_handoff', 'member': {'name': token, 'role': '<script>boom</script>', 'responsibilities': ['## Forged section']}, 'task': 'Use password=secret-value\n## Forged section', 'constraints': [token]}, known_secrets=(token,))
    encoded = json.dumps(result)
    assert token not in encoded and 'secret-value' not in encoded
    assert '<script>' not in result['markdown']
    assert '\n## Forged section' not in result['markdown']
    assert len(result['markdown'].encode()) <= 14_000


@pytest.mark.parametrize('path,scope,expected', [('client/a.ts', 'client/', True), ('clientish/a.ts', 'client', False), ('shared/a.ts', 'shared\\', True), ('client/a.ts', 'client/*.ts', True), ('a.ts', '.', True)])
def test_user_scope_matching_is_explicit(path, scope, expected):
    assert in_scope(path, scope) == expected


@pytest.mark.anyio
async def test_repeated_context_authorizes_each_request_without_scan(monkeypatch):
    intel = analyze(FIXTURES['bookos'])
    snapshots = loader(intel)
    monkeypatch.setattr(AnalysisService, 'analyze_intelligence', AsyncMock(side_effect=AssertionError('No analysis')))
    service = ContextService(snapshots)
    for view in ('project', 'role', 'task', 'ai_handoff'):
        response = await service.create(ContextRequest(owner='example', repo='project', branch='main', context_type=view))
        assert response['analysis']['metadata']['commit'] == 'commit-1'
    assert snapshots.github.commit.await_count == 4
    snapshots.github.file.assert_not_called()
    snapshots.github.tree_snapshot.assert_not_called()
    AnalysisService.analyze_intelligence.assert_not_called()


@pytest.mark.anyio
@pytest.mark.parametrize('state', ['missing', 'stale', 'changed', 'commit_mismatch', 'folder', 'version', 'wrong_store_identity'])
async def test_unavailable_snapshot_requires_explicit_refresh(state):
    intel = analyze(FIXTURES['backend'])
    if state == 'stale':
        intel.snapshot_status = SnapshotStatus.STALE
    if state == 'version':
        intel.analysis_version = 'old'
    snapshots = loader(None if state == 'missing' else intel)
    if state == 'changed':
        snapshots.github.commit.return_value = {'sha': 'new-head'}
    if state == 'wrong_store_identity':
        wrong = deepcopy(intel)
        wrong.repo = 'other'
        snapshots.store.load = lambda *args: wrong
    with pytest.raises(BatonError) as err:
        await snapshots.load('example', 'project', 'main', 'client' if state == 'folder' else '', 'wrong-commit' if state == 'commit_mismatch' else None)
    assert err.value.status_code == 409
    assert REFRESH_MESSAGE in err.value.detail
    snapshots.github.file.assert_not_called()
    snapshots.github.tree_snapshot.assert_not_called()


@pytest.mark.anyio
async def test_default_branch_resolution_and_partial_snapshot_preserved():
    intel = analyze(FIXTURES['backend'])
    intel.snapshot_status = SnapshotStatus.PARTIAL
    snapshots = loader(intel)
    value = await snapshots.load('EXAMPLE', 'PROJECT', '')
    assert value.snapshot_status == SnapshotStatus.PARTIAL
    assert briefing(value)['context']['completeness']['status'] == 'PARTIAL'
    snapshots.github.commit.assert_awaited_once_with('EXAMPLE', 'PROJECT', 'main')
    snapshots.github.repository.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize('http_status', [401, 403, 404, 409])
async def test_authorization_failure_prevents_snapshot_reuse(http_status):
    snapshots = loader(analyze(FIXTURES['frontend']))
    snapshots.github.commit.side_effect = BatonError('GitHub authorization/state failure', http_status)
    with pytest.raises(BatonError) as err:
        await snapshots.load('example', 'project', 'main')
    assert err.value.status_code == http_status
    if http_status == 409:
        assert REFRESH_MESSAGE in err.value.detail


def test_context_route_exposes_new_views_and_legacy_keys(monkeypatch):
    intel = analyze(FIXTURES['bookos'])
    monkeypatch.setattr(ContextSnapshotService, 'load', AsyncMock(return_value=intel))
    client = TestClient(app)
    request = {'owner': 'example', 'repo': 'project', 'branch': 'main', 'context_type': 'ai_handoff', 'member': {'role': 'Frontend Developer', 'ownership': ['client/']}, 'task': 'Inspect askBook'}
    result = client.post('/api/v1/context', json=request)
    assert result.status_code == 200
    assert {'analysis', 'markdown', 'estimated_tokens', 'omitted', 'context'} <= result.json().keys()
    assert result.json()['context']['identity']['context_type'] == 'ai_handoff'
    request['include_markdown'] = False
    structured = client.post('/api/v1/context', json=request).json()
    assert structured['markdown'] == '' and structured['estimated_tokens'] == 0
    request['context_type'] = 'invalid'
    assert client.post('/api/v1/context', json=request).status_code == 422


def test_route_small_budget_and_refresh_errors_are_actionable(monkeypatch):
    client = TestClient(app)
    request = {'owner': 'example', 'repo': 'project', 'branch': 'main', 'max_bytes': 1024}
    monkeypatch.setattr(ContextSnapshotService, 'load', AsyncMock(return_value=analyze(FIXTURES['frontend'])))
    assert client.post('/api/v1/context', json=request).status_code == 413
    monkeypatch.setattr(ContextSnapshotService, 'load', AsyncMock(side_effect=BatonError(REFRESH_MESSAGE, 409)))
    response = client.post('/api/v1/context', json=request)
    assert response.status_code == 409 and REFRESH_MESSAGE in response.json()['detail']


@pytest.mark.anyio
async def test_server_limit_applies_and_member_credentials_are_not_echoed(monkeypatch):
    monkeypatch.setattr(get_settings(), 'max_total_context_bytes', 14_000)
    token = 'secret-user-request-value'
    service = ContextService(loader(analyze(FIXTURES['frontend'])))
    response = await service.create(ContextRequest(owner='example', repo='project', branch='main', max_bytes=500_000, member={'name': token}), token)
    assert len(response['markdown'].encode()) <= 14_000
    assert token not in json.dumps(response)


@pytest.mark.anyio
async def test_new_request_token_cannot_leak_through_older_snapshot_projection():
    token = 'new-opaque-token-value'
    intel = analyze({'README.md': '# Notes\nOpaque author prose ' + token + '\n', token + '.py': 'def helper(): pass\n'})
    assert token in json.dumps(intel.to_legacy_analysis())
    response = await ContextService(loader(intel)).create(ContextRequest(owner='example', repo='project', branch='main'), token)
    assert token not in json.dumps(response)
