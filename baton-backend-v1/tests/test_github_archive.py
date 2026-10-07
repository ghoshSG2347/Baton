"""Bounded archive transport/security and canonical collector equivalence."""
import asyncio
import base64
import gzip
import hashlib
import io
import tarfile
from unittest.mock import patch
import httpx
import pytest
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.services.github_service import GitHubService
from app.services.analysis_service import AnalysisService
from app.intelligence.snapshot import MemorySnapshotStore

SHA = 'a' * 40
@pytest.fixture
def anyio_backend(): return 'asyncio'

def archive(files, *, root='o-r-aaaaaaa', kind=None):
    data=io.BytesIO()
    with tarfile.open(fileobj=data,mode='w:gz') as tar:
        top=tarfile.TarInfo(root); top.type=tarfile.DIRTYPE; tar.addfile(top)
        for path, content in files.items():
            info=tarfile.TarInfo(root+'/'+path); info.size=len(content)
            if kind: info.type=kind; info.linkname='outside'
            tar.addfile(info,io.BytesIO(content) if not kind else None)
    return data.getvalue()

@pytest.mark.parametrize('path',['../escape','/absolute','safe/../../escape','C:/escape','safe\\escape','./relative'])
def test_archive_rejects_unsafe_paths(path):
    with pytest.raises(BatonError) as error: GitHubService.archive_inventory(archive({path:b'x'}),SHA)
    assert error.value.code=='archive_collection_unavailable'

@pytest.mark.parametrize('kind',[tarfile.SYMTYPE,tarfile.LNKTYPE,tarfile.CHRTYPE,tarfile.FIFOTYPE])
def test_archive_rejects_links_and_special_entries(kind):
    with pytest.raises(BatonError): GitHubService.archive_inventory(archive({'link':b''},kind=kind),SHA)

def test_archive_full_commit_root_for_private_download():
    _, contents, _ = GitHubService.archive_inventory(archive({'main.py': b'pass'}, root='o-r-' + SHA), SHA)
    assert contents['main.py']['content'] == 'pass'

def test_archive_commit_root_must_match():
    with pytest.raises(BatonError): GitHubService.archive_inventory(archive({'main.py':b'pass'},root='o-r-bbbbbbb'),SHA)

def test_archive_expansion_entry_and_text_bounds(monkeypatch):
    settings=get_settings()
    monkeypatch.setattr(settings,'max_archive_expanded_bytes',1024)
    with pytest.raises(BatonError): GitHubService.archive_inventory(archive({'big.txt':b'x'*100000}),SHA)
    monkeypatch.setattr(settings,'max_archive_expanded_bytes',40000000)
    monkeypatch.setattr(settings,'max_archive_entries',1)
    with pytest.raises(BatonError): GitHubService.archive_inventory(archive({'main.py':b'pass'}),SHA)
    monkeypatch.setattr(settings,'max_archive_entries',10000)
    monkeypatch.setattr(settings,'max_file_size_bytes',8)
    tree, contents, _=GitHubService.archive_inventory(archive({'.env':b'private','main.py':b'pass','big.py':b'x'*100}),SHA)
    assert len(tree['tree'])==3 and set(contents)=={'main.py'}

def test_archive_folder_uses_same_priority_and_limits(monkeypatch):
    monkeypatch.setattr(get_settings(),'max_files_per_analysis',1)
    files={'root.py':b'pass','client/main.py':b'pass','client/README.md':b'# Client'}
    _, contents, _=GitHubService.archive_inventory(archive(files),SHA,'client')
    assert set(contents)=={'client/README.md'}

@pytest.mark.anyio
async def test_archive_transport_pins_full_commit_and_does_not_forward_credential(monkeypatch):
    calls=[]; payload=archive({'main.py':b'pass'})
    def remote(request):
        calls.append(request)
        if request.url.host=='api.github.com':
            assert request.url.path.endswith('/tarball/'+SHA)
            assert request.headers['Authorization']=='Bearer fixture-credential'
            return httpx.Response(302,headers={'location':'https://codeload.github.com/o/r/tar.gz/'+SHA,'x-ratelimit-remaining':'4999'})
        assert request.url.host=='codeload.github.com' and 'Authorization' not in request.headers
        return httpx.Response(200,content=payload)
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs: original(**kwargs,transport=httpx.MockTransport(remote)))
    service=GitHubService('fixture-credential'); tree,contents,_=await service.archive('o','r',SHA)
    assert len(calls)==2 and contents['main.py']['content']=='pass'
    assert service.request_counts=={'GET archive':1,'GET archive_download':1}
    assert service.last_response['rate_limit']['remaining']==4999

@pytest.mark.anyio
async def test_archive_redirect_and_download_size_rejected(monkeypatch):
    original=httpx.AsyncClient
    for location in ['https://evil.example/file','http://codeload.github.com/file','https://user:pass@codeload.github.com/file']:
        def remote(request): return httpx.Response(302,headers={'location':location})
        monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs: original(**kwargs,transport=httpx.MockTransport(remote)))
        with pytest.raises(BatonError): await GitHubService('fixture-credential').archive('o','r',SHA)
    monkeypatch.setattr(get_settings(),'max_archive_bytes',1024)
    def remote(request): return httpx.Response(200,content=b'x'*2000)
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs: original(**kwargs,transport=httpx.MockTransport(remote)))
    with pytest.raises(BatonError): await GitHubService('fixture-credential').archive('o','r',SHA)

@pytest.mark.anyio
async def test_archive_and_tree_feed_identical_intelligence_and_snapshot_reuse(monkeypatch):
    files={'README.md':b'# Project','main.py':b'def main(): pass','.env':b'private','data.bin':b'x'}
    payload=archive(files)
    async def remote(self,method,path,**kwargs):
        if '/commits/' in path: data={'sha':SHA}
        elif '/git/trees/' in path: data={'tree':[{'path':p,'type':'blob','size':len(v),'sha':hashlib.sha1(b'blob '+str(len(v)).encode()+b'\0'+v).hexdigest()} for p,v in files.items()]}
        else:
            p=path.split('/contents/')[1]; data={'path':p,'type':'file','size':len(files[p]),'content':base64.b64encode(files[p]).decode()}
        return httpx.Response(200,json=data)
    async def download(self,*args): return httpx.Response(200,content=payload)
    with patch('httpx.AsyncClient.request',new=remote),patch.object(GitHubService,'_archive_response',new=download):
        legacy=await AnalysisService('fixture-credential',MemorySnapshotStore()).analyze_intelligence('o','r','main')
        monkeypatch.setattr(get_settings(),'github_archive_analysis',True)
        service=AnalysisService('fixture-credential',MemorySnapshotStore())
        modern=await service.analyze_intelligence('o','r','main')
        assert modern.languages==legacy.languages
        assert modern.completeness.omission_reasons==legacy.completeness.omission_reasons
        assert modern.parsed_files==legacy.parsed_files
        assert modern.file_tree==legacy.file_tree
        assert modern.documentation_sources==legacy.documentation_sources
        assert service.github.request_counts=={'GET archive':1}
        assert service.github.cache_counts['observation']==2  # same credential's HEAD + pinned tree
        reused=AnalysisService('fixture-credential',service.store)
        assert (await reused.analyze_intelligence('o','r','main')).generated==modern.generated
        assert not reused.github.request_counts

@pytest.mark.anyio
async def test_archive_failure_only_falls_back_for_collection_bounds(monkeypatch):
    from unittest.mock import AsyncMock
    monkeypatch.setattr(get_settings(),'github_archive_analysis',True)
    service=AnalysisService('fixture-credential',MemorySnapshotStore())
    service.github.commit=AsyncMock(return_value={'sha':SHA})
    service.github.tree_snapshot=AsyncMock(return_value={'tree':[]})
    service.github.archive=AsyncMock(side_effect=BatonError('quota',429,'github_rate_limit'))
    with pytest.raises(BatonError): await service.analyze_intelligence('o','r','main')
    service.github.tree_snapshot.assert_not_awaited()
    service.github.archive=AsyncMock(side_effect=BatonError('bounds',413,'archive_collection_unavailable'))
    result=await service.analyze_intelligence('o','r','main')
    service.github.tree_snapshot.assert_awaited_once()
    assert any('Archive unavailable' in w for w in result.analysis_warnings)

def test_duplicate_member_and_malformed_payload_rejected():
    data=io.BytesIO()
    with tarfile.open(fileobj=data,mode='w:gz') as tar:
        for _ in range(2):
            info=tarfile.TarInfo('o-r-aaaaaaa/main.py'); info.size=4
            tar.addfile(info,io.BytesIO(b'pass'))
    for payload in (data.getvalue(), b'not-an-archive'):
        with pytest.raises(BatonError): GitHubService.archive_inventory(payload,SHA)

def test_private_archive_download_grant_never_enters_transport_logs(caplog):
    import logging
    with caplog.at_level(logging.INFO, logger='httpx'):
        logging.getLogger('httpx').info('HTTP Request: GET %s', 'https://codeload.github.com/o/r/tar.gz/' + SHA + '?token=fixture-download-grant')
    assert 'fixture-download-grant' not in caplog.text and '[REDACTED]' in caplog.text

@pytest.mark.anyio
async def test_blob_mismatch_uses_authoritative_tree_and_contents(monkeypatch):
    from unittest.mock import AsyncMock
    monkeypatch.setattr(get_settings(), 'github_archive_analysis', True)
    service=AnalysisService('fixture-credential',MemorySnapshotStore())
    service.github.commit=AsyncMock(return_value={'sha':SHA})
    service.github.archive=AsyncMock(return_value=({'tree':[]},{'main.py':{'path':'main.py','content':'bad','sha':'b'*40,'size':3}},{}))
    service.github.tree_snapshot=AsyncMock(return_value={'tree':[{'path':'main.py','type':'blob','sha':'c'*40,'size':4}]})
    service.github.file=AsyncMock(return_value={'path':'main.py','content':'pass','size':4})
    result=await service.analyze_intelligence('o','r','main')
    service.github.tree_snapshot.assert_awaited_once()
    service.github.file.assert_awaited_once()
    assert result.file_tree[0]['sha']=='c'*40
    assert any('Archive unavailable' in w for w in result.analysis_warnings)
