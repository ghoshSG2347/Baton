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

  constructor(message: string, status: number = 0, detail?: string, code: string = 'baton_backend_failure') {
    super(message);
    this.name = 'BatonApiError';
    this.status = status;
    this.detail = detail || message;
    this.code = code;
  }
}

export type ApiError = BatonApiError;

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
    try {
      const body = await res.json();
      if (typeof body.code === 'string') errorCode = body.code;
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
    throw new BatonApiError(message, res.status, message, errorCode);
  }

  try {
    return await res.json() as T;
  } catch {
    throw new BatonApiError('Baton backend returned an invalid response.', res.status);
  }
}

export const batonApi = {
  async inspectWorkspace(request: WorkspaceRequest, token?: string): Promise<WorkspaceInspection> {
    return apiRequest('/api/v1/workspace/inspect', { method: 'POST', body: JSON.stringify(request) }, token);
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
    const params = new URLSearchParams({ owner, repo });
    const data = await apiRequest<{ branches: Branch[] }>(
      `/api/v1/github/branches?${params}`,
      { method: 'GET' },
      githubToken
    );
    return data.branches;
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
    githubToken?: string
  ): Promise<AnalysisResult> {
    return apiRequest<AnalysisResult>(
      '/api/v1/analysis/folder',
      {
        method: 'POST',
        body: JSON.stringify({ owner, repo, branch, folder }),
      },
      githubToken
    );
  },

  async analyzeRepository(
    owner: string,
    repo: string,
    branch: string,
    githubToken?: string
  ): Promise<AnalysisResult> {
    return apiRequest<AnalysisResult>(
      '/api/v1/analysis/repository',
      {
        method: 'POST',
        body: JSON.stringify({ owner, repo, branch }),
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
