"""User-owned Gemini scope, credential isolation and CORS-visible backend failures."""
import asyncio
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from app.main import app
from app.core.config import get_settings
from app.core.security import REQUEST_AI
from app.services.ai_provider import GeminiProvider
from app.schemas.workspace import ChatRequest
from tests.test_ai_workspace import service, request, choose_api

@pytest.fixture
def anyio_backend(): return 'asyncio'

def headers(key='synthetic-user-ai-A', model='fixture-model'):
    return {'X-Gemini-Key': key, 'X-Gemini-Model': model, 'X-GitHub-Token': 'synthetic-user-github', 'Origin': 'https://baton-sigma-six.vercel.app'}

def install_wire(monkeypatch, wire):
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: original(transport=httpx.MockTransport(wire), **kw))
    return original

@pytest.mark.parametrize('status,code', [(200,None),(400,'ai_key_invalid'),(401,'ai_key_invalid'),(403,'ai_key_invalid'),(404,'ai_model_unavailable'),(429,'ai_provider_rate_limit'),(500,'ai_provider_failure')])
def test_request_key_validation_without_server_setup(monkeypatch,status,code):
    settings=get_settings()
    monkeypatch.setattr(settings,'gemini_api_key',SecretStr(''))
    monkeypatch.setattr(settings,'gemini_model','')
    monkeypatch.setattr(settings,'baton_access_key','operator-should-not-be-needed')
    def wire(req):
        assert req.method=='GET' and req.headers['x-goog-api-key']=='synthetic-user-ai-A'
        assert 'authorization' not in req.headers and not req.url.query and not req.content
        return httpx.Response(status,json={'name':'models/fixture-model','supportedGenerationMethods':['generateContent'],'upstream_error':'synthetic-user-ai-A'})
    install_wire(monkeypatch,wire)
    res=TestClient(app).post('/api/v1/workspace/provider/validate',headers=headers())
    assert 'synthetic' not in res.text and 'synthetic' not in res.headers['x-baton-usage']
    usage=json.loads(res.headers['x-baton-usage'])
    assert usage['ai_requests']==0 and usage['ai_validation_requests']==1 and usage['github_requests']==0
    if code: assert res.json()['code']==code
    else: assert res.json()['key_accepted'] and res.json()['model_validation']=='VERIFIED' and res.json()['generation_validation']=='UNVERIFIED'
    assert REQUEST_AI.get() is None

@pytest.mark.parametrize('model,methods', [('other-model',['generateContent']),('fixture-model',['embedContent'])])
def test_invalid_model_metadata_never_claims_ready(monkeypatch,model,methods):
    install_wire(monkeypatch,lambda req:httpx.Response(200,json={'name':'models/'+model,'supportedGenerationMethods':methods}))
    res=TestClient(app).post('/api/v1/workspace/provider/validate',headers=headers())
    assert res.status_code==502 and res.json()['code']=='ai_model_unavailable'

def test_chat_uses_user_key_and_expires_history_on_ai_credential_change(monkeypatch):
    from app.api.routes import workspace as routes
    workspace=service(); workspace.provider=GeminiProvider()
    monkeypatch.setattr(routes,'WorkspaceService',lambda:workspace)
    monkeypatch.setattr(get_settings(),'gemini_api_key',SecretStr('synthetic-server-ai'))
    monkeypatch.setattr(get_settings(),'baton_access_key','synthetic-server-operator')
    seen=[]
    def wire(req):
        seen.append(req.headers['x-goog-api-key'])
        assert seen[-1]=='synthetic-user-ai-A'
        packet=json.loads(json.loads(req.content)['contents'][0]['parts'][0]['text'])
        assert not any(value in json.dumps(packet) for value in ('synthetic-user-ai-A','synthetic-server-ai','synthetic-user-github'))
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':choose_api(packet).model_dump_json()}]}}]})
    install_wire(monkeypatch,wire)
    client=TestClient(app)
    first=client.post('/api/v1/workspace/chat',headers=headers(),json=request(ChatRequest,message='What is the API?').model_dump())
    assert first.status_code==200
    follow=request(ChatRequest,message='Explain it',conversation_id=first.json()['conversation_id'],revision=1).model_dump()
    for changed in (headers('synthetic-user-ai-B'),headers(model='other-model')):
        res=client.post('/api/v1/workspace/chat',headers=changed,json=follow)
        assert res.status_code==409 and res.json()['code']=='conversation_expired'
    assert len(seen)==1 and 'synthetic-user-ai' not in str(workspace.conversations.entries)
    assert REQUEST_AI.get() is None

@pytest.mark.anyio
async def test_concurrent_users_never_mix_provider_headers(monkeypatch):
    async def wire(req):
        key=req.headers['x-goog-api-key']; model=req.url.path.rsplit('/',1)[-1]
        await asyncio.sleep(.01)
        assert key=={'model-a':'synthetic-user-ai-A','model-b':'synthetic-user-ai-B'}[model]
        return httpx.Response(200,json={'name':'models/'+model,'supportedGenerationMethods':['generateContent']})
    original=install_wire(monkeypatch,wire)
    async with original(transport=httpx.ASGITransport(app=app),base_url='https://baton.test') as client:
        results=await asyncio.gather(client.post('/api/v1/workspace/provider/validate',headers=headers('synthetic-user-ai-A','model-a')),client.post('/api/v1/workspace/provider/validate',headers=headers('synthetic-user-ai-B','model-b')))
    assert [r.json()['model'] for r in results]==['model-a','model-b']
    assert REQUEST_AI.get() is None

def test_unexpected_failure_is_safe_and_cors_visible():
    from app.core.response_safety import SafeJSONResponses
    async def failing(scope,receive,send): raise RuntimeError('synthetic-user-ai-A private exception')
    client=TestClient(SafeJSONResponses(failing))
    res=client.get('/',headers=headers())
    assert res.status_code==500 and res.json()['code']=='baton_backend_failure'
    assert 'synthetic' not in res.text
    assert res.headers['access-control-allow-origin']=='https://baton-sigma-six.vercel.app'
    denied=client.get('/',headers={'Origin':'https://untrusted.example'})
    assert 'access-control-allow-origin' not in denied.headers
