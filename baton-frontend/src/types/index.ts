export interface Branch {
  name: string;
  sha: string;
}

export interface TreeItem {
  path: string;
  type: 'blob' | 'tree' | string;
  size: number | null;
  sha?: string | null;
}

export interface FileContent {
  path: string;
  size: number;
  content: string;
  language?: string | null;
}

export interface RepoValidation {
  owner: string;
  repository: string;
  default_branch?: string | null;
  visibility?: string | null;
  accessible: boolean;
}

export interface AnalysisMetadata {
  owner: string;
  repo: string;
  branch: string;
  folder: string;
  commit: string;
  generated: string;
  files_analyzed: number;
  skipped_files: string[];
}

export interface AnalysisResult {
  metadata: AnalysisMetadata;
  stack: {
    detected: string[];
    languages: string[];
  };
  file_tree: { path: string; type: string; size: number }[];
  important_files: string[];
  routes: string[];
  api_calls: string[];
  environment_variables: string[];
  types: string[];
  mock_data: string[];
  handoffs: { path: string; items: string[] }[];
  shared_files: string[];
  stray_files: string[];
  analysis_warnings: string[];
}

export interface ContextResult {
  analysis: AnalysisResult;
  markdown: string;
  estimated_tokens: number;
  omitted: string[];
}

export interface PromptResult {
  prompt: string;
}

export interface Conflict {
  path: string;
  branches: string[];
  reason: string;
}

export interface ConflictResult {
  conflicts: Conflict[];
  conflict_count: number;
}

export interface IntegrationComparison {
  frontend_routes: string[];
  backend_routes: string[];
  unmatched_frontend_routes: string[];
  unmatched_backend_routes: string[];
  compatible: boolean;
}

export interface IntegrationResult {
  owner: string;
  repo: string;
  branch: string;
  status: string;
  comparison?: IntegrationComparison;
  message?: string;
}

export interface TeamMember {
  id: string;
  name: string;
  github: string;
  branch: string;
  role: string;
  folders: string[];
  job: string;
  depends_on: string[];
  provides_to: string[];
}

export type DataState = 'idle' | 'loading' | 'success' | 'partial' | 'error' | 'stale';

export type WorkspaceSection =
  | 'overview'
  | 'repository'
  | 'team'
  | 'analysis'
  | 'context'
  | 'prompt'
  | 'conflicts'
  | 'integration';
