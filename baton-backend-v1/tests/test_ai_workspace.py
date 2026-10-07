"""Strict evidence selection, credentials, artifacts and branch isolation."""
from copy import deepcopy
from dataclasses import asdict
import json
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.intelligence.safety import sanitize_model
from app.intelligence.snapshot import MemorySnapshotStore
from app.main import app
from app.schemas.workspace import ArtifactRequest, ChatRequest, CompareRequest, EvidenceSelection, WorkspaceRequest
from app.services.ai_provider import GeminiProvider
from app.services.analysis_service import AnalysisService
from app.services.context_service import ContextService
from app.services.context_snapshot import ContextSnapshotService
from app.services.conversations import ConversationStore
from app.services.workspace_service import WorkspaceService
from tests.test_context_system import loader
from tests.test_intelligence import analyze, FIXTURES


@pytest.fixture
def anyio_backend(): return 'asyncio'


def request(cls=WorkspaceRequest, **options):
    return cls(owner='example', repo='project', branch='main', **options)


def service(intel=None):
    snapshots = loader(intel or analyze(FIXTURES['bookos']))
    provider = type('FakeProvider', (), {})()
    provider.select = AsyncMock()
    return WorkspaceService(ContextService(snapshots), provider, ConversationStore())


def choose_api(packet):
    return EvidenceSelection(status='grounded', evidence_ids=[next(r['id'] for r in packet['records'] if r['id'].startswith('11:') and ':api:' in r['id'])])


@pytest.mark.anyio
async def test_chat_renders_only_exact_canonical_evidence_no_analysis_calls(monkeypatch):
    workspace = service()
    workspace.provider.select.side_effect = choose_api
    monkeypatch.setattr(AnalysisService, 'analyze_intelligence', AsyncMock(side_effect=AssertionError('No rescans')))
    result = await workspace.chat(request(ChatRequest, message='What is the Ask Book API?'))
    assert result['status'] == 'grounded' and result['citations']
    assert 'POST /api/ask-book' in result['answer']
    assert result['citations'][0]['text'] in result['answer']
    assert result['identity']['commit'] == 'commit-1'
    workspace.contexts.snapshots.github.file.assert_not_called()
    workspace.contexts.snapshots.github.tree_snapshot.assert_not_called()
    AnalysisService.analyze_intelligence.assert_not_called()


@pytest.mark.anyio
@pytest.mark.parametrize('selection', [
    {'status': 'grounded', 'evidence_ids': ['invented:outside-repo']},
    {'status': 'grounded', 'evidence_ids': []},
    {'status': 'unknown', 'evidence_ids': ['invented:outside-repo']},
    {'status': 'out_of_scope', 'answer': 'An invented feature is implemented'},
    {'status': 'grounded', 'evidence_ids': [], 'extra_secret': 'fixture-private-value'},
])
async def test_fabricated_or_unstructured_answers_fail_closed(selection):
    workspace = service()
    workspace.provider.select.return_value = selection
    with pytest.raises(BatonError) as err:
        await workspace.chat(request(ChatRequest, message='Explain the repository'))
    assert err.value.status_code == 502
    assert not workspace.conversations.entries


@pytest.mark.anyio
@pytest.mark.parametrize('status', ['unknown', 'out_of_scope'])
async def test_unknown_and_outside_scope_are_explicit_not_general_chat(status):
    workspace = service()
    workspace.provider.select.return_value = EvidenceSelection(status=status)
    result = await workspace.chat(request(ChatRequest, message='Tell me about an unrelated project'))
    assert result['status'] == status and not result['citations']
    assert ('UNKNOWN' in result['answer']) if status == 'unknown' else ('outside the connected repository' in result['answer'])


@pytest.mark.anyio
async def test_protected_contract_can_be_read_but_action_cannot_target_it():
    workspace = service()
    def select(packet):
        reference = next(r for r in packet['records'] if ':api:' in r['id'])
        return EvidenceSelection(status='grounded', evidence_ids=[reference['id']], actions=[{'kind': 'inspect', 'evidence_id': reference['id'], 'target_path': 'server/routes.ts'}])
    workspace.provider.select.side_effect = select
    with pytest.raises(BatonError, match='outside supplied ownership'):
        await workspace.chat(request(ChatRequest, message='Inspect the API', member={'ownership': ['client/'], 'do_not_touch': ['server/']}))
    workspace.provider.select.side_effect = choose_api
    response = await workspace.chat(request(ChatRequest, message='Explain the API', member={'ownership': ['client/'], 'do_not_touch': ['server/']}))
    assert 'server/routes.ts' in response['answer']


@pytest.mark.anyio
async def test_bounded_actions_require_owned_paths_and_selected_evidence():
    workspace = service()
    def select(packet):
        reference = next(r for r in packet['records'] if ':api:' in r['id'])
        return EvidenceSelection(status='grounded', evidence_ids=[reference['id']], actions=[{'kind': 'verify', 'evidence_id': reference['id'], 'target_path': 'server/routes.ts'}])
    workspace.provider.select.side_effect = select
    result = await workspace.chat(request(ChatRequest, message='Verify API declarations', member={'ownership': ['server/']}))
    assert result['actions'][0]['target_path'] == 'server/routes.ts'
    assert 'not an executed change' in result['actions'][0]['text']


@pytest.mark.anyio
async def test_conversation_followups_are_server_bound_and_bounded():
    workspace = service()
    workspace.provider.select.side_effect = choose_api
    first = await workspace.chat(request(ChatRequest, message='What is the API?'), 'user-one')
    second = await workspace.chat(request(ChatRequest, message='Which source defines it?', conversation_id=first['conversation_id'], revision=first['revision']), 'user-one')
    assert second['revision'] == 2
    assert workspace.provider.select.call_args.args[0]['previous_user_questions'] == ['What is the API?']
    with pytest.raises(BatonError, match='authorization changed'):
        await workspace.chat(request(ChatRequest, message='Reuse someone else\'s chat', conversation_id=first['conversation_id'], revision=first['revision']), 'user-two')
    with pytest.raises(BatonError, match='role or authorization changed'):
        await workspace.chat(request(ChatRequest, message='Change duty', conversation_id=first['conversation_id'], revision=first['revision'], member={'ownership': ['server/']}), 'user-one')


def test_conversation_eviction_revision_limits_and_expiration():
    store = ConversationStore(capacity=1, ttl=3600)
    first = store.append(None, 'owner', 0, 'q', {'evidence_ids': []})
    with pytest.raises(BatonError, match='changed while answering'):
        store.append(first, 'owner', 0, 'q', {})
    store.append(None, 'owner', 0, 'q', {})
    with pytest.raises(BatonError, match='expired'):
        store.load(first, 'owner')
    expired = ConversationStore(ttl=-1)
    identifier = expired.append(None, 'owner', 0, 'q', {})
    with pytest.raises(BatonError, match='expired'):
        expired.load(identifier, 'owner')
    store = ConversationStore()
    identifier = None
    for revision in range(20): identifier = store.append(identifier, 'owner', revision, 'q', {})
    with pytest.raises(BatonError, match='limit reached'):
        store.append(identifier, 'owner', 20, 'q', {})


@pytest.mark.anyio
@pytest.mark.parametrize('kind', ['context', 'handoff', 'prd', 'implementation_plan', 'review', 'prompt'])
async def test_artifacts_reuse_same_context_without_provider_or_new_facts(kind):
    workspace = service()
    result = await workspace.artifact(request(ArtifactRequest, artifact_type=kind, task='Inspect existing askBook integration'))
    assert result['filename'].endswith('.md')
    assert result['identity']['commit'] == 'commit-1'
    assert result['sha256'] and 'commit-1' in result['content']
    assert 'Inspect existing askBook integration' in result['content']
    assert 'leaderboard' not in result['content']
    if kind == 'prd': assert 'DOCUMENTED' in result['content'] and 'PARTIALLY' in result['content']
    if kind == 'prompt': assert 'example/project repository' in result['content']
    workspace.provider.select.assert_not_called()
    workspace.contexts.snapshots.github.file.assert_not_called()


@pytest.mark.anyio
async def test_prompt_requires_user_task_instead_of_inventing_one():
    with pytest.raises(BatonError, match='explicit task'):
        await service().artifact(request(ArtifactRequest, artifact_type='prompt'))


@pytest.mark.anyio
async def test_branch_comparison_uses_authorized_exact_snapshots_and_protection():
    before = analyze(FIXTURES['bookos'])
    after = deepcopy(before)
    after.branch, after.commit = 'feature', 'commit-2'
    next(f for f in after.file_tree if f['path'] == 'server/routes.ts')['sha'] = 'changed-blob'
    after.api_endpoints[0].response_shape = 'ChangedResponse'
    store = MemorySnapshotStore(); store.save(before); store.save(after)
    snapshots = ContextSnapshotService(store=store)
    snapshots.github.commit = AsyncMock(side_effect=lambda owner, repo, branch: {'sha': 'commit-2' if branch == 'feature' else 'commit-1'})
    snapshots.github.file = AsyncMock(side_effect=AssertionError('No raw files'))
    workspace = WorkspaceService(ContextService(snapshots))
    result = await workspace.compare(request(CompareRequest, compare_branch='feature', member={'ownership': ['client/'], 'do_not_touch': ['server/']}))
    assert result['before']['commit'] == 'commit-1' and result['after']['commit'] == 'commit-2'
    assert result['changed_blob_paths'] == ['server/routes.ts']
    assert result['protected_changes'] == ['server/routes.ts'] and result['contract_changes']
    assert snapshots.github.commit.await_count == 2
    snapshots.github.file.assert_not_called()


@pytest.mark.anyio
async def test_comparison_missing_branch_does_not_analyze_or_fallback():
    workspace = service()
    workspace.contexts.snapshots.github.commit.side_effect = lambda owner, repo, branch: {'sha': 'unavailable' if branch == 'other' else 'commit-1'}
    with pytest.raises(BatonError) as error:
        await workspace.compare(request(CompareRequest, compare_branch='other'))
    assert error.value.status_code == 409


@pytest.mark.anyio
async def test_configured_secrets_never_reach_provider_packets_chat_artifacts(monkeypatch):
    secret = 'synthetic-provider-credential-for-tests'
    monkeypatch.setattr(get_settings(), 'gemini_api_key', SecretStr(secret))
    workspace = service(analyze({'README.md': '# Intent\n' + secret + '\n', 'main.py': 'def main(): pass'}))
    workspace.provider.select.return_value = EvidenceSelection(status='unknown')
    response = await workspace.chat(request(ChatRequest, message='Inspect ' + secret, task='USER task ' + secret))
    packet = workspace.provider.select.call_args.args[0]
    assert secret not in json.dumps(packet) and secret not in json.dumps(response)
    assert secret not in json.dumps(workspace.conversations.entries)
    artifact = await workspace.artifact(request(ArtifactRequest, artifact_type='context', task=secret))
    assert secret not in json.dumps(artifact)
    assert secret not in repr(get_settings()) and secret not in json.dumps(get_settings().model_dump())


def test_canonical_redaction_preserves_types_and_removes_secret_paths():
    secret = 'synthetic-private-path'
    intel = analyze({secret + '.py': 'def main(): pass'})
    safe = sanitize_model(intel, (secret,))
    assert secret not in json.dumps(asdict(safe))
    assert safe.snapshot_status == intel.snapshot_status
    assert intel.file_tree[0]['path'] == secret + '.py'


def test_snapshot_storage_cannot_retain_configured_provider_secret(monkeypatch):
    secret = 'synthetic-storage-provider-credential'
    monkeypatch.setattr(get_settings(), 'gemini_api_key', SecretStr(secret))
    intel = analyze({secret + '.py': 'def main(): pass'})
    store = MemorySnapshotStore(); store.save(intel)
    assert secret not in json.dumps([asdict(value) for value in store.entries.values()])


def configure_provider(monkeypatch):
    monkeypatch.setattr(get_settings(), 'gemini_api_key', SecretStr('synthetic-provider-header'))
    monkeypatch.setattr(get_settings(), 'gemini_model', 'fixture-model')


@pytest.mark.anyio
async def test_gemini_key_is_header_only_and_schema_has_no_freeform_answer(monkeypatch):
    configure_provider(monkeypatch)
    original = httpx.AsyncClient
    requests = []
    def respond(req):
        requests.append(req)
        return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '{"status":"unknown","evidence_ids":[],"actions":[]}'}]}}]})
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs))
    result = await GeminiProvider().select({'question': 'Inspect canonical evidence', 'records': []})
    assert result.status == 'unknown'
    sent = requests[0]
    assert sent.headers['x-goog-api-key'] == get_settings().gemini_api_key.get_secret_value()
    assert 'synthetic-provider-header' not in str(sent.url) and 'synthetic-provider-header' not in sent.content.decode()
    payload = json.loads(sent.content)
    assert 'answer' not in payload['generationConfig']['responseJsonSchema']['properties']
    assert 'tools' not in payload


@pytest.mark.anyio
@pytest.mark.parametrize('failure', ['error', 'malformed', 'truncated', 'timeout', 'oversized'])
async def test_provider_failures_never_echo_upstream_secret_payloads(monkeypatch, failure):
    configure_provider(monkeypatch)
    original = httpx.AsyncClient
    def respond(req):
        if failure == 'timeout': raise httpx.ReadTimeout('synthetic-provider-header', request=req)
        if failure == 'error': return httpx.Response(401, json={'error': 'synthetic-provider-header'})
        if failure == 'oversized': return httpx.Response(200, content=b'x' * 100001)
        if failure == 'truncated': return httpx.Response(200, json={'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': [{'text': 'synthetic-provider-header'}]}}]})
        return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'synthetic-provider-header'}]}}]})
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs))
    with pytest.raises(BatonError) as error:
        await GeminiProvider().select({'records': []})
    assert 'synthetic-provider-header' not in error.value.detail
    assert error.value.status_code in {502, 504}


@pytest.mark.anyio
async def test_missing_provider_config_is_explicit_not_simulated_chat(monkeypatch):
    monkeypatch.setattr(get_settings(), 'gemini_api_key', SecretStr(''))
    with pytest.raises(BatonError) as error:
        await GeminiProvider().select({})
    assert error.value.status_code == 503


def test_chat_requires_operator_auth_and_validation_does_not_echo_inputs(monkeypatch):
    client = TestClient(app, headers={'X-GitHub-Token': 'fixture-credential'})
    monkeypatch.setattr(get_settings(), 'baton_access_key', '')
    assert client.post('/api/v1/workspace/chat', json=request(ChatRequest, message='Inspect').model_dump()).status_code == 503
    monkeypatch.setattr(get_settings(), 'baton_access_key', 'synthetic-operator-key')
    assert client.post('/api/v1/workspace/chat', json=request(ChatRequest, message='Inspect').model_dump()).status_code == 401
    bad = client.post('/api/v1/workspace/chat', headers={'X-Baton-Key': 'synthetic-operator-key'}, json={'message': 'synthetic-operator-key', 'gemini_api_key': 'synthetic-operator-key'})
    assert bad.status_code == 422 and 'synthetic-operator-key' not in bad.text


def test_all_json_responses_redact_configured_provider_key(monkeypatch):
    secret = 'synthetic-global-provider-credential'
    monkeypatch.setattr(get_settings(), 'gemini_api_key', SecretStr(secret))
    monkeypatch.setattr(ContextSnapshotService, 'load', AsyncMock(return_value=analyze({secret + '.py': 'def main(): pass'})))
    response = TestClient(app, headers={'X-GitHub-Token': 'fixture-credential'}).post('/api/v1/context', json={'owner': 'example', 'repo': 'project', 'branch': 'main'})
    assert response.status_code == 200 and secret not in response.text


def test_frontend_has_no_provider_key_or_public_operator_key_binding():
    from pathlib import Path
    source = Path(__file__).parents[2] / 'baton-frontend/src'
    files = [p for p in source.rglob('*') if p.suffix in {'.ts', '.tsx', '.css'}]
    text = '\n'.join(p.read_text(encoding='utf-8') for p in files)
    assert 'VITE_GEMINI' not in text and 'VITE_BATON_ACCESS_KEY' not in text
    assert 'generativelanguage.googleapis.com' not in text
    assert 'console.error' not in (source / 'lib/api/batonApi.ts').read_text()
