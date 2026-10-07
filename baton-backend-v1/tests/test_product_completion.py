"""Regressions for disconnected product surfaces and truthful comparison outcomes."""
import asyncio
from unittest.mock import AsyncMock
import pytest
from app.core.exceptions import BatonError
from app.services.conflict_service import detect
from app.services.integration_service import compare
from app.services.conversations import ConversationStore
from app.services.github_service import GitHubService
from app.services.prompt_service import create
from app.schemas.prompt import PromptRequest


def test_inventory_duplicates_are_not_cross_branch_changes():
    assert detect([], {'main': ['src/app.ts', 'src/app.ts']})['conflict_count'] == 0
    result = detect([], {'main': ['src/app.ts'], 'feature': ['src/app.ts']})
    assert result['conflict_count'] == 1
    assert 'inventories' in result['conflicts'][0]['reason']
    assert 'have not been established' in result['conflicts'][0]['reason']


@pytest.mark.parametrize('canonical', [False, True])
def test_empty_contracts_do_not_prove_compatibility(canonical):
    payload = {'canonical_api': {'consumers': [], 'endpoints': []}} if canonical else {}
    result = compare(payload, payload)
    assert result['compatible'] is None
    assert result['evidence_status'] == 'insufficient'


def test_explicit_methods_must_match():
    assert compare({'api_calls': ['POST /users']}, {'routes': ['GET /users']})['compatible'] is False


def test_manual_prompt_identifies_repository_and_unverified_inputs():
    result = create(PromptRequest(task='Fix parser', context='Operator supplied description', repository='example/parser'))
    assert 'example/parser' in result['prompt']
    assert 'USER_PROVIDED' in result['prompt']
    assert 'Baton repository' not in result['prompt']


def test_expired_conversation_is_not_a_snapshot_error():
    store = ConversationStore()
    with pytest.raises(BatonError) as failure:
        store.load('missing', 'binding')
    assert failure.value.code == 'conversation_expired'
    assert failure.value.status_code == 409


@pytest.mark.parametrize('path', ['../secret', '/src/main.py', 'src/../main.py', '.env', 'nested/.env.production', 'keys/private.pem', 'src\\secret'])
def test_generic_source_blocks_invalid_and_secret_paths_without_network(path):
    service = GitHubService('')
    service.request = AsyncMock()
    with pytest.raises(BatonError):
        asyncio.run(service.file('example', 'project', 'commit', path))
    service.request.assert_not_called()


def test_repository_scope_cannot_change_github_endpoint():
    service = GitHubService('')
    service.observed = AsyncMock()
    with pytest.raises(BatonError):
        asyncio.run(service.branches('example/../other', 'project'))
    service.observed.assert_not_called()


def test_analysis_can_still_collect_sanitized_environment_templates():
    import base64
    from app.intelligence.safety import sanitize_file
    service = GitHubService('')
    service.request = AsyncMock(return_value={'type': 'file', 'path': '.env.example', 'size': 12, 'content': base64.b64encode(b'PORT=8000').decode()})
    result = asyncio.run(service.file('example', 'project', 'commit', '.env.example'))
    assert sanitize_file(result['path'], result['content']) == 'PORT=[REDACTED]'
    service.request.assert_awaited_once()


def test_generic_display_blocks_environment_templates_before_network():
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from app.main import app
    with patch('app.api.routes.github.GitHubService.file', new_callable=AsyncMock) as read:
        response = TestClient(app, headers={'X-GitHub-Token': 'fixture-credential'}).get('/api/v1/github/file', params={'owner':'example','repo':'project','branch':'main','path':'.env.example'})
    assert response.status_code == 403
    assert response.json()['code'] == 'sensitive_source_path'
    read.assert_not_called()
