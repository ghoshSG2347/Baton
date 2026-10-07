import re, base64
import httpx
import asyncio
import hashlib
import time
import logging
import json
import io
import tarfile
import gzip
import zlib
from collections import Counter, OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urlsplit
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.utils.text_utils import language_for
from app.intelligence.safety import sensitive_path
from app.utils.file_filters import is_relevant
from app.analyzers.documentation_analyzer import _classify_doc_path


class _SafeArchiveTransportLog(logging.Filter):
    def filter(self, record):
        # httpx INFO logs URLs. GitHub's private redirect contains a temporary
        # download grant; keep that query out of logs at every verbosity.
        message = record.getMessage()
        record.msg = re.sub(r'(https://codeload\.github\.com/[^\s?]+)\?[^\s]+', r'\1?[REDACTED]', message)
        record.args = ()
        return True


logging.getLogger('httpx').addFilter(_SafeArchiveTransportLog())

class GitHubService:
    # Authorization-scoped, short-lived HEAD/metadata observations. These are
    # not snapshots or durable permission grants. Revocation/HEAD changes are
    # revalidated after 60 seconds; explicit analysis bypasses HEAD caching.
    _observations = OrderedDict()
    _observation_sizes = {}
    _pending = {}
    _backoff = OrderedDict()
    observation_ttl = 60

    def remember(self, key, data):
        size = len(json.dumps(data).encode())
        if size > 4_000_000:
            return
        self._observations.pop(key, None)
        self._observation_sizes.pop(key, None)
        while self._observations and (len(self._observations) >= 256 or sum(self._observation_sizes.values()) + size > 40_000_000):
            oldest, _ = self._observations.popitem(last=False)
            self._observation_sizes.pop(oldest, None)
        self._observations[key] = (time.monotonic() + self.observation_ttl, deepcopy(data))
        self._observation_sizes[key] = size

    def __init__(self, token: str | None = None):
        if token and token.strip():
            self.token = token.strip()
        else:
            self.token = None
        self.token_source = getattr(token, 'source', 'request') if self.token else 'none'
        self.access_scope = hashlib.sha256((self.token or '').encode()).hexdigest()
        self.request_counts = Counter()
        self.cache_counts = Counter()
        self.last_response = None
        self._content = {}

    @staticmethod
    def response_metadata(response):
        def number(name):
            try:
                value = int(response.headers.get(name, ''))
                return value if value >= 0 else None
            except (TypeError, ValueError):
                return None
        reset = number('x-ratelimit-reset')
        retry = response.headers.get('retry-after')
        try:
            retry = max(0, int(retry)) if retry is not None else None
        except ValueError:
            try:
                retry = max(0, int((parsedate_to_datetime(retry) - datetime.now(timezone.utc)).total_seconds()))
            except (TypeError, ValueError, OverflowError):
                retry = None
        return {'upstream_status': response.status_code, 'rate_limit': {
            'limit': number('x-ratelimit-limit'), 'remaining': number('x-ratelimit-remaining'),
            'used': number('x-ratelimit-used'), 'reset_at': reset,
            'resource': response.headers.get('x-ratelimit-resource') if response.headers.get('x-ratelimit-resource') in ('core', 'search', 'graphql', 'integration_manifest') else None}, 'retry_after': retry}

    def cache_hit(self, category):
        self.cache_counts[category] += 1
        from app.core.usage import increment
        increment('cache_hits')
        if category == 'coalesced':
            increment('coalesced')

    async def observed(self, path, *, params=None, fresh=False):
        key = (self.access_scope, path, tuple(sorted((params or {}).items())))
        cached = self._observations.get(key)
        if not fresh and cached and cached[0] > time.monotonic():
            self.cache_hit('observation')
            return deepcopy(cached[1])
        loop_key = (asyncio.get_running_loop(), key)
        if loop_key in self._pending:
            self.cache_hit('coalesced')
            return deepcopy(await asyncio.shield(self._pending[loop_key]))
        async def fetch():
            data = await self.request('GET', path, params=params)
            self.remember(key, data)
            return data
        task = asyncio.create_task(fetch())
        self._pending[loop_key] = task
        task.add_done_callback(lambda _: self._pending.pop(loop_key, None))
        return deepcopy(await asyncio.shield(task))

    async def request(self, method:str, path:str, **kwargs):
        if not self.token:
            raise BatonError('GitHub token required. Re-enter your Fine-grained GitHub token.', 401, 'github_token_required')
        cooldown = self._backoff.get(self.access_scope)
        if cooldown and cooldown[0] > time.time():
            raise BatonError('GitHub API limit reached. Wait until the reset or backoff period ends before retrying.', 429, 'github_rate_limit', metadata={**cooldown[1], 'token_source': self.token_source, 'retry_after': max(1, int(cooldown[0] - time.time()))})
        self._backoff.pop(self.access_scope, None)
        headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
        if self.token: headers["Authorization"]=f"Bearer {self.token}"
        category = ('archive' if '/tarball/' in path else 'file' if '/contents/' in path else 'tree' if '/git/trees/' in path
                    else 'commit' if '/commits/' in path else 'branches' if path.endswith('/branches')
                    else 'access' if path in ('/user', '/rate_limit') else 'repository')
        self.request_counts[f'{method} {category}'] += 1
        from app.core.usage import increment
        increment('github_requests')
        from app.core.usage import github_operation, github_result
        github_operation(category)
        archive = kwargs.pop('_archive', False)
        try:
            async with httpx.AsyncClient(base_url="https://api.github.com", timeout=20) as c:
                r = await self._archive_response(c, path, headers) if archive else await c.request(method,path,headers=headers,**kwargs)
        except httpx.TimeoutException:
            github_result(0)
            raise BatonError('GitHub did not respond in time. Please retry.', 504, 'github_timeout') from None
        except httpx.HTTPError:
            github_result(0)
            raise BatonError("Baton could not reach GitHub. Please retry.", 502, "github_network_failure") from None
        if not archive or self.last_response is None or r.status_code >= 400:
            self.last_response = self.response_metadata(r)
        from app.core.usage import observe_quota
        observe_quota(self.last_response or {})
        github_result(r.status_code)
        logging.getLogger('uvicorn.error.baton.github.metrics').debug(
            'github_request endpoint=%s token_present=%s token_source=%s response=%s',
            category, bool(self.token), self.token_source, self.last_response)
        if r.status_code >= 400:
            # Inspect only for classification; never return or log upstream bodies/credentials.
            try:
                body = r.json()
                message = str(body.get("message", "")).lower() if isinstance(body, dict) else ""
            except ValueError:
                message = ""
            primary = self.last_response['rate_limit']['remaining'] == 0
            secondary = 'secondary rate limit' in message or 'abuse detection' in message
            if r.status_code in (403, 429) and (primary or secondary or 'rate limit' in message or r.status_code == 429 or r.headers.get('retry-after')):
                kind = 'primary' if primary else 'secondary' if secondary or r.headers.get('retry-after') else 'unknown'
                increment('github_rate_limited')
                metadata = {**self.last_response, 'rate_limit_kind': kind, 'token_present': bool(self.token),
                            'authorization_present': bool(self.token), 'token_source': self.token_source}
                if metadata['retry_after'] is None and kind != 'primary':
                    metadata['retry_after'] = 60
                deadline = max(self.last_response['rate_limit']['reset_at'] or 0 if primary else 0,
                               time.time() + (metadata['retry_after'] or 0))
                if deadline <= time.time():
                    deadline = time.time() + 60
                    metadata['retry_after'] = 60
                self._backoff[self.access_scope] = (deadline, metadata)
                while len(self._backoff) > 256:
                    self._backoff.popitem(last=False)
                raise BatonError('GitHub API limit reached. Wait until the reset or backoff period ends before retrying.', 429, 'github_rate_limit', metadata=metadata)
            if r.status_code == 401:
                raise BatonError("GitHub token is invalid or expired. Replace your token.", 401, "github_authentication_failure")
            if r.status_code == 403:
                permissions = r.headers.get('x-accepted-github-permissions', '')
                code = 'github_insufficient_permissions' if 'contents=read' in permissions or 'metadata=read' in permissions else 'github_permission_failure'
                raise BatonError("GitHub denied access to this repository. Baton requires Metadata: Read and Contents: Read. Check repository selection and organization approval.", 403, code)
            if r.status_code == 404:
                raise BatonError("GitHub repository or resource not found, or inaccessible. Check the repository URL; for a private repository, supply a GitHub token with access.", 404, "github_not_found")
            if r.status_code == 409 and "/commits/" in path:
                raise BatonError("This repository has no commits to analyze yet.", 409, "empty_repository")
            raise BatonError(f"GitHub API returned HTTP {r.status_code}. Please retry or check GitHub availability.", 502, "github_api_failure")
        if archive:
            return r.content
        try:
            return r.json()
        except ValueError:
            raise BatonError("GitHub returned an invalid API response. Please retry.", 502, "github_api_failure") from None
    async def _archive_response(self, client, path, headers):
        """Bound each stream; never forward the user credential to the redirect host."""
        limit = get_settings().max_archive_bytes
        async with client.stream('GET', path, headers=headers) as response:
            self.last_response = self.response_metadata(response)
            if response.status_code == 302:
                location = response.headers.get('location', '')
                parsed = urlsplit(location)
                if parsed.scheme != 'https' or parsed.hostname != 'codeload.github.com' or parsed.username or parsed.password or parsed.port not in (None, 443):
                    raise BatonError('GitHub archive redirect could not be validated.', 502, 'archive_collection_unavailable')
            else:
                return await self._bounded_archive_response(response, limit)
        self.request_counts['GET archive_download'] += 1
        from app.core.usage import increment
        increment('github_downloads')
        async with client.stream('GET', location, headers={'Accept': 'application/octet-stream'}) as response:
            if response.status_code in (301, 302, 303, 307, 308):
                raise BatonError('GitHub archive returned an unexpected redirect.', 502, 'archive_collection_unavailable')
            return await self._bounded_archive_response(response, limit)

    @staticmethod
    async def _bounded_archive_response(response, limit):
        try:
            if int(response.headers.get('content-length', '0')) > limit:
                raise BatonError('Repository archive exceeds collection bounds.', 413, 'archive_collection_unavailable')
        except ValueError:
            pass
        body = bytearray()
        async for chunk in response.aiter_bytes():
            if len(body) + len(chunk) > limit:
                raise BatonError('Repository archive exceeds collection bounds.', 413, 'archive_collection_unavailable')
            body.extend(chunk)
        return httpx.Response(response.status_code, headers=response.headers, content=bytes(body))

    async def archive(self, owner, repo, commit, folder=''):
        self.validate_repo_url(f'https://github.com/{owner}/{repo}')
        if not re.fullmatch(r'[0-9a-f]{40}', commit):
            raise BatonError('Archive collection requires an exact commit.', 422, 'archive_collection_unavailable')
        payload = await self.request('GET', f'/repos/{owner}/{repo}/tarball/{commit}', _archive=True)
        return self.archive_inventory(payload, commit, folder)

    @staticmethod
    def collection_priority(item):
        path = item.get('path', '')
        if _classify_doc_path(path): return (0, path)
        if path.endswith(('package.json', '.toml', 'requirements.txt', '.env.example')): return (1, path)
        return (2, path)

    @staticmethod
    def archive_inventory(payload, commit, folder=''):
        """Archive is data only: validate every entry, read bounded selected text in memory."""
        settings = get_settings()
        items, members, contents, omissions = [], {}, {}, {}
        total = 0
        try:
            # Bound decompression BEFORE tarfile parses even PAX/long-name headers.
            expanded = io.BytesIO()
            expanded_bytes = 0
            with gzip.GzipFile(fileobj=io.BytesIO(payload)) as zipped:
                while chunk := zipped.read(65536):
                    if expanded_bytes + len(chunk) > settings.max_archive_expanded_bytes:
                        raise ValueError('expanded stream limit')
                    expanded.write(chunk)
                    expanded_bytes += len(chunk)
            expanded.seek(0)
            with tarfile.open(fileobj=expanded, mode='r:') as archive:
                root = None
                entries = 0
                for entry in archive:
                    entries += 1
                    if entries > settings.max_archive_entries:
                        raise ValueError('entry limit')
                    name = entry.name.rstrip('/')
                    parts = name.split('/')
                    if not name or name.startswith(('/', '\\')) or '\\' in name or any(p in ('', '.', '..') for p in parts) or ':' in name or any(ord(c) < 32 for c in name):
                        raise ValueError('unsafe path')
                    if root is None: root = parts[0]
                    if parts[0] != root or not (root.endswith('-' + commit[:7]) or root.endswith('-' + commit)):
                        raise ValueError('commit root mismatch')
                    if not entry.isfile() and not entry.isdir():
                        raise ValueError('links and special entries are unsupported')
                    total += entry.size
                    if entry.size < 0 or total > settings.max_archive_expanded_bytes:
                        raise ValueError('expanded byte limit')
                    path = '/'.join(parts[1:])
                    if not path:
                        if not entry.isdir(): raise ValueError('invalid root')
                        continue
                    if path in members: raise ValueError('duplicate path')
                    members[path] = entry
                    items.append({'path': path, 'type': 'blob' if entry.isfile() else 'tree', 'size': entry.size})
                used = 0
                attempts = 0
                for item in sorted(items, key=GitHubService.collection_priority):
                    path, size = item['path'], item['size']
                    prefix = folder.strip('/')
                    if prefix and path != prefix and not path.startswith(prefix + '/'):
                        continue
                    if item['type'] != 'blob' or sensitive_path(path) or not is_relevant(path) or size > settings.max_file_size_bytes:
                        continue
                    if attempts >= settings.max_files_per_analysis or used + size > settings.max_total_context_bytes:
                        continue
                    attempts += 1
                    stream = archive.extractfile(members[path])
                    raw = stream.read(settings.max_file_size_bytes + 1) if stream else b''
                    if len(raw) != size or len(raw) > settings.max_file_size_bytes: raise ValueError('invalid member size')
                    try:
                        blob_sha = hashlib.sha1(b'blob ' + str(size).encode() + b'\0' + raw).hexdigest()
                        contents[path] = {'path': path, 'size': size, 'content': raw.decode('utf-8'), 'language': language_for(path), 'sha': blob_sha}
                        used += size
                    except UnicodeDecodeError:
                        omissions[path] = 'unreadable_file'
        except (tarfile.TarError, ValueError, OSError, EOFError, zlib.error):
            raise BatonError('Repository archive could not be safely collected within bounds.', 413, 'archive_collection_unavailable') from None
        if root is None:
            raise BatonError('GitHub archive has no verifiable root.', 502, 'archive_collection_unavailable')
        return {'tree': items, 'truncated': False}, contents, omissions

    @staticmethod
    def validate_repo_url(url:str)->tuple[str,str]:
        m=re.fullmatch(r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)/?",url.strip())
        if not m: raise BatonError("Invalid repository URL. Use https://github.com/owner/repository.", 400, "invalid_repository_url")
        owner, repo = m.group(1), m.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        if not repo or repo in (".", "..") or owner in (".", ".."):
            raise BatonError("Invalid repository URL. Use https://github.com/owner/repository.", 400, "invalid_repository_url")
        return owner, repo
    async def repository(self,owner,repo):
        self.validate_repo_url(f"https://github.com/{owner}/{repo}")
        return await self.observed(f"/repos/{owner}/{repo}")
    async def branches(self,owner,repo):
        self.validate_repo_url(f"https://github.com/{owner}/{repo}")
        return await self.observed(f"/repos/{owner}/{repo}/branches",params={"per_page":100})
    async def tree(self,owner,repo,branch,path=""):
        data=await self.tree_snapshot(owner,repo,branch)
        prefix=path.strip("/")
        return [x for x in data.get("tree",[]) if not prefix or x.get("path","")==prefix or x.get("path","").startswith(prefix+"/")]
    async def tree_snapshot(self,owner,repo,branch):
        self.validate_repo_url(f"https://github.com/{owner}/{repo}")
        ref=branch or "HEAD"
        return await self.observed(f"/repos/{owner}/{repo}/git/trees/{quote(ref, safe='')}",params={"recursive":"1"})
    async def commit(self,owner,repo,branch,*,fresh=False):
        self.validate_repo_url(f"https://github.com/{owner}/{repo}")
        return await self.observed(f"/repos/{owner}/{repo}/commits/{quote(branch or 'HEAD', safe='')}",fresh=fresh)

    async def access(self):
        # Same authenticated helper as analysis; return no account/profile data.
        endpoint = '/user'
        key = (self.access_scope, 'access')
        cached = self._observations.get(key)
        if cached and cached[0] > time.monotonic():
            self.cache_hit('access')
            return {**deepcopy(cached[1]), 'token_source': self.token_source}
        loop_key = (asyncio.get_running_loop(), key)
        if loop_key not in self._pending:
            async def check():
                await self.request('GET', endpoint)
                result = {'authenticated': bool(self.token), 'token_source': self.token_source,
                          'token_present': bool(self.token), **self.last_response}
                self.remember(key, result)
                return result
            task = asyncio.create_task(check())
            self._pending[loop_key] = task
            task.add_done_callback(lambda _: self._pending.pop(loop_key, None))
        result = await asyncio.shield(self._pending[loop_key])
        return {**deepcopy(result), 'token_source': self.token_source}

    async def validate_connection(self, owner, repo):
        # Acceptance is proven by /user; repository metadata alone can be public.
        self.validate_repo_url(f'https://github.com/{owner}/{repo}')
        await self.access()
        metadata = await self.observed(f'/repos/{owner}/{repo}', fresh=True)
        # Branch listing exercises Contents: Read even for an empty repository.
        await self.observed(f'/repos/{owner}/{repo}/branches', params={'per_page': 100}, fresh=True)
        head = None
        try:
            head = (await self.commit(owner, repo, metadata.get('default_branch') or 'HEAD', fresh=True)).get('sha')
            if not head:
                raise BatonError('GitHub did not return an exact commit.', 502, 'github_api_failure')
        except BatonError as exc:
            if exc.code != 'empty_repository':
                raise
        return {'authenticated': True, 'token_source': self.token_source,
                'repository_accessible': True, 'accessible': True,
                'owner': owner, 'repository': repo,
                'visibility': metadata.get('visibility') or ('private' if metadata.get('private') else 'public'),
                'default_branch': metadata.get('default_branch'), 'current_head': head,
                'connection_state': 'CONNECTED' if head else 'EMPTY_REPOSITORY',
                'rate_limit': (self.last_response or {}).get('rate_limit', {}),
                'required_permissions': {'metadata': 'read', 'contents': 'read'}}
    async def file(self,owner,repo,branch,path):
        self.validate_repo_url(f'https://github.com/{owner}/{repo}')
        if not path or path.startswith(('/', '\\')) or '\\' in path or any(part in ('', '.', '..') for part in path.split('/')):
            raise BatonError('Invalid repository file path.', 422, 'invalid_source_path')
        if sensitive_path(path):
            raise BatonError('Credential files cannot be displayed.', 403, 'sensitive_source_path')
        path = path.lstrip('/')
        key = (owner.lower(), repo.lower(), branch, path)
        if key in self._content:
            self.cache_hit('file')
            return deepcopy(self._content[key])
        data=await self.request("GET",f"/repos/{owner}/{repo}/contents/{quote(path, safe='/')}",params={"ref":branch})
        if isinstance(data,list) or data.get("type")!="file": raise BatonError("Requested path is not a file")
        if data.get("size",0)>get_settings().max_file_size_bytes: raise BatonError("File exceeds configured size limit",413)
        try: content=base64.b64decode(data.get("content","")).decode("utf-8")
        except (ValueError,UnicodeDecodeError): raise BatonError("Binary files are not supported")
        result = {"path":data["path"],"size":data.get("size",len(content.encode())),"content":content,"language":language_for(data["path"])}
        self._content[key] = result
        return deepcopy(result)
