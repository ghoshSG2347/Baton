import { useState, useCallback, useEffect, useMemo } from 'react';
import type { TeamMember, WorkspaceSection, RepoValidation, WorkspaceRequest } from '@/types';
import { setBatonAccessKey as configureAccess } from '@/lib/api/batonApi';
import { redactUserData } from '@/lib/utils/redaction';

interface WorkspaceState {
  repoUrl: string;
  repo: RepoValidation | null;
  selectedBranch: string;
  selectedFolder: string;
  members: TeamMember[];
  isDemoMode: boolean;
  githubToken: string;
  batonAccessKey: string;
  activeSection: WorkspaceSection;
  firstRun: boolean;
  firstRunStep: number;
  resetVersion: number;
}

const STORAGE_KEY = 'baton-workspace-state';

function loadState(): Partial<WorkspaceState> | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return redactUserData(JSON.parse(raw), []) as Partial<WorkspaceState>;
  } catch {
    return null;
  }
}

function saveState(state: WorkspaceState) {
  try {
    const { githubToken, batonAccessKey, ...persistable } = state;
    void githubToken;
    void batonAccessKey;
    const remembered = { ...persistable, repo: persistable.repo ? {
      owner: persistable.repo.owner, repository: persistable.repo.repository,
      default_branch: persistable.repo.default_branch, visibility: persistable.repo.visibility,
      accessible: false, current_head: persistable.repo.current_head,
    } : null };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(redactUserData(remembered, [githubToken, batonAccessKey])));
  } catch {
    // ignore
  }
}

const initial = loadState();

export function useWorkspaceState() {
  const [repoUrl, setRepoUrl] = useState(initial?.repoUrl || '');
  const [repo, setRepo] = useState<RepoValidation | null>(initial?.repo || null);
  const [selectedBranch, setSelectedBranch] = useState(initial?.selectedBranch || '');
  const [selectedFolder, setSelectedFolder] = useState(initial?.selectedFolder || '');
  const [members, setMembers] = useState<TeamMember[]>(initial?.members || []);
  const [isDemoMode, setIsDemoMode] = useState(initial?.isDemoMode || false);
  const [githubToken, setGithubTokenState] = useState('');
  const [batonAccessKey, setAccessKeyState] = useState('');
  const setBatonAccessKey = useCallback((value: string) => { configureAccess(value); setAccessKeyState(value); }, []);
  const [activeSection, setActiveSection] = useState<WorkspaceSection>('ai');
  const [firstRun, setFirstRun] = useState(!initial?.repo);
  const [firstRunStep, setFirstRunStep] = useState(0);
  const [resetVersion, setResetVersion] = useState(0);
  const setGithubToken = useCallback((value: string) => {
    setGithubTokenState(value.trim());
    setFileReference(null);
  }, []);
  const [analysisRevision, setAnalysisRevision] = useState(0);
  const markAnalysisComplete = useCallback(() => setAnalysisRevision((revision) => revision + 1), []);
  const [fileReference, setFileReference] = useState<{ request: WorkspaceRequest; path: string } | null>(null);
  const openRepositoryFile = useCallback((request: WorkspaceRequest, path: string) => {
    setFileReference({ request, path }); setActiveSection('repository');
  }, []);
  useEffect(() => { setFileReference(null); }, [repo, selectedBranch]);

  const state = useMemo<WorkspaceState>(() => ({
    repoUrl,
    repo,
    selectedBranch,
    selectedFolder,
    members,
    isDemoMode,
    githubToken,
    batonAccessKey,
    activeSection,
    firstRun,
    firstRunStep,
    resetVersion,
  }), [repoUrl, repo, selectedBranch, selectedFolder, members, isDemoMode, githubToken, batonAccessKey, activeSection, firstRun, firstRunStep, resetVersion]);


  useEffect(() => {
    saveState(state);
  }, [state]);

  const addMember = useCallback((member: TeamMember) => {
    setMembers((prev) => [...prev, member]);
  }, []);

  const removeMember = useCallback((id: string) => {
    setMembers((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const reset = useCallback(() => {
    setRepoUrl('');
    setRepo(null);
    setSelectedBranch('');
    setSelectedFolder('');
    setMembers([]);
    setIsDemoMode(false);
    setGithubToken('');
    setBatonAccessKey('');
    setFirstRun(true);
    setFirstRunStep(0);
    setResetVersion((version) => version + 1);
    localStorage.removeItem(STORAGE_KEY);
  }, [setBatonAccessKey, setGithubToken]);

  // Clears all repository-specific state and persisted localStorage while
  // preserving the in-memory GitHub token so the user can immediately
  // connect a new repository without re-entering their token.
  const changeRepository = useCallback(() => {
    setRepoUrl('');
    setRepo(null);
    setSelectedBranch('');
    setSelectedFolder('');
    setMembers([]);
    setIsDemoMode(false);
    setFirstRun(true);
    setFirstRunStep(0);
    setResetVersion((version) => version + 1);
    setActiveSection('repository');
    localStorage.removeItem(STORAGE_KEY);
    // githubToken intentionally not cleared — survives repository switching
  }, []);

  return {
    ...state,
    setRepoUrl,
    setRepo,
    setSelectedBranch,
    setSelectedFolder,
    setMembers,
    addMember,
    removeMember,
    setIsDemoMode,
    setGithubToken,
    setBatonAccessKey,
    setActiveSection,
    setFirstRun,
    setFirstRunStep,
    reset,
    changeRepository,
    resetVersion,
    fileReference, openRepositoryFile,
    analysisRevision, markAnalysisComplete,
  };
}

export type WorkspaceStateHook = ReturnType<typeof useWorkspaceState>;
