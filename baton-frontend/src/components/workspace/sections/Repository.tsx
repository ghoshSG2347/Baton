import { ErrorStatus } from '@/components/ui/StatusPanel';
import { useState, useEffect, useRef } from 'react';
import { GitBranch, File, ChevronRight, Loader2, Github, LogOut } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import type { TreeItem, RepoValidation } from '@/types';
import { batonApi, type GitHubAccess } from '@/lib/api/batonApi';
import { DEMO_BRANCHES, DEMO_TREE, DEMO_FILE_CONTENT } from '@/lib/demo';
import { Button, MonoLabel, Panel, TelemetryLine, SectionLabel } from '@/components/ui/primitives';
import { cn, shortSha } from '@/lib/utils';
import { useRetryBackoff } from '@/hooks/useRetryBackoff';

type ValidateState = 'idle' | 'loading' | 'success' | 'error';

export function Repository({ state }: { state: WorkspaceStateHook }) {
  const [urlInput, setUrlInput] = useState(state.repoUrl || '');
  const [tokenInput, setTokenInput] = useState('');
  const [geminiInput, setGeminiInput] = useState('');
  const [modelInput, setModelInput] = useState(state.geminiModel);
  const [aiBusy, setAiBusy] = useState(false);
  const [checks, setChecks] = useState<string[]>([]);
  const validationLock = useRef(false);
  const aiEpoch = useRef(0);
  const aiLock = useRef(false);
  useEffect(() => () => { aiEpoch.current++; }, []);
  const [access, setAccess] = useState<GitHubAccess | null>(null);
  const [accessBusy, setAccessBusy] = useState(false);
  const [validateState, setValidateState] = useState<ValidateState>('idle');
  const [error, setError] = useState<Error | null>(null);
  const retryBlocked = useRetryBackoff(error);
  const lastAccessToken = useRef('');
  const sameAccess = lastAccessToken.current === (tokenInput.trim() || state.githubToken);
  const [branches, setBranches] = useState(state.isDemoMode ? DEMO_BRANCHES : [] as typeof DEMO_BRANCHES);
  const [tree, setTree] = useState<TreeItem[]>(state.isDemoMode ? DEMO_TREE : []);
  const [selectedFile, setSelectedFile] = useState<{ path: string; content: string } | null>(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [treeLoading, setTreeLoading] = useState(false);
  const [sourceLabel, setSourceLabel] = useState('');
  const validationEpoch = useRef(0);
  const fileEpoch = useRef(0);
  const scopeRef = useRef('');
  scopeRef.current = `${state.repo?.owner}/${state.repo?.repository}:${state.selectedBranch}`;
  useEffect(() => () => { validationEpoch.current++; fileEpoch.current++; }, []);
  useEffect(() => {
    if (!state.repo || state.isDemoMode) return;
    if (!state.githubToken) { setBranches([]); setTree([]); setSelectedFile(null); return; }
    let active = true;
    setBranches([]);
    batonApi.getBranches(state.repo.owner, state.repo.repository, state.githubToken || undefined)
      .then((items) => { if (active) setBranches(items); })
      .catch((err) => { if (active) setError(err instanceof Error ? err : new Error('Branches could not be loaded.')); });
    return () => { active = false; };
  }, [state.repo, state.githubToken, state.isDemoMode]);
  useEffect(() => {
    setSelectedFile(null); setExpandedDirs(new Set()); fileEpoch.current++;
    if (!state.repo || !state.selectedBranch || (!state.isDemoMode && !state.githubToken)) { setTree([]); return; }
    if (state.isDemoMode) { setTree(DEMO_TREE); return; }
    let active = true; setTree([]); setTreeLoading(true); setError(null);
    batonApi.getTree(state.repo.owner, state.repo.repository, state.selectedBranch, '', state.githubToken || undefined)
      .then((items) => { if (active) setTree(items); })
      .catch((err) => { if (active) setError(err instanceof Error ? err : new Error('Branch files could not be loaded.')); })
      .finally(() => { if (active) setTreeLoading(false); });
    return () => { active = false; };
  }, [state.repo, state.selectedBranch, state.githubToken, state.isDemoMode]);
  useEffect(() => {
    const reference = state.fileReference;
    if (!reference || !state.githubToken) return;
    let active = true;
    setSelectedFile(null); setFileLoading(true); setError(null);
    batonApi.source({ ...reference.request, path: reference.path }, state.githubToken || undefined)
      .then((result) => { if (active) { setSelectedFile(result); setSourceLabel(`Commit ${shortSha(result.identity.commit)} · lines ${result.start_line}–${result.end_line}${result.partial ? ' · partial source region' : ''}`); } })
      .catch((err) => { if (active) setError(err instanceof Error ? err : new Error('Source could not be loaded.')); })
      .finally(() => { if (active) setFileLoading(false); });
    return () => { active = false; };
  }, [state.fileReference, state.githubToken]);

  const handleValidate = async () => {
    if (!urlInput.trim() || (!state.isDemoMode && !(tokenInput.trim() || state.githubToken)) || validateState === 'loading' || validationLock.current || (retryBlocked && sameAccess)) return;
    validationLock.current = true;
    const current = ++validationEpoch.current;
    setChecks([]);
    const effectiveToken = tokenInput.trim() || state.githubToken;
    lastAccessToken.current = effectiveToken;
    setValidateState('loading');
    setError(null);

    if (state.isDemoMode || urlInput.includes('baton/demo-project')) {
      setTimeout(() => {
        if (current !== validationEpoch.current) return;
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
        setBranches(DEMO_BRANCHES); validationLock.current = false;
      }, 1200);
      return;
    }

    try {
      const result = await batonApi.validateRepository(urlInput, effectiveToken || undefined);
      if (current !== validationEpoch.current) return;
      setChecks(['Repository URL valid', 'GitHub token accepted', 'Repository access verified', 'Required read endpoints available']);
      if (geminiInput.trim()) {
        await batonApi.validateGemini(geminiInput.trim(), modelInput.trim());
        if (current !== validationEpoch.current) return;
        state.setGeminiCredential(geminiInput.trim(), modelInput.trim(), true); setGeminiInput('');
        setChecks(previous => [...previous, 'Gemini key accepted', 'Gemini model reports generation support']);
      }
      state.setRepoUrl(urlInput);
      state.setRepo(result);
      state.setGithubToken(effectiveToken);
      setTokenInput('');
      state.setSelectedBranch(result.default_branch || '');
      state.setSelectedFolder('');
      setValidateState('success');

    } catch (err) {
      if (current !== validationEpoch.current) return;
      setValidateState('error');
      setError(err instanceof Error ? err : new Error('Failed to validate repository'));
    } finally { validationLock.current = false; }
  };

  const handleBranchSelect = (branchName: string) => {
    state.setSelectedBranch(branchName);
    if (state.repo) state.setRepo({ ...state.repo, current_head: branches.find(branch => branch.name === branchName)?.sha || null });
  };

  const checkAccess = async () => {
    if (accessBusy || (retryBlocked && sameAccess)) return;
    setAccessBusy(true); setAccess(null); setError(null);
    const token = tokenInput.trim() || state.githubToken;
    lastAccessToken.current = token;
    const current = ++validationEpoch.current;
    try {
      if (!state.repo) return;
      const result = await batonApi.validateRepository(state.repoUrl, token || undefined);
      if (current !== validationEpoch.current) return;
      if (result.owner !== state.repo.owner || result.repository !== state.repo.repository) return;
      state.setRepo(result);
      state.setGithubToken(token); setTokenInput(''); setAccess({ authenticated: result.authenticated === true, token_present: true, upstream_status: 200, token_source: 'request', rate_limit: result.rate_limit || {} });
    } catch (err) {
      if (current !== validationEpoch.current) return;
      state.setGithubToken('');
      setError(err instanceof Error ? err : new Error('GitHub access could not be checked.'));
    } finally { setAccessBusy(false); }
  };

  const handleFileClick = async (path: string) => {
    setSourceLabel('Current branch source');
    if (state.isDemoMode) {
      setSelectedFile({ path, content: DEMO_FILE_CONTENT });
      return;
    }
    if (!state.repo || !state.selectedBranch) return;
    const current = ++fileEpoch.current;
    const selectedScope = scopeRef.current;
    setFileLoading(true); setSelectedFile(null); setError(null);
    try {
      const fileData = await batonApi.getFile(
        state.repo.owner,
        state.repo.repository,
        state.selectedBranch,
        path,
        state.githubToken || undefined
      );
      if (current === fileEpoch.current && selectedScope === scopeRef.current) setSelectedFile({ path: fileData.path, content: fileData.content });
    } catch (err) {
      if (current === fileEpoch.current && selectedScope === scopeRef.current) setError(err instanceof Error ? err : new Error('File could not be loaded.'));
    } finally {
      if (current === fileEpoch.current && selectedScope === scopeRef.current) setFileLoading(false);
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

  const validateAI = async () => {
    if (aiBusy || aiLock.current || retryBlocked || !geminiInput.trim() || !modelInput.trim()) return;
    aiLock.current = true;
    const current = ++aiEpoch.current;
    setAiBusy(true); setError(null);
    // Replacing a credential immediately disables the old AI scope.
    state.setGeminiCredential('', modelInput.trim());
    try {
      await batonApi.validateGemini(geminiInput.trim(), modelInput.trim());
      if (current !== aiEpoch.current) return;
      state.setGeminiCredential(geminiInput.trim(), modelInput.trim(), true); setGeminiInput('');
      setChecks(previous => [...previous.filter(check => !check.startsWith('Gemini')), 'Gemini key accepted', 'Gemini model reports generation support']);
    } catch (err) { if (current === aiEpoch.current) setError(err instanceof Error ? err : new Error('Gemini validation failed')); }
    finally { aiLock.current = false; if (current === aiEpoch.current) setAiBusy(false); }
  };
  const aiFields = <div className="space-y-3" aria-label="Gemini credentials">
    <label className="block text-xs text-baton-text-secondary">Gemini API key
      <input aria-label="Gemini API key" type="password" autoComplete="off" maxLength={512} value={geminiInput} onChange={event => setGeminiInput(event.target.value)} placeholder={state.geminiReady ? 'Validated key held in this tab' : 'Enter your own Gemini key'} className="mt-2 w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2.5 text-sm text-baton-white" />
    </label>
    <label className="block text-xs text-baton-text-secondary">Gemini model
      <input aria-label="Gemini model" maxLength={100} value={modelInput} onChange={event => setModelInput(event.target.value)} placeholder="Model identifier available to your key" className="mt-2 w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2.5 text-sm text-baton-white" />
    </label>
    <p className="text-xs text-baton-text-tertiary">Keys stay in this tab's memory and are used by Baton’s backend. Reload requires re-entry. Model validation checks provider metadata; generation and quota are confirmed when you ask. Repository context and exports remain available without AI.</p>
    <a className="text-xs text-baton-accent underline" href="https://aistudio.google.com/api-keys" target="_blank" rel="noreferrer">Get a Gemini API key</a>
    {state.repo && <div className="flex flex-wrap gap-2"><Button onClick={validateAI} disabled={aiBusy || retryBlocked || !geminiInput.trim() || !modelInput.trim()}>{aiBusy ? 'Validating Gemini…' : 'Validate Gemini'}</Button><Button variant="ghost" onClick={() => { aiEpoch.current++; setAiBusy(false); state.setGeminiCredential('', modelInput.trim()); setGeminiInput(''); setChecks(previous => previous.filter(check => !check.startsWith('Gemini'))); }}>Clear Gemini key</Button></div>}
    <p role="status" className="text-xs text-baton-text-secondary">{aiBusy ? 'AI validating' : state.geminiReady ? `AI ready · ${state.geminiModel}` : 'AI key required or not validated'}</p>
  </div>;

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
      {error && <div className="mb-4"><ErrorStatus error={error} operation="connection" primaryAction={!state.repo && <Button onClick={handleValidate} disabled={validateState === 'loading'}>Retry connection</Button>} /></div>}

      {checks.length > 0 && <ul aria-label="Connection checks" className="mb-5 text-xs text-baton-text-secondary space-y-2">{checks.map(check => <li key={check}>✓ {check}</li>)}</ul>}
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
                  type="url"
                  aria-label="GitHub repository URL"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://github.com/owner/repository"
                  className="flex-1 bg-transparent text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono"
                />
              </div>
            </div>
            <div>
              <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-2">
                Fine-grained GitHub token (required)
              </label>
              <input
                type="password"
                autoComplete="off"
                aria-label="Fine-grained GitHub token"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="github_pat_..."
                className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2.5 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono"
              />
            </div>
            <p className="text-xs text-baton-text-secondary">Baton uses your token for authenticated repository access and higher API limits. Required permissions: Metadata — Read; Contents — Read. Select the repository you want Baton to analyze. Organization approval may also be required.</p>
            <a className="text-xs text-baton-accent underline" href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens" target="_blank" rel="noreferrer">How to create a Fine-grained token</a>
            {aiFields}
            <div className="flex items-center gap-3">
              <Button variant="primary" onClick={handleValidate} disabled={validateState === 'loading' || !urlInput.trim() || (!state.isDemoMode && !(tokenInput.trim() || state.githubToken)) || (retryBlocked && sameAccess)}>
                {validateState === 'loading' ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    VALIDATING...
                  </>
                ) : (
                  geminiInput.trim() ? 'VALIDATE & CONNECT' : 'CONNECT REPOSITORY'
                )}
              </Button>
            </div>
            {validateState === 'loading' && (
              <div className="pt-2">
                <TelemetryLine active />
              </div>
            )}
          </div>
        </Panel>
      )}

      {/* Repository connected — metadata + change action */}
      {state.repo && (
        <>
          <Panel label="GITHUB ACCESS" className="mb-6">
            <div className="p-4 space-y-3">
              <p className="text-xs text-baton-text-tertiary">Your Fine-grained GitHub token is required and kept only in memory. Re-enter it after reloading. Replacing it validates access to this repository again.</p>
              <input aria-label="GitHub token for connected repository" type="password" autoComplete="off" value={tokenInput} onChange={(event) => setTokenInput(event.target.value)} placeholder={state.githubToken ? 'Token present in this tab' : 'GitHub token required'} className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2.5 text-sm text-baton-white outline-none font-mono" />
              <Button variant="secondary" onClick={checkAccess} disabled={accessBusy || !(tokenInput.trim() || state.githubToken) || (retryBlocked && sameAccess)}>{accessBusy ? 'Checking access…' : 'Validate repository access'}</Button>
              <Button variant="ghost" onClick={() => { state.setGithubToken(''); setTokenInput(''); setAccess(null); setError(null); }}>Clear GitHub token</Button>
              <p className="text-xs text-baton-text-secondary">Baton uses your token for authenticated repository access and higher API limits. Required permissions: Metadata — Read; Contents — Read. Select the repository you want Baton to analyze. Organization approval may also be required.</p>
            <a className="text-xs text-baton-accent underline" href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens" target="_blank" rel="noreferrer">How to create a Fine-grained token</a>
              {access && <p role="status" className="text-xs text-baton-text-secondary">{access.authenticated ? 'GitHub accepted the token.' : 'GitHub token required.'} Token source: {access.token_source}. Requests remaining: {access.rate_limit.remaining ?? 'unavailable'} / {access.rate_limit.limit ?? 'unavailable'}.{access.rate_limit.reset_at ? ` Reset: ${new Date(access.rate_limit.reset_at * 1000).toLocaleString()}.` : ''}</p>}
            </div>
          </Panel>
          <Panel label="GEMINI ACCESS" className="mb-6"><div className="p-4">{aiFields}</div></Panel>
          <p className="text-xs text-baton-text-secondary mb-4">{state.repo.current_head ? `${state.githubToken ? 'Current commit' : 'Last observed commit'}: ${state.repo.current_head}` : 'Commit unavailable'}</p>
          {!state.githubToken && !state.isDemoMode && <p role="status" className="mb-4 text-sm text-baton-warning">GitHub token required. Re-enter your token to restore access to this remembered repository.</p>}
          {/* Change repository action */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <span className="font-mono text-[11px] text-baton-text-tertiary">{state.githubToken || state.isDemoMode ? 'CONNECTED TO' : 'TOKEN REQUIRED FOR'}</span>
              <span className="font-mono text-[11px] text-baton-text-highlight ml-2">{state.repo.owner}/{state.repo.repository}</span>
            </div>
            <button
              type="button"
              id="repository-change-repository-btn"
              onClick={() => state.changeRepository()}
              aria-label="Exit current repository and connect a new one"
              className="inline-flex items-center gap-1.5 font-mono text-[10px] tracking-wider text-baton-text-tertiary hover:text-baton-warning border border-baton-border hover:border-baton-warning/50 rounded-baton px-3 py-1.5 transition-all duration-150 uppercase"
            >
              <LogOut size={11} />
              ← Change Repository
            </button>
          </div>

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
                      <p className="font-mono text-[10px] text-baton-text-tertiary mb-3">{sourceLabel}</p>
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
