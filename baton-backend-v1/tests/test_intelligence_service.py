import json
from dataclasses import asdict
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.intelligence.snapshot import MemorySnapshotStore
from app.intelligence.models import SnapshotStatus
from app.main import app
from app.services.analysis_service import AnalysisService
from app.services.github_service import GitHubService


@pytest.fixture
def anyio_backend():
    return 'asyncio'


def service_for(contents, commit='commit-sha', **tree_options):
    service = AnalysisService(store=MemorySnapshotStore())
    service.github.commit = AsyncMock(return_value={'sha': commit})
    service.github.repository = AsyncMock(return_value={'default_branch': 'main'})
    service.github.tree_snapshot = AsyncMock(return_value={
        'sha': 'tree-sha-not-a-commit',
        'tree': [{'path': p, 'type': 'blob', 'sha': 'blob-sha', 'size': len(t.encode())} for p, t in contents.items()],
        **tree_options,
    })
    async def file(owner, repo, ref, path):
        return {'path': path, 'content': contents[path]}
    service.github.file = AsyncMock(side_effect=file)
    return service


@pytest.mark.anyio
async def test_commit_pinned_reads_and_cache_reuse_authorize_each_request():
    service = service_for({'README.md': '# Overview', 'main.py': 'def main(): pass'})
    first = await service.analyze_intelligence('o', 'r', 'main')
    second = await service.analyze_intelligence('o', 'r', 'main')
    assert first == second and first.commit == 'commit-sha'
    assert service.github.commit.await_count == 2
    assert service.github.tree_snapshot.await_count == 1
    assert service.github.file.await_count == 2
    service.github.tree_snapshot.assert_awaited_once_with('o', 'r', 'commit-sha')
    assert all(call.args[2] == 'commit-sha' for call in service.github.file.await_args_list)
    assert {call.args[3] for call in service.github.file.await_args_list} == {'README.md', 'main.py'}


@pytest.mark.anyio
async def test_cached_private_repository_does_not_bypass_authorization():
    service = service_for({'main.py': 'pass'})
    await service.analyze_intelligence('o', 'r', 'main')
    service.github.commit.side_effect = BatonError('GitHub request failed', 404)
    with pytest.raises(BatonError):
        await service.analyze_intelligence('o', 'r', 'main')
    assert service.github.tree_snapshot.await_count == 1


@pytest.mark.anyio
async def test_folder_scope_not_reused_for_whole_repo():
    service = service_for({'client/App.tsx': "import React from 'react';", 'server/main.py': 'from fastapi import FastAPI'})
    folder = await service.analyze_intelligence('o', 'r', 'main', '/client/')
    whole = await service.analyze_intelligence('o', 'r', 'main')
    assert folder.project_root == 'client'
    assert len(folder.file_tree) == 1
    assert len(whole.file_tree) == 2
    assert len(service.store.metadata()) == 2


@pytest.mark.anyio
async def test_changed_head_reanalyzes_without_stale_facts():
    service = service_for({'main.py': 'def first(): pass'})
    first = await service.analyze_intelligence('o', 'r', 'main')
    service.github.commit.return_value = {'sha': 'new-commit'}
    service.github.file.side_effect = None
    service.github.file.return_value = {'content': 'def second(): pass'}
    second = await service.analyze_intelligence('o', 'r', 'main')
    assert first.commit != second.commit
    assert 'changed' in ' '.join(second.analysis_warnings)
    assert second.parsed_files[0].symbols[0]['name'] == 'second'
    assert service.github.tree_snapshot.await_count == 2


@pytest.mark.anyio
async def test_resolve_default_branch_and_no_commit_repository():
    service = service_for({})
    await service.analyze_intelligence('o', 'r', '')
    service.github.commit.assert_awaited_once_with('o', 'r', 'main')
    service.github.commit.side_effect = BatonError('GitHub request failed', 409)
    intel = await service.analyze_intelligence('o', 'empty', 'main')
    assert intel.commit is None and intel.snapshot_status == SnapshotStatus.PARTIAL
    assert not service.store.exists('o', 'empty', 'main', None)


@pytest.mark.anyio
async def test_document_first_collection_and_all_limits(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, 'max_files_per_analysis', 2)
    monkeypatch.setattr(settings, 'max_file_size_bytes', 100)
    monkeypatch.setattr(settings, 'max_total_context_bytes', 50)
    service = service_for({
        'a.py': 'x' * 40, 'README.md': '# Project intent',
        'big.py': 'x' * 101, 'small.py': 'pass', 'last.py': 'pass',
        'node_modules/file.js': 'ignored', '.env': 'SECRET=excluded', 'model.bin': 'binary',
    })
    intel = await service.analyze_intelligence('o', 'r', 'main')
    assert service.github.file.await_args_list[0].args[3] == 'README.md'
    reasons = intel.completeness.omission_reasons
    assert reasons['a.py'] == 'total_byte_limit'
    assert reasons['big.py'] == 'file_size_limit'
    assert reasons['small.py'] == 'file_count_limit'
    assert reasons['node_modules/file.js'] == 'filtered_or_binary'
    assert reasons['.env'] == 'sensitive_file'
    assert reasons['model.bin'] == 'filtered_or_binary'
    assert len(intel.file_tree) == 8
    assert service.github.file.await_count == 2
    assert intel.completeness.files_fully_analyzed + intel.completeness.files_omitted == 8


@pytest.mark.anyio
async def test_post_decode_byte_limit_and_failed_read_recording(monkeypatch):
    monkeypatch.setattr(get_settings(), 'max_total_context_bytes', 10)
    service = service_for({'a.py': 'pass', 'b.py': 'pass'})
    service.github.file.side_effect = [{'content': '界' * 8}, BatonError('Binary files are not supported', 400)]
    intel = await service.analyze_intelligence('o', 'r', 'main')
    assert intel.completeness.omission_reasons == {'a.py': 'total_byte_limit', 'b.py': 'unreadable_file'}


@pytest.mark.anyio
async def test_auth_failure_aborts_without_caching():
    service = service_for({'main.py': 'pass'})
    service.github.file.side_effect = BatonError('GitHub request failed', 403)
    with pytest.raises(BatonError):
        await service.analyze_intelligence('o', 'r', 'main')
    assert not service.store.metadata()


@pytest.mark.anyio
async def test_tree_truncation_is_explicit():
    service = service_for({'main.py': 'pass'}, truncated=True)
    intel = await service.analyze_intelligence('o', 'r', 'main')
    assert intel.completeness.tree_truncated
    assert intel.snapshot_status == SnapshotStatus.PARTIAL
    assert any('truncated' in w for w in intel.analysis_warnings)


@pytest.mark.anyio
async def test_request_and_environment_tokens_removed_before_findings(monkeypatch):
    monkeypatch.setattr(get_settings(), 'github_token', 'env-pat-canary')
    service = service_for({'README.md': '# Features\n- Preserve request-pat-canary and env-pat-canary.\n', 'main.py': '# TODO request-pat-canary\n'})
    service.github.token = 'request-pat-canary'
    intel = await service.analyze_intelligence('o', 'r', 'main')
    for payload in (asdict(intel), asdict(service.store.load('o', 'r', 'main', 'commit-sha'))):
        encoded = json.dumps(payload, default=str)
        assert 'request-pat-canary' not in encoded
        assert 'env-pat-canary' not in encoded


@pytest.mark.anyio
async def test_github_error_does_not_echo_remote_token(monkeypatch):
    import httpx
    async def remote_error(*args, **kwargs):
        return httpx.Response(403, json={'message': 'token secret-canary'}, request=httpx.Request('GET', 'https://api.github.com'))
    monkeypatch.setattr(httpx.AsyncClient, 'request', remote_error)
    with pytest.raises(BatonError) as caught:
        await GitHubService('secret-canary').repository('o', 'r')
    assert 'secret-canary' not in caught.value.detail


def test_existing_routes_consume_canonical_projection(monkeypatch):
    from app.intelligence.pipeline import run
    intel = run([{'path': 'main.py', 'type': 'blob'}], {'main.py': "@app.get('/health')\ndef health(): return {}"}, {'owner': 'o', 'repo': 'r', 'branch': 'main', 'commit': 'commit'}, [])
    monkeypatch.setattr(AnalysisService, 'analyze_intelligence', AsyncMock(return_value=intel))
    from app.services.context_snapshot import ContextSnapshotService
    monkeypatch.setattr(ContextSnapshotService, 'load', AsyncMock(return_value=intel))
    client = TestClient(app, headers={'X-GitHub-Token': 'fixture-credential'})
    request = {'owner': 'o', 'repo': 'r', 'branch': 'main'}
    for route in ('/api/v1/analysis/repository', '/api/v1/analysis/folder'):
        response = client.post(route, json=request)
        assert response.status_code == 200
        assert response.json()['routes'] == ['main.py: GET /health']
    response = client.post('/api/v1/context', json=request)
    assert response.status_code == 200
    assert response.json()['analysis']['metadata']['commit'] == 'commit'
    assert '/health' in response.json()['markdown']
