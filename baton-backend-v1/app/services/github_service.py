import re, base64
import httpx
from urllib.parse import quote
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.utils.text_utils import language_for

class GitHubService:
    def __init__(self, token: str | None = None):
        if token and token.strip():
            self.token = token.strip()
        else:
            env_token = get_settings().github_token
            self.token = env_token.strip() if env_token and env_token.strip() else None
    async def request(self, method:str, path:str, **kwargs):
        headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
        if self.token: headers["Authorization"]=f"Bearer {self.token}"
        try:
            async with httpx.AsyncClient(base_url="https://api.github.com", timeout=20) as c: r=await c.request(method,path,headers=headers,**kwargs)
        except httpx.HTTPError:
            raise BatonError("Baton could not reach GitHub. Please retry.", 502, "github_network_failure") from None
        if r.status_code >= 400:
            # Inspect only for classification; never return or log upstream bodies/credentials.
            try:
                body = r.json()
                message = str(body.get("message", "")).lower() if isinstance(body, dict) else ""
            except ValueError:
                message = ""
            if r.status_code == 429 or (r.status_code == 403 and (
                r.headers.get("x-ratelimit-remaining") == "0" or r.headers.get("retry-after")
                or "rate limit" in message)):
                raise BatonError("GitHub rate limit reached. Wait before retrying; a valid GitHub token can increase the limit.", 429, "github_rate_limit")
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
    async def repository(self,owner,repo): return await self.request("GET",f"/repos/{owner}/{repo}")
    async def branches(self,owner,repo): return await self.request("GET",f"/repos/{owner}/{repo}/branches",params={"per_page":100})
    async def tree(self,owner,repo,branch,path=""):
        data=await self.tree_snapshot(owner,repo,branch)
        prefix=path.strip("/")
        return [x for x in data.get("tree",[]) if not prefix or x.get("path","")==prefix or x.get("path","").startswith(prefix+"/")]
    async def tree_snapshot(self,owner,repo,branch):
        ref=branch or "HEAD"
        return await self.request("GET",f"/repos/{owner}/{repo}/git/trees/{quote(ref, safe='')}",params={"recursive":"1"})
    async def commit(self,owner,repo,branch):
        return await self.request("GET",f"/repos/{owner}/{repo}/commits/{quote(branch or 'HEAD', safe='')}")
    async def file(self,owner,repo,branch,path):
        data=await self.request("GET",f"/repos/{owner}/{repo}/contents/{path.lstrip('/')}",params={"ref":branch})
        if isinstance(data,list) or data.get("type")!="file": raise BatonError("Requested path is not a file")
        if data.get("size",0)>get_settings().max_file_size_bytes: raise BatonError("File exceeds configured size limit",413)
        try: content=base64.b64decode(data.get("content","")).decode("utf-8")
        except (ValueError,UnicodeDecodeError): raise BatonError("Binary files are not supported")
        return {"path":data["path"],"size":data.get("size",len(content.encode())),"content":content,"language":language_for(data["path"])}
