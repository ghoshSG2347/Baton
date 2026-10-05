"""Opt-in live GitHub acceptance check. No provider request or credential output."""
import asyncio
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch
from app.intelligence.snapshot import MemorySnapshotStore
from app.schemas.workspace import ArtifactRequest, CompareRequest, WorkspaceRequest
from app.services.analysis_service import AnalysisService
from app.services.context_service import ContextService
from app.services.context_snapshot import ContextSnapshotService
from app.services.github_service import GitHubService
from app.services.workspace_retrieval import retrieve
from app.services.workspace_service import WorkspaceService


async def main():
    results = []
    original = GitHubService.request
    counts = Counter()
    async def counted(self, method, path, **kwargs):
        counts['tree' if '/git/trees/' in path else 'file' if '/contents/' in path else 'commit' if '/commits/' in path else 'metadata'] += 1
        return await original(self, method, path, **kwargs)
    with patch.object(GitHubService, 'request', counted):
        for owner, repo in [('octocat', 'Hello-World'), ('karpathy', 'micrograd')]:
            github = GitHubService()
            metadata = await github.repository(owner, repo)
            branch = metadata['default_branch']
            store = MemorySnapshotStore()
            intel = await AnalysisService(store=store).analyze_intelligence(owner, repo, branch)
            workspace = WorkspaceService(ContextService(ContextSnapshotService(store=store)))
            req = WorkspaceRequest(owner=owner, repo=repo, branch=branch, commit=intel.commit)
            inspection = await workspace.inspect(req)
            collected = dict(counts)
            input_sizes = []
            for question in ['Explain the project', 'Explain backend' if owner == 'octocat' else 'Explain the ML training pipeline', 'What is unfinished?']:
                context = await workspace.context(req)
                packet, _ = retrieve(context['context'], question, {'turns': []}, 32000)
                input_sizes.append(packet['retrieval']['input_bytes'])
            for kind in ['prd', 'technical_design', 'tasks', 'handoff', 'prompt']:
                artifact = await workspace.artifact(ArtifactRequest(**{**req.model_dump(), 'artifact_type': kind, 'task': 'Audit the documented implementation within configured ownership'}))
                assert intel.commit in artifact['content']
            assert counts['tree'] == collected.get('tree', 0) and counts['file'] == collected.get('file', 0)
            result = {'repository': f'{owner}/{repo}', 'branch': branch, 'commit': intel.commit,
                      'project_types': [t.value for t in intel.project_types], 'snapshot': inspection['identity']['snapshot_status'],
                      'files_analyzed': intel.completeness.files_fully_analyzed, 'input_bytes': input_sizes,
                      'analysis_tree_reads': collected['tree'], 'repeated_questions_additional_tree_reads': 0,
                      'repeated_questions_additional_file_reads': 0, 'artifacts': 5, 'live_provider_calls': 0}
            if owner == 'octocat':
                branches = await github.branches(owner, repo)
                other = next((b['name'] for b in branches if b['name'] != branch), None)
                if other:
                    await AnalysisService(store=store).analyze_intelligence(owner, repo, other)
                    comparison = await workspace.compare(CompareRequest(**req.model_dump(), compare_branch=other))
                    result['comparison'] = {'before': comparison['before']['branch'], 'after': comparison['after']['branch'],
                                            'before_commit': comparison['before']['commit'], 'after_commit': comparison['after']['commit']}
            results.append(result)
            print(json.dumps(result), flush=True)
    output = Path(__file__).parents[2] / 'baton-frontend/.test-output/public-acceptance.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({'results': results, 'github_calls': counts, 'private_access': 'Unavailable',
                                 'live_provider': 'Not tested: deployment key/model not supplied'}, indent=2))


if __name__ == '__main__': asyncio.run(main())
