"""User credential preflight and safe endpoint failure contracts (synthetic wire)."""
from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import github_token
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.services.github_service import GitHubService

@pytest.fixture
def anyio_backend(): return 'asyncio'

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(get_settings(), 'baton_access_key', '')
    return TestClient(app, headers={'X-GitHub-Token': 'fixture-user-credential'})

def test_github_token_precedence_rules(monkeypatch):
    monkeypatch.setattr(get_settings(), 'github_token', 'fixture-server-credential')
    assert github_token(' user-credential ').source == 'request'
    for value in (None, '', '   '):
        with pytest.raises(BatonError) as error: github_token(value)
        assert error.value.code == 'github_token_required'
    assert GitHubService().token is None

@pytest.mark.parametrize('path,method,body', [
    ('github/validate-repository','post', {'repo_url':'https://github.com/o/r'}),
    ('github/access','get', None), ('github/branches?owner=o&repo=r','get',None),
    ('github/tree?owner=o&repo=r&branch=main','get',None),
    ('github/file?owner=o&repo=r&branch=main&path=main.py','get',None),
    ('analysis/repository','post',{'owner':'o','repo':'r','branch':'main'}),
    ('context','post',{'owner':'o','repo':'r','branch':'main'}),
    ('integration','post',{'owner':'o','repo':'r','branch':'main'}),
    ('workspace/inspect','post',{'owner':'o','repo':'r','branch':'main'}),
    ('workspace/source','post',{'owner':'o','repo':'r','branch':'main','path':'main.py'}),
    ('workspace/artifacts','post',{'owner':'o','repo':'r','branch':'main','artifact_type':'context'}),
    ('workspace/compare','post',{'owner':'o','repo':'r','branch':'main','compare_branch':'feature'}),
])
def test_no_token_never_contacts_github(monkeypatch, path, method, body):
    monkeypatch.setattr(get_settings(), 'baton_access_key', '')
    monkeypatch.setattr(get_settings(), 'github_token', 'fixture-server-credential')
    with patch('httpx.AsyncClient.request', side_effect=AssertionError('Network forbidden')):
        response = TestClient(app).request(method, '/api/v1/'+path, json=body)
    assert response.status_code == 401 and response.json()['code'] == 'github_token_required'
    assert 'fixture-server-credential' not in response.text

@pytest.mark.parametrize('visibility', ['public','private'])
def test_connection_proves_acceptance_repository_contents_and_head(client, visibility):
    calls=[]
    async def remote(self, method, path, **kwargs):
        calls.append(path)
        assert kwargs['headers']['Authorization'] == 'Bearer fixture-user-credential'
        data = {'login':'private-account'} if path == '/user' else [] if path.endswith('/branches') else {'sha':'exact-head'} if '/commits/' in path else {'default_branch':'main','visibility':visibility}
        return httpx.Response(200, json=data, headers={'x-ratelimit-limit':'5000','x-ratelimit-remaining':'4996','x-ratelimit-resource':'core'})
    with patch('httpx.AsyncClient.request', new=remote):
        response=client.post('/api/v1/github/validate-repository',json={'repo_url':'https://github.com/o/r.git'})
    assert response.status_code == 200
    data=response.json()
    assert data['authenticated'] and data['repository_accessible'] and data['token_source']=='request'
    assert data['visibility']==visibility and data['current_head']=='exact-head'
    assert data['rate_limit']['resource']=='core'
    assert calls==['/user','/repos/o/r','/repos/o/r/branches','/repos/o/r/commits/main']
    assert 'fixture-user-credential' not in response.text and 'private-account' not in response.text

@pytest.mark.parametrize('endpoint,status,headers,code', [
    ('/user',401,{},'github_authentication_failure'),
    ('/repos/o/r',404,{},'github_not_found'),
    ('/repos/o/r',403,{'x-accepted-github-permissions':'metadata=read'},'github_insufficient_permissions'),
    ('/repos/o/r/branches',403,{'x-accepted-github-permissions':'contents=read'},'github_insufficient_permissions'),
    ('/repos/o/r',403,{},'github_permission_failure'),
    ('/user',403,{'x-ratelimit-remaining':'0','x-ratelimit-reset':'2000000000'},'github_rate_limit'),
    ('/user',403,{'retry-after':'60'},'github_rate_limit'),
    ('/user',429,{},'github_rate_limit'), ('/user',503,{},'github_api_failure'),
])
def test_preflight_failure_stops_without_downgrade(client, endpoint, status, headers, code):
    calls=[]
    async def remote(self,method,path,**kwargs):
        calls.append(path)
        if path == endpoint: return httpx.Response(status,headers=headers,json={'message':'Denied fixture-private-upstream'})
        return httpx.Response(200,json={'default_branch':'main'})
    with patch('httpx.AsyncClient.request',new=remote):
        response=client.post('/api/v1/github/validate-repository',json={'repo_url':'https://github.com/o/r'})
    assert response.json()['code']==code and response.status_code >= 400
    assert calls[-1]==endpoint and 'fixture-private-upstream' not in response.text

def test_empty_repository_preflight_is_connected_without_fabricated_commit(client):
    async def remote(self,method,path,**kwargs):
        if '/commits/' in path: return httpx.Response(409,json={'message':'Git Repository is empty.'})
        return httpx.Response(200,json=[] if path.endswith('/branches') else {'default_branch':'main'})
    with patch('httpx.AsyncClient.request',new=remote):
        response=client.post('/api/v1/github/validate-repository',json={'repo_url':'https://github.com/o/r'})
    assert response.status_code==200 and response.json()['current_head'] is None
    assert response.json()['connection_state']=='EMPTY_REPOSITORY'

@pytest.mark.parametrize('url',['https://example.com/o/r','https://github.com/o/.git','https://github.com/o/../'])
def test_invalid_repository_error(client,url):
    response=client.post('/api/v1/github/validate-repository',json={'repo_url':url})
    assert response.status_code==400 and response.json()['code']=='invalid_repository_url'

@pytest.mark.parametrize('failure,code',[('network','github_network_failure'),('timeout','github_timeout'),('json','github_api_failure')])
def test_transport_failures_are_safe(client,failure,code):
    async def remote(*args,**kwargs):
        if failure=='json': return httpx.Response(200,text='fixture-private-upstream')
        if failure=='timeout': raise httpx.ReadTimeout('fixture-private-upstream')
        raise httpx.ConnectError('fixture-private-upstream')
    with patch('httpx.AsyncClient.request',new=remote):
        response=client.post('/api/v1/github/validate-repository',json={'repo_url':'https://github.com/o/r'})
    assert response.json()['code']==code and 'fixture-private-upstream' not in response.text

@pytest.mark.parametrize('state', ['invalid', 'expired', 'revoked'])
def test_rejected_token_lifecycle_is_always_401_without_retry(client, state):
    calls=[]
    async def remote(self,method,path,**kwargs):
        calls.append(path)
        return httpx.Response(401,json={'message':state})
    with patch('httpx.AsyncClient.request',new=remote):
        response=client.post('/api/v1/github/validate-repository',json={'repo_url':'https://github.com/o/r'})
    assert response.status_code==401 and response.json()['code']=='github_authentication_failure'
    assert calls==['/user']
