import type { WorkspaceInspection, WorkspaceRequest } from '@/types';

import { BatonApiError } from '@/lib/api/batonApi';



export type RepositoryState = 'TOKEN_REQUIRED' | 'TOKEN_INVALID' | 'INSUFFICIENT_PERMISSIONS' | 'REPOSITORY_NOT_FOUND' | 'NETWORK_ERROR' | 'DISCONNECTED' | 'CONNECTING' | 'CONNECTED' | 'ANALYZING' | 'READY' | 'NOT_ANALYZED' | 'STALE' | 'ANALYSIS_FAILED' | 'REQUEST_FAILED' | 'PERMISSION_DENIED' | 'RATE_LIMITED' | 'INVALID_REPOSITORY' | 'SNAPSHOT_INVALID' | 'EMPTY_REPOSITORY' | 'CONFIGURATION_INCOMPLETE';

export type Severity = 'info' | 'warning' | 'error' | 'success';

export type StatusMessage = { state: RepositoryState; severity: Severity; title: string; explanation: string };



export function requestFailure(error: unknown, operation = 'request'): StatusMessage {

  const code = error instanceof BatonApiError ? error.code : '';

  const status = error instanceof BatonApiError ? error.status : -1;

  if (code.startsWith('conversation_')) return { state: 'REQUEST_FAILED', severity: 'warning', title: 'Chat session needs attention', explanation: error instanceof Error ? error.message : 'Start a new chat and retry your question.' };

  if (code === 'sensitive_source_path') return { state: 'PERMISSION_DENIED', severity: 'info', title: 'Credential file cannot be displayed', explanation: 'Choose a source file that does not contain credentials.' };
  if (code === 'invalid_source_path') return { state: 'REQUEST_FAILED', severity: 'error', title: 'Invalid source path', explanation: 'Choose a file inside the selected repository without traversal segments.' };
  if (code === 'ai_configuration_incomplete') return repositoryMessage('CONFIGURATION_INCOMPLETE');
  if (code.startsWith('ai_provider_')) return { state: 'REQUEST_FAILED', severity: 'error', title: ({ ai_provider_authentication_failure: 'Gemini authentication failed', ai_provider_rate_limit: 'Gemini rate limit reached', ai_provider_timeout: 'Gemini response timed out', ai_provider_invalid_response: 'Gemini response was rejected', ai_provider_busy: 'AI capacity is busy' } as Record<string, string>)[code] || 'AI provider request failed', explanation: error instanceof Error ? error.message : 'Review backend provider configuration and quota, then retry.' };

  if (code === 'invalid_repository_url' || status === 422) return { state: 'INVALID_REPOSITORY', severity: 'error', title: 'Invalid repository or branch', explanation: 'Check the repository URL, selected branch and request settings.' };

  if (code === 'github_token_required') return { state: 'TOKEN_REQUIRED', severity: 'warning', title: 'GitHub token required', explanation: 'Baton uses your Fine-grained GitHub token for authenticated repository access and higher API limits. Enter your token in Repository. Required: Metadata — Read and Contents — Read.' };
  if (code === 'github_insufficient_permissions') return { state: 'INSUFFICIENT_PERMISSIONS', severity: 'error', title: 'Insufficient repository permissions', explanation: 'Your token authenticated, but GitHub denied the required read operation. Select this repository and grant Metadata — Read and Contents — Read. Check organization approval.' };
  if (code === 'github_authentication_failure') return { state: 'TOKEN_INVALID', severity: 'error', title: 'GitHub token is invalid or expired', explanation: 'Replace your token in Repository and validate repository access again.' };

  if (status === 401) return { state: 'PERMISSION_DENIED', severity: 'error', title: 'Baton authentication required', explanation: 'Enter a valid Baton access key in workspace settings.' };

  if (code === 'github_rate_limit' && error instanceof BatonApiError) {
    const remaining = error.rateLimit?.remaining;
    const reset = error.rateLimit?.reset_at;
    const metadata = `${remaining !== undefined ? ` Requests remaining: ${remaining}.` : ''}${reset && remaining === 0 ? ` Reset: ${new Date(reset * 1000).toLocaleString()}.` : ''}`;
    return { state: 'RATE_LIMITED', severity: 'warning', title: 'GitHub API limit reached', explanation: `GitHub has temporarily limited requests for this account. Baton will not retry aggressively.${metadata}${error.rateLimitKind === 'secondary' ? ' A secondary limit requires a backoff period.' : ''} Wait until the reset or backoff period ends. Check GitHub access in Repository to verify your token.` };
  }

  if (status === 429) return { state: 'RATE_LIMITED', severity: 'warning', title: 'Request limit reached', explanation: 'The service is busy or its quota is exhausted. Try again later.' };
  if (status === 504) return { state: 'REQUEST_FAILED', severity: 'error', title: 'Request timed out', explanation: 'The service took too long to respond. Retry the operation.' };
  if (status === 403) return { state: 'PERMISSION_DENIED', severity: 'error', title: 'GitHub denied the request', explanation: 'Check token permissions and organization access. GitHub may also restrict requests temporarily.' };

  if (code === 'github_not_found' || status === 404) return { state: 'REPOSITORY_NOT_FOUND', severity: 'error', title: 'Repository or branch not found', explanation: 'Check the URL and branch. Private repositories need a GitHub token with access.' };

  if (code === 'empty_repository') return { state: 'EMPTY_REPOSITORY', severity: 'info', title: 'No commits to analyze', explanation: 'Add a commit to this repository, then analyze its branch.' };

  if (code === 'snapshot_required') return repositoryMessage('NOT_ANALYZED');

  if (code === 'snapshot_stale') return repositoryMessage('STALE');

  if (code === 'snapshot_invalid') return repositoryMessage('SNAPSHOT_INVALID');

  if (code === 'github_network_failure' || code === 'network_failure' || status === 0) return { state: 'NETWORK_ERROR', severity: 'error', title: 'Could not reach the repository service', explanation: 'Check your connection and retry. The backend or GitHub may be temporarily unavailable.' };

  if (code === 'ai_configuration_incomplete') return repositoryMessage('CONFIGURATION_INCOMPLETE');

  const titles: Record<string, string> = { analysis: 'Analysis failed', chat: 'Baton could not answer', artifact: 'Artifact generation failed', compare: 'Branch comparison failed', branch: 'Branches could not be loaded', connection: 'Repository connection failed', context: 'Context generation failed', prompt: 'Prompt generation failed', integration: 'Integration check failed', conflicts: 'Conflict check failed' };

  return { state: operation === 'analysis' ? 'ANALYSIS_FAILED' : 'REQUEST_FAILED', severity: 'error', title: titles[operation] || 'Request failed', explanation: operation === 'analysis' ? 'Baton could not create a valid repository analysis. Retry when the repository service is available.' : 'Baton could not complete this operation. Review the technical details or retry.' };

}



export function repositoryMessage(state: RepositoryState): StatusMessage {

  const messages: Partial<Record<RepositoryState, [Severity, string, string]>> = {

    CONNECTING: ['info', 'Checking branch', 'Resolving the current commit and checking for an existing analysis.'],

    DISCONNECTED: ['info', 'Connect a repository', 'Connect a GitHub repository and choose a branch to begin.'],
    CONNECTED: ['info', 'Repository connected', 'Choose a branch and analyze it to prepare repository context.'],

    ANALYZING: ['info', 'Analyzing branch…', 'Reading repository files and creating context for this commit. Chat becomes available when analysis is ready.'],

    NOT_ANALYZED: ['warning', 'Analysis required', 'This branch is connected. Analyze it before asking Baton about the repository.'],

    STALE: ['warning', 'Snapshot is out of date', 'The branch changed after its last analysis. Re-analyze it to use the current commit.'],

    READY: ['success', 'Current', 'Repository intelligence is synchronized with the selected branch and commit.'],

    SNAPSHOT_INVALID: ['error', 'Analysis needs to be rebuilt', 'The stored analysis could not be validated for this branch. Re-analyze the branch.'],

    EMPTY_REPOSITORY: ['info', 'No repository files to analyze', 'Add a commit with project files, then analyze this branch.'],

    CONFIGURATION_INCOMPLETE: ['info', 'AI chat is not configured', 'Server configuration is needed for AI chat. Repository context, artifacts and branch comparison remain available.'],

  };

  const [severity, title, explanation] = messages[state] || ['error', 'Analysis failed', 'Baton could not create a valid analysis. Retry the operation.'];

  return { state, severity, title, explanation };

}



export function snapshotState(inspection: WorkspaceInspection, request: WorkspaceRequest): RepositoryState {

  const identity = inspection.identity;

  if (identity.repository.toLowerCase() !== `${request.owner}/${request.repo}`.toLowerCase() || identity.branch !== request.branch || identity.project_root.replace(/^\/+|\/+$/g, '') !== request.folder.replace(/^\/+|\/+$/g, '')) return 'SNAPSHOT_INVALID';

  if (inspection.state === 'EMPTY_REPOSITORY') return 'EMPTY_REPOSITORY';

  const head = identity.current_head;

  if (!head) return 'SNAPSHOT_INVALID';

  if (identity.commit && identity.commit !== head) return 'STALE';

  if (inspection.available === false) return inspection.state === 'SNAPSHOT_INVALID' ? 'SNAPSHOT_INVALID' : 'NOT_ANALYZED';

  if (inspection.available !== true || !identity.commit || !identity.snapshot_id || !['CURRENT', 'PARTIAL'].includes(identity.snapshot_status)) return 'SNAPSHOT_INVALID';

  return 'READY';

}



export function analysisAction(state: RepositoryState): string {

  if (state === 'READY') return 'Refresh analysis';

  if (state === 'STALE' || state === 'SNAPSHOT_INVALID') return 'Re-analyze branch';

  if (['ANALYSIS_FAILED', 'REQUEST_FAILED', 'PERMISSION_DENIED', 'RATE_LIMITED', 'INVALID_REPOSITORY'].includes(state)) return 'Retry analysis';

  return 'Analyze branch';

}
