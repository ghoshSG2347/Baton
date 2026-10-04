import re, base64
import httpx
from app.core.config import get_settings
from app.core.exceptions import BatonError

class GitHubService:
    def __init__(self, token:str|None=None): self.token=token or get_settings().github_token
    async def request(self, method:str, path:str, **kwargs):
        headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
        if self.token: headers["Authorization"]=f"Bearer {self.token}"
        try:
            async with httpx.AsyncClient(base_url="https://api.github.com", timeout=20) as c: r=await c.request(method,path,headers=headers,**kwargs)
        except httpx.HTTPError as e: raise BatonError(f"GitHub request failed: {e}",502)
        if r.status_code>=400: raise BatonError(r.json().get("message","GitHub request failed") if r.headers.get("content-type","" ).startswith("application/json") else "GitHub request failed", r.status_code)
        return r.json()
    @staticmethod
    def validate_repo_url(url:str)->tuple[str,str]:
        m=re.fullmatch(r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)/?",url.strip())
        if not m: raise BatonError("repo_url must be a public github.com owner/repository URL")
        return m.group(1),m.group(2)
    async def repository(self,owner,repo): return await self.request("GET",f"/repos/{owner}/{repo}")
    async def branches(self,owner,repo): return await self.request("GET",f"/repos/{owner}/{repo}/branches",params={"per_page":100})
    async def tree(self,owner,repo,branch,path=""):
        ref=branch or "HEAD"; data=await self.request("GET",f"/repos/{owner}/{repo}/git/trees/{ref}",params={"recursive":"1"})
        prefix=path.strip("/")
        return [x for x in data.get("tree",[]) if not prefix or x.get("path","")==prefix or x.get("path","").startswith(prefix+"/")]
    async def file(self,owner,repo,branch,path):
        data=await self.request("GET",f"/repos/{owner}/{repo}/contents/{path.lstrip('/')}",params={"ref":branch})
        if isinstance(data,list) or data.get("type")!="file": raise BatonError("Requested path is not a file")
        if data.get("size",0)>get_settings().max_file_size_bytes: raise BatonError("File exceeds configured size limit",413)
        try: content=base64.b64decode(data.get("content","")).decode("utf-8")
        except (ValueError,UnicodeDecodeError): raise BatonError("Binary files are not supported")
        return {"path":data["path"],"size":data.get("size",len(content.encode())),"content":content}
