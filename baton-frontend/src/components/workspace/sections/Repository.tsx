import { useState } from 'react';
import { GitBranch, File, ChevronRight, Loader2, Github } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import type { TreeItem, RepoValidation } from '@/types';
import { batonApi } from '@/lib/api/batonApi';
import { DEMO_BRANCHES, DEMO_TREE, DEMO_FILE_CONTENT } from '@/lib/demo';
import { Button, MonoLabel, Panel, TelemetryLine, SectionLabel } from '@/components/ui/primitives';
import { cn, shortSha } from '@/lib/utils';

type ValidateState = 'idle' | 'loading' | 'success' | 'error';

export function Repository({ state }: { state: WorkspaceStateHook }) {
  const [urlInput, setUrlInput] = useState(state.repoUrl || '');
  const [tokenInput, setTokenInput] = useState('');
  const [validateState, setValidateState] = useState<ValidateState>('idle');
  const [error, setError] = useState('');
  const [branches, setBranches] = useState(state.isDemoMode ? DEMO_BRANCHES : [] as typeof DEMO_BRANCHES);
  const [tree, setTree] = useState<TreeItem[]>(state.isDemoMode ? DEMO_TREE : []);
  const [selectedFile, setSelectedFile] = useState<{ path: string; content: string } | null>(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [treeLoading, setTreeLoading] = useState(false);

  const handleValidate = async () => {
    if (!urlInput.trim()) return;
    setValidateState('loading');
    setError('');

    if (state.isDemoMode || urlInput.includes('baton/demo-project')) {
      setTimeout(() => {
        const demoRepo: RepoValidation = {
          owner: 'baton',
          repository: 'demo-project',
          default_branch: 'main',
          visibility: 'public',
          accessible: true,
        };
        state.setRepoUrl(urlInput);
        state.setRepo(demoRepo);
        setValidateState('success');
        setBranches(DEMO_BRANCHES);
      }, 1200);
      return;
    }

    try {
      const result = await batonApi.validateRepository(urlInput, tokenInput || undefined);
      state.setRepoUrl(urlInput);
      state.setRepo(result);
      state.setGithubToken(tokenInput);
      setValidateState('success');
      const fetchedBranches = await batonApi.getBranches(result.owner, result.repository, tokenInput || undefined);
      setBranches(fetchedBranches);
    } catch (err) {
      setValidateState('error');
      setError(err instanceof Error ? err.message : 'Failed to validate repository');
    }
  };

  const handleBranchSelect = async (branchName: string) => {
    state.setSelectedBranch(branchName);
    setSelectedFile(null);
    setTreeLoading(true);
    if (state.isDemoMode) {
      setTimeout(() => {
        setTree(DEMO_TREE);
        setTreeLoading(false);
      }, 600);
      return;
    }
    try {
      if (state.repo) {
        const items = await batonApi.getTree(state.repo.owner, state.repo.repository, branchName, '', tokenInput || state.githubToken || undefined);
        setTree(items);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tree');
    } finally {
      setTreeLoading(false);
    }
  };

  const handleFileClick = async (path: string) => {
    if (state.isDemoMode) {
      setSelectedFile({ path, content: DEMO_FILE_CONTENT });
      return;
    }
    if (!state.repo || !state.selectedBranch) return;
    setFileLoading(true);
    try {
      const fileData = await batonApi.getFile(
        state.repo.owner,
        state.repo.repository,
        state.selectedBranch,
        path,
        tokenInput || state.githubToken || undefined
      );
      setSelectedFile({ path: fileData.path, content: fileData.content });
    } catch (err) {
      setSelectedFile({
        path,
        content: `// Error loading file: ${err instanceof Error ? err.message : 'Failed to fetch file content'}`,
      });
    } finally {
      setFileLoading(false);
    }
  };

  const toggleDir = (path: string) => {
    setExpandedDirs((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const buildTree = (items: TreeItem[]) => {
    const sorted = [...items].sort((a, b) => {
      if (a.type === 'tree' && b.type !== 'tree') return -1;
      if (a.type !== 'tree' && b.type === 'tree') return 1;
      return a.path.localeCompare(b.path);
    });
    return sorted;
  };

  const getDepth = (path: string) => path.split('/').length - 1;
  const isExpanded = (path: string) => expandedDirs.has(path) || path.endsWith('/');
  const visibleItems = buildTree(tree).filter((item) => {
    const parent = item.path.substring(0, item.path.lastIndexOf('/'));
    if (!parent) return true;
    return isExpanded(parent + '/') || expandedDirs.has(parent);
  });

  return (
    <div className="p-6 lg:p-8 max-w-6xl">
      <SectionLabel className="mb-6">REPOSITORY</SectionLabel>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Repository</h1>
      <p className="text-sm text-baton-text-tertiary mb-8">Connect and inspect the GitHub repository.</p>

      {/* Connect form */}
      {!state.repo && validateState !== 'success' && (
        <Panel label="CONNECT REPOSITORY" className="mb-6">
          <div className="p-6 space-y-4">
            <div>
              <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-2">
                Repository URL
              </label>
              <div className="flex items-center gap-2 border border-baton-border bg-baton-black rounded-baton px-3 py-2.5">
                <Github size={15} className="text-baton-text-tertiary flex-shrink-0" />
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://github.com/owner/repository"
                  className="flex-1 bg-transparent text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono"
                />
              </div>
            </div>
            <div>
              <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-2">
                GitHub Token (optional — for private repos or higher rate limits)
              </label>
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="ghp_..."
                className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2.5 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono"
              />
            </div>
            <div className="flex items-center gap-3">
              <Button variant="primary" onClick={handleValidate} disabled={validateState === 'loading' || !urlInput.trim()}>
                {validateState === 'loading' ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    VALIDATING...
                  </>
                ) : (
                  'VALIDATE REPOSITORY'
                )}
              </Button>
              {validateState === 'error' && (
                <span className="text-sm text-baton-warning">{error}</span>
              )}
            </div>
            {validateState === 'loading' && (
              <div className="pt-2">
                <TelemetryLine active />
              </div>
            )}
          </div>
        </Panel>
      )}

      {/* Repository metadata */}
      {state.repo && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-baton-border mb-6">
            {[
              { label: 'OWNER', value: state.repo.owner },
              { label: 'REPOSITORY', value: state.repo.repository },
              { label: 'DEFAULT BRANCH', value: state.repo.default_branch },
              { label: 'VISIBILITY', value: state.repo.visibility },
            ].map((item) => (
              <div key={item.label} className="bg-baton-near-black p-4">
                <MonoLabel>{item.label}</MonoLabel>
                <div className="font-mono text-sm text-baton-text-highlight mt-1">{item.value}</div>
              </div>
            ))}
          </div>

          {/* Branch selection */}
          <Panel label="BRANCHES" className="mb-6">
            <div className="p-4">
              <div className="space-y-1">
                {branches.map((branch) => (
                  <button
                    key={branch.name}
                    onClick={() => handleBranchSelect(branch.name)}
                    className={cn(
                      'w-full flex items-center justify-between px-3 py-2 rounded-baton transition-colors',
                      state.selectedBranch === branch.name
                        ? 'bg-baton-layer-1 text-baton-white'
                        : 'text-baton-text-secondary hover:text-baton-text-highlight hover:bg-baton-layer-1/50'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <GitBranch size={13} className={state.selectedBranch === branch.name ? 'text-baton-accent' : ''} />
                      <span className="font-mono text-[12px]">{branch.name}</span>
                    </div>
                    <span className="font-mono text-[10px] text-baton-text-tertiary">{shortSha(branch.sha)}</span>
                  </button>
                ))}
              </div>
            </div>
          </Panel>

          {/* File browser */}
          {state.selectedBranch && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Panel label="FILE TREE">
                <div className="p-3 max-h-[500px] overflow-y-auto">
                  {treeLoading ? (
                    <div className="flex items-center gap-2 px-3 py-4">
                      <Loader2 size={14} className="animate-spin text-baton-accent" />
                      <span className="font-mono text-[11px] text-baton-text-tertiary">Loading tree...</span>
                    </div>
                  ) : (
                    <div className="space-y-0.5">
                      {visibleItems.map((item) => {
                        const isTree = item.type === 'tree' || item.path.endsWith('/');
                        const depth = getDepth(item.path);
                        const name = item.path.split('/').pop() || item.path;
                        const expanded = expandedDirs.has(item.path);
                        return (
                          <button
                            key={item.path}
                            onClick={() => (isTree ? toggleDir(item.path) : handleFileClick(item.path))}
                            className={cn(
                              'w-full flex items-center gap-1.5 px-2 py-1 rounded-baton transition-colors text-left',
                              selectedFile?.path === item.path
                                ? 'bg-baton-layer-1 text-baton-white'
                                : 'text-baton-text-secondary hover:text-baton-text-highlight hover:bg-baton-layer-1/50'
                            )}
                            style={{ paddingLeft: `${depth * 12 + 8}px` }}
                          >
                            {isTree ? (
                              <ChevronRight size={12} className={cn('flex-shrink-0 transition-transform', expanded && 'rotate-90')} />
                            ) : (
                              <File size={12} className="flex-shrink-0 text-baton-text-tertiary" />
                            )}
                            <span className="font-mono text-[11px] truncate">{name}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </Panel>

              <Panel label="FILE PREVIEW">
                <div className="p-4 min-h-[200px]">
                  {fileLoading ? (
                    <div className="flex items-center gap-2 text-baton-text-tertiary py-8 justify-center">
                      <Loader2 size={16} className="animate-spin text-baton-accent" />
                      <span className="font-mono text-[11px]">Loading file content...</span>
                    </div>
                  ) : selectedFile ? (
                    <div>
                      <div className="font-mono text-[11px] text-baton-accent mb-3">{selectedFile.path}</div>
                      <pre className="font-mono text-[11px] text-baton-text-highlight leading-relaxed whitespace-pre-wrap">
                        {selectedFile.content}
                      </pre>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full text-baton-text-tertiary py-12">
                      <span className="font-mono text-[11px]">Select a file to preview</span>
                    </div>
                  )}
                </div>
              </Panel>
            </div>
          )}
        </>
      )}
    </div>
  );
}
