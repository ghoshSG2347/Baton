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

const BASE_URL = import.meta.env.VITE_BATON_API_URL || 'http://localhost:8000';
const BATON_KEY = import.meta.env.VITE_BATON_ACCESS_KEY || '';

function getHeaders(githubToken?: string): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (BATON_KEY) headers['X-Baton-Key'] = BATON_KEY;
  if (githubToken) headers['X-GitHub-Token'] = githubToken;
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Request failed' }));
    const error = new Error(body.detail || `HTTP ${res.status}`) as Error & {
      status: number;
      detail: string;
    };
    error.status = res.status;
    error.detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    throw error;
  }
  return res.json() as Promise<T>;
}

export interface ApiError extends Error {
  status: number;
  detail: string;
}

export const batonApi = {
  async checkHealth(): Promise<{ status: string; service: string }> {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse(res);
  },

  async validateRepository(
    repoUrl: string,
    githubToken?: string
  ): Promise<RepoValidation> {
    const res = await fetch(`${BASE_URL}/api/v1/github/validate-repository`, {
      method: 'POST',
      headers: getHeaders(githubToken),
      body: JSON.stringify({ repo_url: repoUrl }),
    });
    return handleResponse(res);
  },

  async getBranches(owner: string, repo: string, githubToken?: string): Promise<Branch[]> {
    const params = new URLSearchParams({ owner, repo });
    const res = await fetch(`${BASE_URL}/api/v1/github/branches?${params}`, {
      headers: getHeaders(githubToken),
    });
    const data = await handleResponse<{ branches: Branch[] }>(res);
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
    const res = await fetch(`${BASE_URL}/api/v1/github/tree?${params}`, {
      headers: getHeaders(githubToken),
    });
    const data = await handleResponse<{ items: TreeItem[] }>(res);
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
    const res = await fetch(`${BASE_URL}/api/v1/github/file?${params}`, {
      headers: getHeaders(githubToken),
    });
    return handleResponse(res);
  },

  async analyzeFolder(
    owner: string,
    repo: string,
    branch: string,
    folder: string,
    githubToken?: string
  ): Promise<AnalysisResult> {
    const res = await fetch(`${BASE_URL}/api/v1/analysis/folder`, {
      method: 'POST',
      headers: getHeaders(githubToken),
      body: JSON.stringify({ owner, repo, branch, folder }),
    });
    return handleResponse(res);
  },

  async analyzeRepository(
    owner: string,
    repo: string,
    branch: string,
    githubToken?: string
  ): Promise<AnalysisResult> {
    const res = await fetch(`${BASE_URL}/api/v1/analysis/repository`, {
      method: 'POST',
      headers: getHeaders(githubToken),
      body: JSON.stringify({ owner, repo, branch }),
    });
    return handleResponse(res);
  },

  async generateContext(
    owner: string,
    repo: string,
    branch: string,
    folder: string,
    includeMarkdown: boolean,
    githubToken?: string
  ): Promise<ContextResult> {
    const res = await fetch(`${BASE_URL}/api/v1/context`, {
      method: 'POST',
      headers: getHeaders(githubToken),
      body: JSON.stringify({ owner, repo, branch, folder, include_markdown: includeMarkdown }),
    });
    return handleResponse(res);
  },

  async generatePrompt(
    task: string,
    context: string,
    constraints: string[],
    githubToken?: string
  ): Promise<PromptResult> {
    const res = await fetch(`${BASE_URL}/api/v1/prompt`, {
      method: 'POST',
      headers: getHeaders(githubToken),
      body: JSON.stringify({ task, context, constraints }),
    });
    return handleResponse(res);
  },

  async detectConflicts(
    branches: Record<string, string[]>,
    files: string[] = [],
    githubToken?: string
  ): Promise<ConflictResult> {
    const res = await fetch(`${BASE_URL}/api/v1/conflicts`, {
      method: 'POST',
      headers: getHeaders(githubToken),
      body: JSON.stringify({ files, branches }),
    });
    return handleResponse(res);
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
    const res = await fetch(`${BASE_URL}/api/v1/integration`, {
      method: 'POST',
      headers: getHeaders(githubToken),
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  },
};
