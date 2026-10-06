"""Wire-level authentication, quota evidence and canonical request counts."""
import asyncio
import base64
from collections import Counter
from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.intelligence.snapshot import MemorySnapshotStore
from app.services.github_service import GitHubService
from app.services.analysis_service import AnalysisService
from app.services.context_snapshot import ContextSnapshotService
from app.services.context_service import ContextService
from app.schemas.context import ContextRequest
from app.intelligence.models import SnapshotStatus


@pytest.fixture
def anyio_backend(): return 'asyncio'


@pytest.fixture
def wire(monkeypatch):
    monkeypatch.setattr(get_settings(), 'github_token', '')
    monkeypatch.setattr(get_settings(), 'baton_access_key', '')
    calls = []
    async def respond(self, method, path, **kwargs):
        calls.append((path, kwargs.get('headers', {}), kwargs.get('params')))
        await asyncio.sleep(0.001)
        headers = {'x-ratelimit-limit': '5000', 'x-ratelimit-remaining': '4990',
                   'x-ratelimit-used': '10', 'x-ratelimit-reset': '2000000000'}
        if path == '/user': data = {'login': 'must-not-leave-service', 'email': 'private@example.org'}
        elif '/commits/' in path: data = {'sha': 'head-' + path.rsplit('/', 1)[-1]}
        elif '/git/trees/' in path:
            data = {'tree': [{'type': 'blob', 'path': p, 'size': 4} for p in ['main.py', 'README.md', 'main.py']]}
        elif '/contents/' in path:
            data = {'type': 'file', 'path': path.split('/contents/')[1], 'size': 4,
                    'content': base64.b64encode(b'pass').decode()}
        elif path.endswith('/branches'): data = [{'name': 'main', 'commit': {'sha': 'head-main'}}]
        else: data = {'default_branch': 'main', 'visibility': 'public'}
        return httpx.Response(200, headers=headers, json=data)
    monkeypatch.setattr(httpx.AsyncClient, 'request', respond)
    return calls


def test_fastapi_request_token_reaches_all_analysis_wire_requests(wire, monkeypatch):
    monkeypatch.setattr(get_settings(), 'github_token', 'server-canary')
    response = TestClient(app).post('/api/v1/analysis/repository',
        json={'owner': 'wire', 'repo': 'forward', 'branch': 'main'},
        headers={'X-GitHub-Token': ' request-canary '})
    assert response.status_code == 200
    assert len(wire) == 4  # HEAD + tree + two distinct files, despite duplicate tree entry
    assert all(headers.get('Authorization') == 'Bearer request-canary' for _, headers, _ in wire)
    assert 'canary' not in response.text


@pytest.mark.anyio
async def test_public_and_authenticated_headers_and_token_scoped_cache(wire):
    await GitHubService().commit('o', 'r', 'main')
    await GitHubService('first').commit('o', 'r', 'main')
    await GitHubService('first').commit('o', 'r', 'main')
    await GitHubService('second').commit('o', 'r', 'main')
    assert len(wire) == 3
    assert 'Authorization' not in wire[0][1]
    assert wire[1][1]['Authorization'] == 'Bearer first'
    assert wire[2][1]['Authorization'] == 'Bearer second'


@pytest.mark.anyio
async def test_head_expiry_and_explicit_refresh_revalidate(wire, monkeypatch):
    service = GitHubService('first')
    await service.commit('o', 'r', 'main')
    await service.commit('o', 'r', 'main', fresh=True)
    assert len(wire) == 2
    monkeypatch.setattr(service, 'observation_ttl', -1)
    await service.commit('o', 'r', 'main', fresh=True)
    await service.commit('o', 'r', 'main')
    assert len(wire) == 4


@pytest.mark.anyio
async def test_file_cache_is_request_local_and_commit_scoped(wire):
    service = GitHubService('first')
    first = await service.file('o', 'r', 'sha', 'main.py')
    first['content'] = 'mutated'
    second = await service.file('o', 'r', 'sha', 'main.py')
    assert second['content'] == 'pass' and len(wire) == 1
    await service.file('o', 'r', 'other-sha', 'main.py')
    await GitHubService('first').file('o', 'r', 'sha', 'main.py')
    assert len(wire) == 3


@pytest.mark.anyio
async def test_concurrent_analysis_single_collection_snapshot_reads_zero_github(wire):
    store = MemorySnapshotStore()
    services = [AnalysisService('first', store) for _ in range(3)]
    results = await asyncio.gather(*(s.analyze_intelligence('o', 'r', 'main') for s in services))
    assert len(wire) == 4 and len({r.generated for r in results}) == 1
    assert Counter(p for p, _, _ in wire).most_common(1)[0][1] == 1
    await AnalysisService('first', store).analyze_intelligence('o', 'r', 'main')
    contexts = ContextService(ContextSnapshotService('first', store))
    req = ContextRequest(owner='o', repo='r', branch='main')
    await contexts.create(req); await contexts.create(req)
    assert len(wire) == 4  # no HEAD/tree/files for cached snapshot consumers
    await AnalysisService('first', store).analyze_intelligence('o', 'r', 'main', force_refresh=True)
    assert len(wire) == 7  # same pinned commit's tree is immutable and reused
    await AnalysisService('first', store).analyze_intelligence('o', 'r', 'feature')
    assert len(wire) == 11


def test_access_check_acceptance_and_cached_safe_metadata(wire):
    client = TestClient(app)
    for _ in range(2):
        response = client.get('/api/v1/github/access', headers={'X-GitHub-Token': 'request-canary'})
        assert response.status_code == 200
        data = response.json()
        assert data['authenticated'] and data['token_source'] == 'request'
        assert data['rate_limit'] == {'limit': 5000, 'remaining': 4990, 'used': 10, 'reset_at': 2000000000}
        assert 'canary' not in response.text and 'private@example.org' not in response.text
    assert len(wire) == 1


@pytest.mark.anyio
async def test_concurrent_access_checks_use_one_safe_identity_request(wire):
    results = await asyncio.gather(*(GitHubService('first').access() for _ in range(3)))
    assert all(r['authenticated'] for r in results) and len(wire) == 1


@pytest.mark.anyio
async def test_refresh_racing_cache_read_still_refreshes(wire):
    store = MemorySnapshotStore()
    first = await AnalysisService('first', store).analyze_intelligence('o', 'r', 'main')
    ordinary = AnalysisService('first', store)
    refresh = AnalysisService('first', store)
    cached, changed = await asyncio.gather(ordinary.analyze_intelligence('o', 'r', 'main'),
                                         refresh.analyze_intelligence('o', 'r', 'main', force_refresh=True))
    assert cached.generated == first.generated
    assert changed.generated != first.generated and len(wire) == 7


@pytest.mark.anyio
async def test_refresh_racing_first_collection_does_not_scan_twice(wire):
    store = MemorySnapshotStore()
    ordinary, refresh = AnalysisService('first', store), AnalysisService('first', store)
    a, b = await asyncio.gather(ordinary.analyze_intelligence('o', 'r', 'main'),
                                refresh.analyze_intelligence('o', 'r', 'main', force_refresh=True))
    assert a.generated == b.generated and len(wire) == 4


@pytest.mark.anyio
async def test_invalid_snapshot_is_collected_again_instead_of_reused(wire):
    store = MemorySnapshotStore()
    first = await AnalysisService('first', store).analyze_intelligence('o', 'r', 'main')
    key = next(iter(store.entries))
    store.entries[key].snapshot_status = SnapshotStatus.STALE
    second = await AnalysisService('first', store).analyze_intelligence('o', 'r', 'main')
    assert second.generated != first.generated and second.snapshot_status != SnapshotStatus.STALE
    assert len(wire) == 6  # reuses authorized HEAD/tree, reads the two files once


@pytest.mark.parametrize('status,headers,message,code,kind', [
    (401, {}, 'Bad credentials', 'github_authentication_failure', None),
    (403, {'x-ratelimit-remaining':'100'}, 'Resource not accessible', 'github_permission_failure', None),
    (403, {'x-ratelimit-remaining':'0','x-ratelimit-limit':'60','x-ratelimit-reset':'2000000000'}, 'API rate limit exceeded', 'github_rate_limit', 'primary'),
    (403, {'x-ratelimit-remaining':'0','x-ratelimit-limit':'5000','x-ratelimit-reset':'2000000000'}, 'API rate limit exceeded', 'github_rate_limit', 'primary'),
    (403, {'x-ratelimit-remaining':'4999','retry-after':'90'}, 'secondary rate limit', 'github_rate_limit', 'secondary'),
    (403, {}, 'API rate limit exceeded', 'github_rate_limit', 'unknown'),
    (429, {}, 'Too many requests', 'github_rate_limit', 'unknown'),
    (404, {}, 'Not found', 'github_not_found', None),
])
@pytest.mark.anyio
async def test_quota_classification_metadata_and_backoff(monkeypatch, status, headers, message, code, kind):
    monkeypatch.setattr(get_settings(), 'github_token', '')
    async def remote(*args, **kwargs):
        return httpx.Response(status, headers=headers, json={'message': message + ' ghp_canary_secret'})
    with patch('httpx.AsyncClient.request', new=remote):
        with pytest.raises(BatonError) as failure:
            await GitHubService('request-canary').repository('o', 'r')
    error = failure.value
    assert error.code == code and 'canary' not in error.detail
    if kind:
        assert error.metadata['rate_limit_kind'] == kind
        assert error.metadata['upstream_status'] == status
        if kind == 'primary':
            assert error.metadata['rate_limit']['limit'] == int(headers['x-ratelimit-limit'])
            assert error.metadata['rate_limit']['remaining'] == 0
        with patch('httpx.AsyncClient.request', side_effect=AssertionError('backoff must not contact GitHub')):
            with pytest.raises(BatonError) as second:
                await GitHubService('request-canary').commit('o', 'r', 'main', fresh=True)
        assert second.value.code == 'github_rate_limit'


@pytest.mark.parametrize('retry,expected', [('120',120),('nonsense',None),('-1',0),('Tue, 01 Jan 2030 00:00:00 GMT','future')])
def test_rate_headers_and_retry_after_parsing(retry, expected):
    metadata = GitHubService.response_metadata(httpx.Response(429, headers={'retry-after':retry,'x-ratelimit-limit':'bad','x-ratelimit-used':'3'}))
    assert metadata['rate_limit']['limit'] is None
    assert metadata['rate_limit']['used'] == 3
    assert metadata['retry_after'] > 0 if expected == 'future' else metadata['retry_after'] == expected


@pytest.mark.anyio
async def test_timeout_mapping(monkeypatch):
    async def remote(*args, **kwargs): raise httpx.ReadTimeout('secret-canary')
    with patch('httpx.AsyncClient.request', new=remote):
        with pytest.raises(BatonError) as error:
            await GitHubService('first').request('GET', '/user')
    assert error.value.code == 'github_timeout' and error.value.status_code == 504
    assert 'canary' not in error.value.detail
