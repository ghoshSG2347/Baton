from app.generators.context_generator import generate
from app.core.config import get_settings
from app.schemas.context import ContextOptions
from app.services.context_snapshot import ContextSnapshotService
from app.core.exceptions import BatonError
from app.generators.context_builder import scrub
from app.core.secrets import secret_values


class ContextService:
    def __init__(self, snapshot_service=None):
        self.snapshots = snapshot_service

    async def create(self, req, token=None, allow_snapshot=False):
        snapshots = self.snapshots or ContextSnapshotService(token)
        if allow_snapshot:
            intelligence = await snapshots.load(req.owner, req.repo, req.branch, req.folder, req.commit, allow_snapshot=True)
        else:
            intelligence = await snapshots.load(req.owner, req.repo, req.branch, req.folder, req.commit)
        options = ContextOptions(context_type=req.context_type, member=req.member, task=req.task, constraints=req.constraints)
        secrets = secret_values(token, getattr(getattr(snapshots, 'github', None), 'token', None))
        result = generate(intelligence, min(req.max_bytes or get_settings().max_total_context_bytes,
                                           get_settings().max_total_context_bytes), options=options,
                          known_secrets=secrets)
        result['context']['identity']['current_head'] = getattr(snapshots, 'current_commit', intelligence.commit)
        if getattr(snapshots, 'historical', False):
            result['context']['identity']['snapshot_status'] = 'STALE'
            warning = f'Based on older snapshot {intelligence.commit}; current branch HEAD is {snapshots.current_commit}. Repository changed since the current intelligence snapshot.'
            result['context']['warnings'] = [warning]
            result['markdown'] = '> STALE: ' + warning + '\n\n' + result['markdown'].replace('**Snapshot status:** `CURRENT`', '**Snapshot status:** `STALE`')
        if req.include_markdown and not result['context']['usable']:
            raise BatonError('Context byte budget cannot retain a usable briefing. Increase max_bytes and the configured context limit.', 413)
        if not req.include_markdown:
            result['markdown'] = ''
            result['estimated_tokens'] = 0
        return {'analysis': scrub(intelligence.to_legacy_analysis(), secrets),
                'project_types': [kind.value for kind in intelligence.project_types], **result}
