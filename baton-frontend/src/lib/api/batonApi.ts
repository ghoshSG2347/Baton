import type {
  Branch,
  TreeItem,
  FileContent,
  RepoValidation,
  AnalysisResult,
  ContextResult,
  PromptResult,
  ConflictResult,
  IntegrationResult,
} from '@/types';
import type { WorkspaceRequest, WorkspaceInspection, ChatAnswer, WorkspaceArtifact, ArtifactType, BranchComparison } from '@/types';
import { redactUserText } from '@/lib/utils/redaction';

const RAW_URL = import.meta.env.VITE_BATON_API_URL || 'http://localhost:8000';
const BASE_URL = RAW_URL.replace(/\/+$/, '');
let batonAccessKey = '';
export function setBatonAccessKey(value: string) { batonAccessKey = value; }

export class BatonApiError extends Error {
  status: number;
  detail: string;
  code: string;
  rateLimit?: GitHubRateLimit;
  retryAt?: number;
  rateLimitKind?: string;

  constructor(message: string, status: number = 0, detail?: string, code: string = 'baton_backend_failure') {
    super(message);
    this.name = 'BatonApiError';
    this.status = status;
    this.detail = detail || message;
    this.code = code;
  }
}

export type GitHubRateLimit = { limit?: number; remaining?: number; used?: number; reset_at?: number };
export type GitHubAccess = { authenticated: boolean; token_present: boolean; token_source: 'request' | 'server' | 'none'; upstream_status: number; rate_limit: GitHubRateLimit };

export type ApiError = BatonApiError;
// Concurrent mounted views share this read. Keys/credentials exist only until
// the request settles; nothing is persisted in browser storage.
const branchReads = new Map<string, Promise<Branch[]>>();

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  githubToken?: string
): Promise<T> {
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${BASE_URL}${normalizedEndpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (batonAccessKey) headers['X-Baton-Key'] = batonAccessKey;
  if (githubToken?.trim()) headers['X-GitHub-Token'] = githubToken.trim();

  let res: Response;
  try {
    res = await fetch(url, { ...options, headers });
  } catch {
    throw new BatonApiError(
      'Unable to reach Baton backend. Check the backend URL or network connection.',
      0, undefined, 'network_failure'
    );
  }

  if (!res.ok) {
    let bodyDetail = '';
    let errorCode = 'baton_backend_failure';
    let rateLimit: GitHubRateLimit | undefined;
    let retryAfter: number | undefined;
    let rateLimitKind: string | undefined;
    try {
      const body = await res.json();
      if (typeof body.code === 'string') errorCode = body.code;
      if (body.rate_limit && typeof body.rate_limit === 'object') {
        rateLimit = {};
        for (const key of ['limit', 'remaining', 'used', 'reset_at'] as const) {
          const value = body.rate_limit[key];
          if (typeof value === 'number' && Number.isFinite(value) && value >= 0) rateLimit[key] = value;
        }
      }
      if (typeof body.retry_after === 'number' && Number.isFinite(body.retry_after) && body.retry_after >= 0) retryAfter = body.retry_after;
      if (['primary', 'secondary', 'unknown'].includes(body.rate_limit_kind)) rateLimitKind = body.rate_limit_kind;
      if (typeof body.detail === 'string') {
        bodyDetail = body.detail;
      } else if (Array.isArray(body.detail)) {
        bodyDetail = body.detail.map((e: { msg?: string; loc?: string[] }) => e.msg || JSON.stringify(e)).join(', ');
      } else if (body.detail) {
        bodyDetail = JSON.stringify(body.detail);
      }
    } catch {
      // response wasn't JSON
    }

    let defaultMsg = `Request failed with status ${res.status}`;
    if (res.status === 401) {
      defaultMsg = 'Baton authentication failed. Invalid or missing access key.';
    } else if (res.status === 403) {
      defaultMsg = 'GitHub access denied. Check the GitHub token and repository permissions.';
    } else if (res.status === 404) {
      defaultMsg = 'Repository or Baton endpoint not found.';
    } else if (res.status === 422) {
      defaultMsg = 'Invalid repository request. Check the repository URL.';
    } else if (res.status >= 500) {
      defaultMsg = 'Baton backend encountered an internal error.';
    }

    const message = redactUserText(bodyDetail || defaultMsg, [githubToken || '', batonAccessKey]);
    const failure = new BatonApiError(message, res.status, message, errorCode);
    failure.rateLimit = rateLimit;
    failure.rateLimitKind = rateLimitKind;
    if (errorCode === 'github_rate_limit') {
      failure.retryAt = Math.max(rateLimit?.remaining === 0 ? (rateLimit.reset_at || 0) * 1000 : 0,
        Date.now() + (retryAfter ?? (rateLimit?.remaining === 0 && rateLimit.reset_at ? 0 : 60)) * 1000);
    }
    throw failure;
  }

  try {
    return await res.json() as T;
  } catch {
    throw new BatonApiError('Baton backend returned an invalid response.', res.status);
  }
}

export const batonApi = {
  async checkGitHubAccess(token?: string): Promise<GitHubAccess> {
    const result = await apiRequest<GitHubAccess>('/api/v1/github/access', { method: 'GET' }, token);
    if (typeof result?.authenticated !== 'boolean' || !result.rate_limit || !['request', 'server', 'none'].includes(result.token_source)) {
      throw new BatonApiError('Baton backend returned an invalid GitHub access response.', 502);
    }
    return result;
  },
  async inspectWorkspace(request: WorkspaceRequest, token?: string): Promise<WorkspaceInspection> {
    const result = await apiRequest<WorkspaceInspection>('/api/v1/workspace/inspect', { method: 'POST', body: JSON.stringify(request) }, token);
    const identity = result?.identity;
    if (!identity || typeof identity.repository !== 'string' || typeof identity.branch !== 'string'
      || typeof identity.project_root !== 'string' || typeof identity.commit !== 'string'
      || !result.completeness || typeof result.completeness.status !== 'string'
      || !Array.isArray(result.sections) || !Array.isArray(result.omission_manifest)
      || typeof result.provider?.configured !== 'boolean') {
      throw new BatonApiError('Baton backend returned an invalid analysis response.', 502, undefined, 'snapshot_invalid');
    }
    return result;
  },
  async chat(request: WorkspaceRequest & { message: string; conversation_id?: string }, token?: string, signal?: AbortSignal): Promise<ChatAnswer> {
    return apiRequest('/api/v1/workspace/chat', { method: 'POST', body: JSON.stringify(request), signal }, token);
  },
  async artifact(request: WorkspaceRequest & { artifact_type: ArtifactType; target?: string }, token?: string): Promise<WorkspaceArtifact> {
    return apiRequest('/api/v1/workspace/artifacts', { method: 'POST', body: JSON.stringify(request) }, token);
  },
  async compareBranches(request: WorkspaceRequest & { compare_branch: string; compare_commit?: string }, token?: string): Promise<BranchComparison> {
    return apiRequest('/api/v1/workspace/compare', { method: 'POST', body: JSON.stringify(request) }, token);
  },
  async source(request: WorkspaceRequest & { path: string; start_line?: number }, token?: string): Promise<{ path: string; content: string; start_line: number; end_line: number; partial: boolean; identity: { commit: string } }> {
    return apiRequest('/api/v1/workspace/source', { method: 'POST', body: JSON.stringify(request) }, token);
  },
  async checkHealth(): Promise<{ status: string; service: string }> {
    return apiRequest<{ status: string; service: string }>('/api/health');
  },

  async validateRepository(
    repoUrl: string,
    githubToken?: string
  ): Promise<RepoValidation> {
    return apiRequest<RepoValidation>(
      '/api/v1/github/validate-repository',
      {
        method: 'POST',
        body: JSON.stringify({ repo_url: repoUrl }),
      },
      githubToken
    );
  },

  async getBranches(owner: string, repo: string, githubToken?: string): Promise<Branch[]> {
    const readKey = JSON.stringify([owner, repo, githubToken || '', batonAccessKey]);
    const pending = branchReads.get(readKey);
    if (pending) return pending;
    const read = (async () => {
    const params = new URLSearchParams({ owner, repo });
    const data = await apiRequest<{ branches: Branch[] }>(
      `/api/v1/github/branches?${params}`,
      { method: 'GET' },
      githubToken
    );
    if (!Array.isArray(data.branches) || data.branches.some((branch) => typeof branch.name !== 'string' || typeof branch.sha !== 'string')) {
      throw new BatonApiError('Baton backend returned an invalid branch list.', 502);
    }
    return data.branches;
    })();
    branchReads.set(readKey, read);
    try { return await read; }
    finally { branchReads.delete(readKey); }
  },

  async getTree(
    owner: string,
    repo: string,
    branch: string,
    path?: string,
    githubToken?: string
  ): Promise<TreeItem[]> {
    const params = new URLSearchParams({ owner, repo, branch });
    if (path) params.set('path', path);
    const data = await apiRequest<{ items: TreeItem[] }>(
      `/api/v1/github/tree?${params}`,
      { method: 'GET' },
      githubToken
    );
    if (!Array.isArray(data.items)) throw new BatonApiError('Baton backend returned an invalid file tree.', 502);
    return data.items;
  },

  async getFile(
    owner: string,
    repo: string,
    branch: string,
    path: string,
    githubToken?: string
  ): Promise<FileContent> {
    const params = new URLSearchParams({ owner, repo, branch, path });
    return apiRequest<FileContent>(
      `/api/v1/github/file?${params}`,
      { method: 'GET' },
      githubToken
    );
  },

  async analyzeFolder(
    owner: string,
    repo: string,
    branch: string,
    folder: string,
    githubToken?: string,
    forceRefresh = false
  ): Promise<AnalysisResult> {
    return apiRequest<AnalysisResult>(
      '/api/v1/analysis/folder',
      {
        method: 'POST',
        body: JSON.stringify({ owner, repo, branch, folder, force_refresh: forceRefresh }),
      },
      githubToken
    );
  },

  async analyzeRepository(
    owner: string,
    repo: string,
    branch: string,
    githubToken?: string,
    forceRefresh = false
  ): Promise<AnalysisResult> {
    return apiRequest<AnalysisResult>(
      '/api/v1/analysis/repository',
      {
        method: 'POST',
        body: JSON.stringify({ owner, repo, branch, force_refresh: forceRefresh }),
      },
      githubToken
    );
  },

  async generateContext(
    owner: string,
    repo: string,
    branch: string,
    folder: string,
    includeMarkdown: boolean,
    githubToken?: string
  ): Promise<ContextResult> {
    return apiRequest<ContextResult>(
      '/api/v1/context',
      {
        method: 'POST',
        body: JSON.stringify({ owner, repo, branch, folder, include_markdown: includeMarkdown }),
      },
      githubToken
    );
  },

  async generatePrompt(
    task: string,
    context: string,
    constraints: string[],
    githubToken?: string
  ): Promise<PromptResult> {
    return apiRequest<PromptResult>(
      '/api/v1/prompt',
      {
        method: 'POST',
        body: JSON.stringify({ task, context, constraints }),
      },
      githubToken
    );
  },

  async detectConflicts(
    branches: Record<string, string[]>,
    files: string[] = [],
    githubToken?: string
  ): Promise<ConflictResult> {
    return apiRequest<ConflictResult>(
      '/api/v1/conflicts',
      {
        method: 'POST',
        body: JSON.stringify({ files, branches }),
      },
      githubToken
    );
  },

  async checkIntegration(
    owner: string,
    repo: string,
    branch: string,
    frontendBranch?: string,
    backendBranch?: string,
    githubToken?: string
  ): Promise<IntegrationResult> {
    const body: Record<string, string> = { owner, repo, branch };
    if (frontendBranch) body.frontend_branch = frontendBranch;
    if (backendBranch) body.backend_branch = backendBranch;
    return apiRequest<IntegrationResult>(
      '/api/v1/integration',
      {
        method: 'POST',
        body: JSON.stringify(body),
      },
      githubToken
    );
  },
};
