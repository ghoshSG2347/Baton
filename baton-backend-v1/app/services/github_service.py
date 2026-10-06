import re, base64
import httpx
import asyncio
import hashlib
import time
import logging
import json
from collections import Counter, OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.utils.text_utils import language_for

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
            env_token = get_settings().github_token
            self.token = env_token.strip() if env_token and env_token.strip() else None
        self.token_source = getattr(token, 'source', 'request') if token and token.strip() else 'server' if self.token else 'none'
        self.access_scope = hashlib.sha256((self.token or '').encode()).hexdigest()
        self.request_counts = Counter()
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
            'used': number('x-ratelimit-used'), 'reset_at': reset}, 'retry_after': retry}

    async def observed(self, path, *, params=None, fresh=False):
        key = (self.access_scope, path, tuple(sorted((params or {}).items())))
        cached = self._observations.get(key)
        if not fresh and cached and cached[0] > time.monotonic():
            return deepcopy(cached[1])
        loop_key = (asyncio.get_running_loop(), key)
        if loop_key in self._pending:
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
        cooldown = self._backoff.get(self.access_scope)
        if cooldown and cooldown[0] > time.time():
            raise BatonError('GitHub API limit reached. Wait until the reset or backoff period ends before retrying.', 429, 'github_rate_limit', metadata={**cooldown[1], 'token_source': self.token_source, 'retry_after': max(1, int(cooldown[0] - time.time()))})
        self._backoff.pop(self.access_scope, None)
        headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
        if self.token: headers["Authorization"]=f"Bearer {self.token}"
        category = ('file' if '/contents/' in path else 'tree' if '/git/trees/' in path
                    else 'commit' if '/commits/' in path else 'branches' if path.endswith('/branches')
                    else 'access' if path in ('/user', '/rate_limit') else 'repository')
        self.request_counts[f'{method} {category}'] += 1
        try:
            async with httpx.AsyncClient(base_url="https://api.github.com", timeout=20) as c: r=await c.request(method,path,headers=headers,**kwargs)
        except httpx.TimeoutException:
            raise BatonError('GitHub did not respond in time. Please retry.', 504, 'github_timeout') from None
        except httpx.HTTPError:
            raise BatonError("Baton could not reach GitHub. Please retry.", 502, "github_network_failure") from None
        self.last_response = self.response_metadata(r)
        logging.getLogger('uvicorn.error.baton.github.metrics').info(
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
                raise BatonError("GitHub authentication failed. Replace the supplied GitHub token or the backend GITHUB_TOKEN.", 401, "github_authentication_failure")
            if r.status_code == 403:
                raise BatonError("GitHub denied access. Check token permissions and organization authorization.", 403, "github_permission_failure")
            if r.status_code == 404:
                raise BatonError("GitHub repository or resource not found, or inaccessible. Check the repository URL; for a private repository, supply a GitHub token with access.", 404, "github_not_found")
            if r.status_code == 409 and "/commits/" in path:
                raise BatonError("This repository has no commits to analyze yet.", 409, "empty_repository")
            raise BatonError(f"GitHub API returned HTTP {r.status_code}. Please retry or check GitHub availability.", 502, "github_api_failure")
        try:
            return r.json()
        except ValueError:
            raise BatonError("GitHub returned an invalid API response. Please retry.", 502, "github_api_failure") from None
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
    async def repository(self,owner,repo): return await self.observed(f"/repos/{owner}/{repo}")
    async def branches(self,owner,repo): return await self.observed(f"/repos/{owner}/{repo}/branches",params={"per_page":100})
    async def tree(self,owner,repo,branch,path=""):
        data=await self.tree_snapshot(owner,repo,branch)
        prefix=path.strip("/")
        return [x for x in data.get("tree",[]) if not prefix or x.get("path","")==prefix or x.get("path","").startswith(prefix+"/")]
    async def tree_snapshot(self,owner,repo,branch):
        ref=branch or "HEAD"
        return await self.observed(f"/repos/{owner}/{repo}/git/trees/{quote(ref, safe='')}",params={"recursive":"1"})
    async def commit(self,owner,repo,branch,*,fresh=False):
        return await self.observed(f"/repos/{owner}/{repo}/commits/{quote(branch or 'HEAD', safe='')}",fresh=fresh)

    async def access(self):
        # Same authenticated helper as analysis; return no account/profile data.
        endpoint = '/user' if self.token else '/rate_limit'
        key = (self.access_scope, 'access')
        cached = self._observations.get(key)
        if cached and cached[0] > time.monotonic():
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
    async def file(self,owner,repo,branch,path):
        path = path.lstrip('/')
        key = (owner.lower(), repo.lower(), branch, path)
        if key in self._content:
            return deepcopy(self._content[key])
        data=await self.request("GET",f"/repos/{owner}/{repo}/contents/{quote(path, safe='/')}",params={"ref":branch})
        if isinstance(data,list) or data.get("type")!="file": raise BatonError("Requested path is not a file")
        if data.get("size",0)>get_settings().max_file_size_bytes: raise BatonError("File exceeds configured size limit",413)
        try: content=base64.b64decode(data.get("content","")).decode("utf-8")
        except (ValueError,UnicodeDecodeError): raise BatonError("Binary files are not supported")
        result = {"path":data["path"],"size":data.get("size",len(content.encode())),"content":content,"language":language_for(data["path"])}
        self._content[key] = result
        return deepcopy(result)
