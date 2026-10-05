"""Authorized, commit-pinned collection feeding the single canonical pipeline."""
from datetime import datetime, timezone
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.core.secrets import secret_values
from app.services.github_service import GitHubService
from app.utils.file_filters import is_relevant
from app.intelligence import pipeline, snapshot
from app.intelligence.safety import sensitive_path, sanitize_file, sanitize_model
from app.analyzers.documentation_analyzer import _classify_doc_path

class AnalysisService:
    def __init__(self, token=None, store=None):
        self.github = GitHubService(token)
        self.store = store or snapshot._DEFAULT

    async def analyze(self, owner, repo, branch, folder=""):
        return (await self.analyze_intelligence(owner, repo, branch, folder)).to_legacy_analysis()

    async def analyze_intelligence(self, owner, repo, branch, folder=""):
        settings = get_settings()
        if not branch:
            repository = await self.github.repository(owner, repo)
            branch = repository.get('default_branch') or 'HEAD'
        # Resolve and authorize on EVERY request, including cache hits. Tree SHA
        # is not commit SHA; pin all subsequent reads to this resolved commit.
        try:
            state = await self.github.commit(owner, repo, branch)
        except BatonError as exc:
            if exc.status_code != 409:
                raise
            # GitHub returns 409 for repositories without commits. No reusable
            # exact-state snapshot can exist yet.
            return pipeline.run([], {}, dict(owner=owner, repo=repo, branch=branch,
                                commit=None, folder=folder.strip('/'),
                                analysis_warnings=['Repository has no resolvable commit; snapshot is not cached.']), [])
        commit = state.get('sha')
        if not commit:
            raise BatonError('GitHub did not return an exact commit', 502)
        folder = folder.strip('/')
        cached = self.store.load(owner, repo, branch, commit, folder)
        if cached is not None:
            return sanitize_model(cached, secret_values(self.github.token))
        stale = any(x['owner'].lower() == owner.lower() and x['repo'].lower() == repo.lower() and x['branch'] == branch and x['folder'] == folder and x['commit'] != commit for x in self.store.metadata())
        tree = await self.github.tree_snapshot(owner, repo, commit)
        items = [x for x in tree.get('tree', []) if not folder or x.get('path') == folder or x.get('path', '').startswith(folder + '/')]
        contents, omissions = {}, {}
        total_bytes, attempts = 0, 0
        # Discover intent first, followed by manifests/config, then remaining code.
        def priority(x):
            path = x.get('path', '')
            if _classify_doc_path(path): return (0, path)
            if path.endswith(('package.json', '.toml', 'requirements.txt', '.env.example')): return (1, path)
            return (2, path)
        for item in sorted(items, key=priority):
            if item.get('type') != 'blob':
                continue
            path = item['path']
            reason = None
            if sensitive_path(path): reason = 'sensitive_file'
            elif not is_relevant(path): reason = 'filtered_or_binary'
            elif (item.get('size') or 0) > settings.max_file_size_bytes: reason = 'file_size_limit'
            elif attempts >= settings.max_files_per_analysis: reason = 'file_count_limit'
            elif total_bytes + (item.get('size') or 0) > settings.max_total_context_bytes: reason = 'total_byte_limit'
            if reason:
                omissions[path] = reason
                continue
            attempts += 1
            try:
                data = await self.github.file(owner, repo, commit, path)
                text = data['content']
                size = len(text.encode('utf-8'))
                if size > settings.max_file_size_bytes:
                    omissions[path] = 'file_size_limit'
                elif total_bytes + size > settings.max_total_context_bytes:
                    omissions[path] = 'total_byte_limit'
                else:
                    total_bytes += size
                    contents[path] = sanitize_file(path, text, secret_values(self.github.token))
            except BatonError as exc:
                if exc.status_code in {401, 403, 429}:
                    raise  # never cache an authorization/rate-limit failure
                omissions[path] = 'unreadable_file'
        warnings = []
        if stale: warnings.append('Repository has changed since the previous analysis snapshot.')
        if tree.get('truncated'): warnings.append('GitHub returned a truncated tree; inventory is incomplete.')
        metadata = dict(owner=owner, repo=repo, branch=branch, folder=folder, commit=commit,
                        generated=datetime.now(timezone.utc).isoformat(), files_analyzed=len(contents),
                        analysis_warnings=warnings, omission_reasons=omissions, tree_truncated=bool(tree.get('truncated')))
        intelligence = pipeline.run(items, contents, metadata, list(omissions))
        intelligence = sanitize_model(intelligence, secret_values(self.github.token))
        self.store.save(intelligence)
        return intelligence
