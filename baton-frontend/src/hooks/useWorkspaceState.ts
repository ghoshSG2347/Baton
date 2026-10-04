import { useState, useCallback, useEffect, useMemo } from 'react';
import type { TeamMember, WorkspaceSection, RepoValidation } from '@/types';

interface WorkspaceState {
  repoUrl: string;
  repo: RepoValidation | null;
  selectedBranch: string;
  selectedFolder: string;
  members: TeamMember[];
  isDemoMode: boolean;
  githubToken: string;
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
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveState(state: WorkspaceState) {
  try {
    const { githubToken, ...persistable } = state;
    void githubToken;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(persistable));
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
  const [githubToken, setGithubToken] = useState('');
  const [activeSection, setActiveSection] = useState<WorkspaceSection>('overview');
  const [firstRun, setFirstRun] = useState(!initial?.repo);
  const [firstRunStep, setFirstRunStep] = useState(0);
  const [resetVersion, setResetVersion] = useState(0);

  const state = useMemo<WorkspaceState>(() => ({
    repoUrl,
    repo,
    selectedBranch,
    selectedFolder,
    members,
    isDemoMode,
    githubToken,
    activeSection,
    firstRun,
    firstRunStep,
    resetVersion,
  }), [repoUrl, repo, selectedBranch, selectedFolder, members, isDemoMode, githubToken, activeSection, firstRun, firstRunStep, resetVersion]);

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
    setFirstRun(true);
    setFirstRunStep(0);
    setResetVersion((version) => version + 1);
    localStorage.removeItem(STORAGE_KEY);
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
    setActiveSection,
    setFirstRun,
    setFirstRunStep,
    reset,
    resetVersion,
  };
}

export type WorkspaceStateHook = ReturnType<typeof useWorkspaceState>;
