"""Authorized, commit-pinned collection feeding the single canonical pipeline."""
from datetime import datetime, timezone
import asyncio
import logging
from copy import deepcopy
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.core.secrets import secret_values
from app.services.github_service import GitHubService
from app.utils.file_filters import is_relevant
from app.intelligence import pipeline, snapshot
from app.intelligence.models import SnapshotStatus
from app.intelligence.safety import sensitive_path, sanitize_file, sanitize_model

class AnalysisService:
    _inflight = {}
    def __init__(self, token=None, store=None):
        self.github = GitHubService(token)
        self.store = store or snapshot._DEFAULT
        self._collected = False

    async def analyze(self, owner, repo, branch, folder="", *, force_refresh=False):
        return (await self.analyze_intelligence(owner, repo, branch, folder, force_refresh=force_refresh)).to_legacy_analysis()

    async def analyze_intelligence(self, owner, repo, branch, folder="", *, force_refresh=False):
        key = (asyncio.get_running_loop(), id(self.store), self.github.access_scope,
               owner.lower(), repo.lower(), branch, folder.strip('/'))
        if key in self._inflight:
            pending, collector = self._inflight[key]
            result = await asyncio.shield(pending)
            # A refresh can join a real collection, but must not be silently
            # satisfied by another caller's cache-only read.
            if force_refresh and not collector._collected:
                return await self.analyze_intelligence(owner, repo, branch, folder, force_refresh=True)
            return deepcopy(result)
        task = asyncio.create_task(self._collect(owner, repo, branch, folder, force_refresh=force_refresh))
        self._inflight[key] = (task, self)
        def finished(done):
            self._inflight.pop(key, None)
            self.github._content.clear()
            logging.getLogger('uvicorn.error.baton.analysis.metrics').debug(
                'analysis_requests token_present=%s token_source=%s counts=%s total=%s cache_hits=%s last_response=%s failed=%s',
                bool(self.github.token), self.github.token_source, dict(self.github.request_counts),
                sum(self.github.request_counts.values()), dict(self.github.cache_counts), self.github.last_response,
                done.cancelled() or done.exception() is not None)
        task.add_done_callback(finished)
        return deepcopy(await asyncio.shield(task))

    async def _collect(self, owner, repo, branch, folder="", *, force_refresh=False):
        settings = get_settings()
        self._collected = False
        self.github._content.clear()  # file reuse is confined to this collection
        self.github.request_counts.clear()
        self.github.cache_counts.clear()
        if not branch:
            repository = await self.github.repository(owner, repo)
            branch = repository.get('default_branch') or 'HEAD'
        # Use a recent token-scoped authorized HEAD observation for cache reads.
        # Explicit refresh always resolves GitHub HEAD. Tree SHA is not commit SHA.
        try:
            state = await self.github.commit(owner, repo, branch, fresh=True) if force_refresh else await self.github.commit(owner, repo, branch)
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
        cache_matches = cached is not None and (
            cached.owner.lower(), cached.repo.lower(), cached.branch, cached.commit,
            cached.project_root.strip('/'), cached.analysis_version) == (
            owner.lower(), repo.lower(), branch, commit, folder, '1.1')
        if cache_matches and cached.snapshot_status in {SnapshotStatus.CURRENT, SnapshotStatus.PARTIAL} and not force_refresh:
            self.github.cache_counts['snapshot'] += 1
            return sanitize_model(cached, secret_values(self.github.token))
        stale = any(x['owner'].lower() == owner.lower() and x['repo'].lower() == repo.lower() and x['branch'] == branch and x['folder'] == folder and x['commit'] != commit for x in self.store.metadata())
        self._collected = True
        archive_contents, archive_omissions = None, {}
        archive_warning = None
        tree = None
        if settings.github_archive_analysis:
            try:
                _, archive_contents, archive_omissions = await self.github.archive(owner, repo, commit, folder)
                # Retain Git's authoritative blob/mode/tree evidence. Verify every
                # selected archive byte against the exact commit's Git blob SHA,
                # including repositories configured to expand LFS in archives.
                tree = await self.github.tree_snapshot(owner, repo, commit)
                expected = {item['path']: item.get('sha') for item in tree.get('tree', []) if item.get('type') == 'blob'}
                if tree.get('truncated') or any(expected.get(path) != data['sha'] for path, data in archive_contents.items()):
                    raise BatonError('Archive content does not match verified Git blob evidence.', 409, 'archive_collection_unavailable')
            except BatonError as exc:
                if exc.code != 'archive_collection_unavailable':
                    raise  # Auth/quota/transport failures must never trigger a second collection.
                archive_contents = None
                archive_warning = 'Archive unavailable within safety bounds; used bounded tree/content collection.'
        if tree is None:
            tree = await self.github.tree_snapshot(owner, repo, commit)
        items = [x for x in tree.get('tree', []) if not folder or x.get('path') == folder or x.get('path', '').startswith(folder + '/')]
        contents, omissions = {}, {}
        total_bytes, attempts = 0, 0
        # Discover intent first, followed by manifests/config, then remaining code.
        seen = set()
        for item in sorted(items, key=GitHubService.collection_priority):
            if item.get('type') != 'blob':
                continue
            path = item['path']
            if path in seen:
                continue
            seen.add(path)
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
                if archive_contents is not None:
                    if path not in archive_contents:
                        omissions[path] = archive_omissions.get(path, 'unreadable_file')
                        continue
                    data = archive_contents.pop(path)
                else:
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
                if exc.status_code in {401, 403, 429} or exc.code in {'github_network_failure', 'github_timeout', 'github_api_failure'}:
                    raise  # never cache an authorization/rate-limit failure
                omissions[path] = 'unreadable_file'
        warnings = []
        if archive_warning: warnings.append(archive_warning)
        if stale: warnings.append('Repository has changed since the previous analysis snapshot.')
        if tree.get('truncated'): warnings.append('GitHub returned a truncated tree; inventory is incomplete.')
        metadata = dict(owner=owner, repo=repo, branch=branch, folder=folder, commit=commit,
                        generated=datetime.now(timezone.utc).isoformat(), files_analyzed=len(contents),
                        analysis_warnings=warnings, omission_reasons=omissions, tree_truncated=bool(tree.get('truncated')))
        intelligence = pipeline.run(items, contents, metadata, list(omissions))
        intelligence = sanitize_model(intelligence, secret_values(self.github.token))
        self.store.save(intelligence)
        retained = self.store.load(owner, repo, branch, commit, folder)
        if retained is None or retained.generated != intelligence.generated:
            raise BatonError('Analysis could not be retained within the backend snapshot storage limits.', 503, 'snapshot_not_stored')
        return intelligence
