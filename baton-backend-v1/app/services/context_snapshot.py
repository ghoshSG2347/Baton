"""Authorized snapshot reads. This service deliberately cannot analyze files."""
from app.core.exceptions import BatonError
from app.intelligence.models import SnapshotStatus
from app.intelligence.snapshot import _DEFAULT, SnapshotStore
from app.services.github_service import GitHubService


REFRESH_MESSAGE = 'The repository intelligence snapshot is unavailable/stale and must be refreshed.'


class ContextSnapshotService:
    def __init__(self, token=None, store: SnapshotStore | None = None):
        self.github = GitHubService(token)
        self.store = store if store is not None else _DEFAULT

    async def load(self, owner, repo, branch, folder='', expected_commit=None, allow_snapshot=False):
        if not branch:
            metadata = await self.github.repository(owner, repo)
            branch = metadata.get('default_branch') or 'HEAD'
        try:
            state = await self.github.commit(owner, repo, branch)
        except BatonError as exc:
            if exc.status_code == 409:
                raise BatonError(REFRESH_MESSAGE + ' No repository commit is available.', 409) from None
            raise
        current_commit = state.get('sha')
        self.current_commit = current_commit
        self.historical = bool(expected_commit and expected_commit != current_commit)
        if not current_commit or (self.historical and not allow_snapshot):
            raise BatonError(REFRESH_MESSAGE + ' The requested commit is not the current branch state.', 409)
        selected_commit = expected_commit if self.historical else current_commit
        intelligence = self.store.load(owner, repo, branch, selected_commit, folder.strip('/'))
        requested_key = (owner.lower(), repo.lower(), branch, selected_commit, folder.strip('/'), '1.1')
        actual_key = ((intelligence.owner.lower(), intelligence.repo.lower(), intelligence.branch,
                       intelligence.commit, intelligence.project_root.strip('/'), intelligence.analysis_version)
                      if intelligence is not None else None)
        if intelligence is None or actual_key != requested_key or intelligence.snapshot_status == SnapshotStatus.STALE:
            raise BatonError(REFRESH_MESSAGE + ' Run the existing repository/folder analysis endpoint explicitly.', 409)
        return intelligence
