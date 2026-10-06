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
  do_not_touch?: string[];
  team_scope?: string[];
}

export type DataState = 'idle' | 'loading' | 'success' | 'partial' | 'error' | 'stale';

export type WorkspaceSection =
  | 'ai'
  | 'overview'
  | 'repository'
  | 'team'
  | 'analysis'
  | 'context'
  | 'prompt'
  | 'conflicts'
  | 'integration';

export interface MemberContext {
  name?: string;
  role?: string;
  responsibilities: string[];
  ownership: string[];
  do_not_touch: string[];
  team_scope: string[];
}
export interface WorkspaceRequest {
  owner: string; repo: string; branch: string; folder: string;
  commit?: string; context_type: 'project' | 'role' | 'task' | 'ai_handoff';
  continue_snapshot?: boolean;
  member?: MemberContext; task?: string; constraints: string[];
}
export interface SnapshotIdentity {
  repository: string; branch: string; commit: string; project_root: string;
  snapshot_id: string; analysis_timestamp: string; snapshot_status: string;
  context_type: string; context_version: string;
  current_head?: string | null;
}
export interface EvidenceRecord { id: string; text: string; source_paths: string[]; section?: string }
export interface ContextCoverage {
  status: string; files_discovered: number; files_analyzed: number;
  files_omitted: number; critical_files_omitted: number; budget_omitted_blocks: number;
}
export interface WorkspaceInspection {
  available?: boolean; warnings?: string[];
  state?: 'READY' | 'NOT_ANALYZED' | 'STALE' | 'SNAPSHOT_INVALID' | 'EMPTY_REPOSITORY';
  project_types?: string[];
  identity: SnapshotIdentity; completeness: ContextCoverage; markdown: string;
  relevance: { editable_files: string[]; protected_files: string[]; cross_boundary_files: string[]; warnings: string[] };
  sections: { number: number; title: string; records: EvidenceRecord[] }[];
  omission_manifest: { category: string; source_paths: string[]; reason: string; record?: string }[];
  provider: { name: string; configured: boolean };
}
export interface ChatAnswer {
  conversation_id: string; revision: number; status: 'grounded' | 'unknown' | 'out_of_scope';
  answer: string; citations: EvidenceRecord[]; identity: SnapshotIdentity;
  actions: { kind: string; target_path: string; evidence_id: string; text: string }[];
  completeness: ContextCoverage; omission_manifest: WorkspaceInspection['omission_manifest'];
  artifact?: WorkspaceArtifact | null; comparison?: BranchComparison | null;
  confidence?: string; warnings?: string[]; intent?: string;
  retrieval?: { records_available: number; records_retrieved: number; records_omitted: number; input_bytes: number };
}
export type ArtifactType = 'context' | 'handoff' | 'prd' | 'technical_design' | 'tasks' | 'onboarding' | 'implementation_plan' | 'review' | 'prompt';
export interface WorkspaceArtifact {
  artifact_type: ArtifactType; filename: string; content: string; sha256: string;
  identity: SnapshotIdentity; completeness: ContextCoverage;
  omission_manifest: WorkspaceInspection['omission_manifest'];
  summary?: string;
}
export interface BranchComparison {
  before: SnapshotIdentity; after: SnapshotIdentity;
  completeness: { before: ContextCoverage; after: ContextCoverage };
  only_in_before_inventory: string[]; only_in_after_inventory: string[];
  changed_blob_paths: string[]; unknown_blob_paths: string[]; protected_changes: string[];
  contract_changes: { source_file: string; method: string; route: string; before: unknown; after: unknown }[];
  warnings: string[];
  findings?: Record<string, { record: string; before: EvidenceRecord | null; after: EvidenceRecord | null; before_branch: string; after_branch: string }[]>;
}
