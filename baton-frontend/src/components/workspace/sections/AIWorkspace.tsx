import { useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArrowUp, GitBranch, FileText, Plus, Download, PanelRightClose, PanelRightOpen, RefreshCw, Square, ChevronDown, Check, Files, ArrowLeftRight } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import type { ArtifactType, Branch, BranchComparison, ChatAnswer, WorkspaceArtifact, WorkspaceInspection, WorkspaceRequest } from '@/types';
import { BatonApiError, batonApi } from '@/lib/api/batonApi';
import { CopyButton, Button, SectionLabel, Panel } from '@/components/ui/primitives';
import { shortSha } from '@/lib/utils';
import { redactUserText } from '@/lib/utils/redaction';
import { ErrorStatus, StatusPanel } from '@/components/ui/StatusPanel';
import { analysisAction, repositoryMessage, requestFailure, snapshotState } from '@/lib/workspaceStatus';
import './AIWorkspace.css';
import { beginConversation } from '@/lib/usage';
import { useRetryBackoff } from '@/hooks/useRetryBackoff';
type Turn = { id: number; question: string; result: ChatAnswer };
const artifactNames: Record<ArtifactType, string> = {
  context: 'Repository context', handoff: 'Developer handoff', prd: 'PRD evidence draft',
  implementation_plan: 'Implementation plan', review: 'Review briefing', prompt: 'Coding prompt',
  technical_design: 'Technical design', tasks: 'Task breakdown', onboarding: 'Developer onboarding',
};
const suggestions = ['Explain the architecture and component connections', 'What is documented versus actually detected?', 'Which contracts do my changes need to preserve?', 'What remains unknown or needs investigation?'];
function Markdown({ text }: { text: string }) {
  return <div className="ai-markdown"><ReactMarkdown skipHtml components={{ a: ({ children }) => <span>{children}</span>, img: () => null }}>{text}</ReactMarkdown></div>;
}
function download(content: string, filename: string) {
  const url = URL.createObjectURL(new Blob([content], { type: 'text/markdown;charset=utf-8' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename;
  anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function AIWorkspace({ state }: { state: WorkspaceStateHook }) {
  const [memberId, setMemberId] = useState('');
  const [protectedScopes, setProtectedScopes] = useState('');
  const [task, setTask] = useState('');
  const [constraints, setConstraints] = useState('');
  const [message, setMessage] = useState('');
  const [scopeDraft, setScopeDraft] = useState({ memberId: '', protectedScopes: '', task: '', constraints: '' });
  const [branchNotice, setBranchNotice] = useState('');
  const previousBranch = useRef(state.selectedBranch || state.repo?.default_branch || '');
  const [promptTarget, setPromptTarget] = useState('Codex');
  const [inspection, setInspection] = useState<WorkspaceInspection | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [conversationRevision, setConversationRevision] = useState(0);
  const chatLock = useRef<AbortController | null>(null);
  const [stopNotice, setStopNotice] = useState('');
  const [pendingQuestion, setPendingQuestion] = useState('');
  const [busy, setBusy] = useState<'inspect' | 'refresh' | 'chat' | 'artifact' | 'compare' | null>(null);
  const [error, setError] = useState<{ cause: unknown; operation: string } | null>(null);
  const [branchError, setBranchError] = useState<unknown>(null);
  const retryBlocked = useRetryBackoff(error?.cause);
  const [inspectionScope, setInspectionScope] = useState('');
  const [knownHead, setKnownHead] = useState({ key: '', sha: '' });
  const [panelOpen, setPanelOpen] = useState(true);
  const [scopeOpen, setScopeOpen] = useState(false);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [compareBranch, setCompareBranch] = useState('');
  const [comparison, setComparison] = useState<BranchComparison | null>(null);
  const [artifacts, setArtifacts] = useState<WorkspaceArtifact[]>([]);
  const [activeArtifact, setActiveArtifact] = useState<WorkspaceArtifact | null>(null);
  const [artifactType, setArtifactType] = useState<ArtifactType>('context');
  const epoch = useRef(0);
  const analysisLock = useRef('');
  const controller = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement | null>(null);
  const preview = useRef<HTMLDivElement | null>(null);
  const composer = useRef<HTMLTextAreaElement | null>(null);
  const [focusComposer, setFocusComposer] = useState(false);
  useEffect(() => {
    if (focusComposer && !busy) { composer.current?.focus(); setFocusComposer(false); }
  }, [focusComposer, busy]);
  const member = state.members.find((item) => item.id === memberId);
  const request = useMemo<WorkspaceRequest>(() => ({
    owner: state.repo?.owner || '', repo: state.repo?.repository || '',
    branch: state.selectedBranch || state.repo?.default_branch || '', folder: state.selectedFolder,
    continue_snapshot: false,
    context_type: task.trim() ? 'task' : member ? 'role' : 'project',
    member: member ? { name: member.name, role: member.role, responsibilities: member.job ? [member.job] : [],
      ownership: member.folders, do_not_touch: [...(member.do_not_touch || []), ...protectedScopes.split('\n').map((s) => s.trim()).filter(Boolean)], team_scope: member.team_scope || [] }
      : { responsibilities: [], ownership: [], do_not_touch: protectedScopes.split('\n').map((s) => s.trim()).filter(Boolean), team_scope: [] },
    task: task.trim() || undefined, constraints: constraints.split('\n').map((s) => s.trim()).filter(Boolean),
  }), [state.repo, state.selectedBranch, state.selectedFolder, member, protectedScopes, task, constraints]);
  const scopeKey = JSON.stringify(request);
  const canOperate = !!state.repo && !state.isDemoMode;
  const identityKey = `${request.owner.toLowerCase()}/${request.repo.toLowerCase()}:${request.branch}:${request.folder}`;
  const inspectionMatches = inspectionScope === scopeKey;
  const lifecycle = !canOperate ? 'DISCONNECTED' : busy === 'refresh' ? 'ANALYZING'
    : error && ['inspect', 'analysis'].includes(error.operation) ? requestFailure(error.cause, error.operation).state
    : !inspectionMatches || busy === 'inspect' ? 'CONNECTING'
    : inspection ? snapshotState(inspection, request) : 'CONNECTED';
  const ready = lifecycle === 'READY';
  const chatReady = ready && !!inspection?.provider.configured;
  const currentHead = inspectionMatches ? inspection?.identity.current_head || (knownHead.key === identityKey ? knownHead.sha : '') : knownHead.key === identityKey ? knownHead.sha : '';
  const statusMessage = error && ['inspect', 'analysis'].includes(error.operation) ? requestFailure(error.cause, error.operation) : repositoryMessage(lifecycle);
  const actionLabel = analysisAction(lifecycle);
  const headerLabel = ready ? 'Repository grounded' : lifecycle === 'ANALYZING' ? 'Analyzing repository' : lifecycle === 'STALE' ? 'Repository snapshot stale' : lifecycle === 'ANALYSIS_FAILED' ? 'Analysis failed' : canOperate ? 'Repository connected' : 'No repository connected';
  const acceptInspection = (result: WorkspaceInspection) => {
    setInspection(result); setInspectionScope(scopeKey);
    if (result.identity.current_head) setKnownHead({ key: identityKey, sha: result.identity.current_head });
  };
  const openFile = (path: string, commit = inspection?.identity.commit) => { if (commit) state.openRepositoryFile({ ...request, commit }, path); };
  useEffect(() => { if (previousBranch.current !== request.branch) { setBranchNotice(`Context switched from ${previousBranch.current} → ${request.branch}`); previousBranch.current = request.branch; } }, [request.branch]);
  useEffect(() => {
    const current = ++epoch.current;
    beginConversation(); setStopNotice('');
    controller.current?.abort(); setTurns([]); setConversationId(undefined); setConversationRevision(0); setPendingQuestion('');
    setInspection(null); setArtifacts([]); setActiveArtifact(null); setComparison(null); setError(null);
    if (!canOperate) { setBusy(null); return; }
    setBusy('inspect');
    batonApi.inspectWorkspace(request, state.githubToken || undefined)
      .then((result) => { if (current === epoch.current) acceptInspection(result); })
      .catch((err) => { if (current === epoch.current) setError({ cause: err, operation: 'inspect' }); })
      .finally(() => { if (current === epoch.current) setBusy(null); });
    return () => { if (epoch.current === current) epoch.current = current + 1; controller.current?.abort(); };
    // Scope values are serialized to avoid treating equivalent object instances as changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scopeKey, canOperate, state.githubToken, state.batonAccessKey, state.analysisRevision]);
  useEffect(() => {
    if (!canOperate || !state.repo || knownHead.key !== identityKey || !knownHead.sha) return;
    let active = true; setBranches([]); setBranchError(null);
    batonApi.getBranches(state.repo.owner, state.repo.repository, state.githubToken || undefined)
      .then((items) => { if (active) setBranches(items); }).catch((err) => { if (active) { setBranches([]); setBranchError(err); } });
    return () => { active = false; };
  }, [canOperate, state.repo, state.githubToken, knownHead.key, knownHead.sha, identityKey]);
  useEffect(() => {
    if (state.activeSection !== 'ai' || !canOperate || busy || !inspectionMatches || !inspection) return;
    const current = epoch.current;
    batonApi.inspectWorkspace(request, state.githubToken || undefined).then((result) => {
      if (current !== epoch.current) return;
      acceptInspection(result);
      if (snapshotState(result, request) !== 'READY' || result.identity.commit !== inspection.identity.commit) {
        setTurns([]); setConversationId(undefined); setConversationRevision(0); setArtifacts([]); setActiveArtifact(null); setComparison(null);
      }
    }).catch((cause) => { if (current === epoch.current) { setInspection(null); setError({ cause, operation: 'inspect' }); } });
    // Returning to the workspace revalidates HEAD without discarding a current conversation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.activeSection]);
  useEffect(() => { if (turns.length || pendingQuestion) bottom.current?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'nearest' }); }, [turns, pendingQuestion]);
  useEffect(() => {
    if (!activeArtifact) return;
    const previousFocus = document.activeElement as HTMLElement | null;
    const node = preview.current;
    const focusable = () => Array.from(node?.querySelectorAll<HTMLElement>('button:not(:disabled), [href], input, select, textarea, [tabindex="0"]') || []);
    focusable()[0]?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { setActiveArtifact(null); return; }
      if (event.key !== 'Tab') return;
      const items = focusable(); const first = items[0]; const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener('keydown', handleKey);
    return () => { document.removeEventListener('keydown', handleKey); previousFocus?.focus(); };
  }, [activeArtifact]);
  const refresh = async () => {
    if (!canOperate || busy || retryBlocked || analysisLock.current === scopeKey) return;
    analysisLock.current = scopeKey;
    const current = ++epoch.current; controller.current?.abort();
    setBusy('refresh'); setError(null); setInspection(null); setTurns([]); setConversationId(undefined); setConversationRevision(0);
    setArtifacts([]); setActiveArtifact(null); setComparison(null);
    try {
      const forceRefresh = ['READY', 'STALE', 'SNAPSHOT_INVALID'].includes(lifecycle);
      if (request.folder) await batonApi.analyzeFolder(request.owner, request.repo, request.branch, request.folder, state.githubToken || undefined, forceRefresh);
      else await batonApi.analyzeRepository(request.owner, request.repo, request.branch, state.githubToken || undefined, forceRefresh);
      if (current !== epoch.current) return;
      const result = await batonApi.inspectWorkspace({ ...request, commit: undefined, continue_snapshot: false }, state.githubToken || undefined);
      if (current === epoch.current) { acceptInspection(result); }
    } catch (err) { if (current === epoch.current) setError({ cause: err, operation: 'analysis' }); }
    finally { if (analysisLock.current === scopeKey) analysisLock.current = ''; if (current === epoch.current) setBusy(null); }
  };
  const ask = async (question = message) => {
    if (!chatReady || !inspection || busy || retryBlocked || chatLock.current || !question.trim()) return;
    const safeQuestion = redactUserText(question.trim(), [state.githubToken, state.batonAccessKey]);
    if (safeQuestion === '[REDACTED]') { setError({ cause: new Error('Enter a repository question without credentials.'), operation: 'chat' }); return; }
    const current = epoch.current;
    const abort = new AbortController(); controller.current = abort; chatLock.current = abort; setStopNotice('');
    setBusy('chat'); setPendingQuestion(safeQuestion); setMessage(''); setError(null);
    try {
      const result = await batonApi.chat({ ...request, commit: inspection.identity.commit, message: safeQuestion, conversation_id: conversationId, revision: conversationId ? conversationRevision : undefined }, state.githubToken || undefined, abort.signal);
      if (current !== epoch.current || abort.signal.aborted) return;
      setTurns((previous) => [...previous, { id: result.revision, question: safeQuestion, result }]);
      setConversationId(result.conversation_id); setConversationRevision(result.revision);
      if (result.artifact) { const artifact = result.artifact; setArtifacts((previous) => [...previous.filter((a) => a.artifact_type !== artifact.artifact_type), artifact]); setPanelOpen(true); }
      if (result.comparison) { setComparison(result.comparison); setPanelOpen(true); }
    } catch (err) {
      if (current === epoch.current && !abort.signal.aborted) {
        setError({ cause: err, operation: 'chat' }); setMessage(safeQuestion);
        if (err instanceof BatonApiError && ['conversation_expired', 'conversation_limit', 'conversation_changed'].includes(err.code)) {
          setConversationId(undefined); setConversationRevision(0); setTurns([]);
        } else if (err instanceof BatonApiError && (err.code.startsWith('snapshot_') || (err.status === 409 && err.code === 'baton_backend_failure'))) {
          setInspection(null);
          try {
            const result = await batonApi.inspectWorkspace({ ...request, commit: undefined, continue_snapshot: false }, state.githubToken || undefined);
            if (current === epoch.current) { acceptInspection(result); setError(null); }
          } catch (inspectError) { if (current === epoch.current) setError({ cause: inspectError, operation: 'inspect' }); }
        }
      }
    }
    finally { if (chatLock.current === abort) chatLock.current = null; if (current === epoch.current) { setBusy(null); setPendingQuestion(''); } }
  };
  const generateArtifact = async () => {
    if (!ready || !inspection || busy) return;
    const current = epoch.current; setBusy('artifact'); setError(null); setPanelOpen(true);
    try {
      const result = await batonApi.artifact({ ...request, commit: inspection.identity.commit, artifact_type: artifactType, target: promptTarget }, state.githubToken || undefined);
      if (current !== epoch.current) return;
      setArtifacts((previous) => [...previous.filter((a) => a.artifact_type !== result.artifact_type), result]); setActiveArtifact(result);
    } catch (err) { if (current === epoch.current) setError({ cause: err, operation: 'artifact' }); }
    finally { if (current === epoch.current) setBusy(null); }
  };
  const compare = async () => {
    if (!ready || !inspection || busy || !compareBranch) return;
    const current = epoch.current; setBusy('compare'); setError(null);
    try {
      const result = await batonApi.compareBranches({ ...request, commit: inspection.identity.commit, compare_branch: compareBranch }, state.githubToken || undefined);
      if (current === epoch.current) { setComparison(result); setPanelOpen(true); }
    } catch (err) { if (current === epoch.current) setError({ cause: err, operation: 'compare' }); }
    finally { if (current === epoch.current) setBusy(null); }
  };
  const newChat = () => {
    controller.current?.abort(); chatLock.current = null; beginConversation(); setStopNotice('');
    epoch.current++; setMessage(''); setTurns([]); setConversationId(undefined); setConversationRevision(0);
    setPendingQuestion(''); setError((previous) => previous && ['inspect', 'analysis'].includes(previous.operation) ? previous : null);
    setBusy(null); setFocusComposer(true);
  };
  return <section className={`ai-workspace ${panelOpen ? '' : 'ai-panel-collapsed'}`} aria-label="Repository AI workspace">
    <header className="ai-toolbar">
      <div><SectionLabel>Development workspace</SectionLabel><h1>Ask Baton <span className={`ai-grounding ${ready ? '' : 'ai-grounding-muted'}`}>{headerLabel}</span></h1></div>
      <div className="ai-toolbar-actions">
        <button onClick={newChat} disabled={busy !== null && busy !== 'chat'}><Plus size={15} /> New chat</button>
        <button onClick={() => setPanelOpen((value) => !value)} aria-label={panelOpen ? 'Hide evidence panel' : 'Show evidence panel'}>{panelOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}</button>
      </div>
    </header>
    <div className="ai-scope-bar">
      <GitBranch size={14} />
      <select aria-label="Current repository branch" value={request.branch} onChange={(event) => state.setSelectedBranch(event.target.value)} disabled={!canOperate}>
        {!branches.some((branch) => branch.name === request.branch) && <option value={request.branch}>{request.branch || 'Default branch'}</option>}
        {branches.map((branch) => <option key={branch.name} value={branch.name}>{branch.name}</option>)}
      </select>
      <code title={currentHead || undefined}>{currentHead ? shortSha(currentHead) : 'Commit unavailable'}</code>
      <span className="ai-scope-divider" />
      <button onClick={() => setScopeOpen((open) => !open)} aria-expanded={scopeOpen}>{member?.name || 'Project scope'} <ChevronDown size={12} /></button>
      <button className="ai-refresh" onClick={refresh} disabled={!canOperate || busy !== null || retryBlocked}><RefreshCw size={13} className={busy === 'refresh' ? 'ai-spin' : ''} />{busy === 'refresh' ? 'Analyzing…' : actionLabel}</button>
    </div>
    <div className="ai-state-row"><div className="ai-visible-state"><code>{state.repo ? `${state.repo.owner}/${state.repo.repository}` : 'No repository'}</code><span className={`ai-lifecycle ai-lifecycle-${statusMessage.severity}`}>{ready ? 'Current' : statusMessage.title}</span><span>Commit: <code title={currentHead || undefined}>{currentHead ? shortSha(currentHead) : 'Commit unavailable'}</code></span><span>Role: {member?.role || 'Unassigned'}</span><span>Ownership: {member ? member.folders.join(', ') || 'Unassigned' : 'Project-wide'}</span></div>{branchNotice && <p className="ai-branch-notice" role="status">{branchNotice}</p>}
      {canOperate && !ready && <StatusPanel {...statusMessage} className="ai-analysis-status"
        technicalDetails={error?.cause instanceof BatonApiError ? `HTTP ${error.cause.status} · ${error.cause.code}` : lifecycle === 'SNAPSHOT_INVALID' ? 'Snapshot identity or validity did not match the selected repository, branch, folder and commit.' : undefined}
        primaryAction={!['CONNECTING', 'ANALYZING', 'EMPTY_REPOSITORY'].includes(lifecycle) && <Button onClick={refresh} disabled={!!busy || retryBlocked}>{actionLabel}</Button>}
        secondaryAction={lifecycle !== 'ANALYZING' && <Button variant="ghost" onClick={() => document.querySelector<HTMLSelectElement>('[aria-label="Current repository branch"]')?.focus()}>Switch branch</Button>}>
        {currentHead && <p className="baton-status-commit">Current commit <code title={currentHead}>{shortSha(currentHead)}</code></p>}
      </StatusPanel>}
      {!!branchError && <ErrorStatus error={branchError} operation="branch" />}
      {ready && inspection && (inspection.completeness.status !== 'COMPLETE' || inspection.completeness.files_omitted > 0 || inspection.completeness.budget_omitted_blocks > 0) && <StatusPanel severity="warning" title="Analysis completed with limited coverage" explanation={`${inspection.completeness.files_omitted} source files and ${inspection.completeness.budget_omitted_blocks} context blocks were omitted. Review the omissions in Working context before relying on an absent feature.`} />}
      {ready && inspection?.project_types?.includes('Documentation / Specification Only') && <StatusPanel severity="info" title="Documentation and specifications found" explanation="Baton found project documentation with limited implementation evidence. Documented plans do not establish that features are implemented." />}
      {scopeOpen && <div className="ai-scope-editor">
      <label>Developer<select aria-label="Developer" value={scopeDraft.memberId} onChange={(event) => setScopeDraft({ ...scopeDraft, memberId: event.target.value })}><option value="">Project-wide / ownership not configured</option>{state.members.map((person) => <option key={person.id} value={person.id}>{person.name} · {person.role}</option>)}</select></label>
      <label>Explicit task<textarea value={scopeDraft.task} maxLength={8000} onChange={(event) => setScopeDraft({ ...scopeDraft, task: event.target.value })} placeholder="What are you working on?" /></label>
      <label>Do not touch · one scope per line<textarea value={scopeDraft.protectedScopes} maxLength={4000} onChange={(event) => setScopeDraft({ ...scopeDraft, protectedScopes: event.target.value })} placeholder={'database/\ndeployment/'} /></label>
      <label>Task constraints · one per line<textarea value={scopeDraft.constraints} maxLength={8000} onChange={(event) => setScopeDraft({ ...scopeDraft, constraints: event.target.value })} placeholder="Preserve the existing request contract" /></label>
      <button className="ai-apply-scope" onClick={() => { setMemberId(scopeDraft.memberId); setTask(scopeDraft.task); setProtectedScopes(scopeDraft.protectedScopes); setConstraints(scopeDraft.constraints); setScopeOpen(false); }}>Apply scope</button>
      <p>Role and ownership come from Team & Ownership. Protected files stay readable; scope changes start a fresh conversation.</p>
    </div>}</div>
    <div className="ai-center">
      <div className="ai-conversation" role="log" aria-label="Conversation">
        {turns.length === 0 && !pendingQuestion && <div className={`ai-welcome ${ready ? '' : 'ai-welcome-pending'}`}>
          <div className="ai-baton-mark" aria-hidden="true"><i /><i /><i /></div>
          <span className="ai-eyebrow">A clearer view of your code</span>
          <h2>One repository.<br />Shared understanding.</h2>
          <p>Explore architecture, understand the gaps, and prepare your next change with evidence from the connected snapshot.</p>
          {!canOperate ? <div className="ai-get-started"><p>{state.isDemoMode ? 'Live AI uses authorized repository snapshots. Connect a repository to leave demo mode.' : 'Connect a repository to begin, then explicitly analyze its branch.'}</p><button onClick={() => state.setActiveSection('repository')}>Connect repository <GitBranch size={14} /></button></div>
          : ready ? <div className="ai-suggestions">{suggestions.map((suggestion, index) => <button key={suggestion} disabled={!chatReady || busy !== null} onClick={() => ask(suggestion)}><span>0{index + 1}</span>{suggestion}<ArrowUp size={14} /></button>)}</div> : null}
        </div>}
        {(inspectionMatches ? turns : []).map((turn) => <article className="ai-turn" key={turn.id}>
          <div className="ai-user-message"><span>You</span><p>{turn.question}</p></div>
          <div className="ai-assistant-message"><div className="ai-message-byline"><span className="ai-mini-mark">B</span><strong>Baton</strong><span>{turn.result.status.replace(/_/g, ' ')}</span><code>{shortSha(turn.result.identity.commit)}</code></div>
            <Markdown text={turn.result.answer} />
            {turn.result.confidence && <p className="ai-answer-confidence">Confidence: {turn.result.confidence}</p>}
            {turn.result.artifact && <Button variant="secondary" onClick={() => setActiveArtifact(turn.result.artifact!)}>View {artifactNames[turn.result.artifact.artifact_type]}</Button>}
            {turn.result.intent && !turn.result.artifact && <div className="ai-contextual-actions">{(turn.result.intent === 'ARCHITECTURE' ? ['Explain the architecture deeper', 'Generate a technical design'] : ['STATUS', 'IMPLEMENTATION_GAP', 'NEXT_TASK'].includes(turn.result.intent) ? ['What should I work on next?', 'Generate a task breakdown'] : ['API_ANALYSIS', 'FILE_EXPLANATION', 'INTEGRATION_ANALYSIS'].includes(turn.result.intent) ? ['Generate a Codex prompt for this', 'Generate an Anti-Gravity prompt for this'] : []).map((question) => <button key={question} disabled={!!busy || !chatReady} onClick={() => ask(question)}>{question}</button>)}</div>}
            {turn.result.actions.length > 0 && <div className="ai-actions-list"><h3>Suggested investigation</h3>{turn.result.actions.map((action, index) => <p key={index}><Check size={13} />{action.text}</p>)}</div>}
            {turn.result.citations.length > 0 && <details className="ai-citations"><summary>{turn.result.citations.length} evidence references · {turn.result.completeness.status.toLowerCase()} context</summary>{turn.result.citations.map((citation) => <div key={citation.id}><code>{citation.id}</code><span>{citation.source_paths.length ? citation.source_paths.map((path) => <button className="ai-file-link" key={path} onClick={() => openFile(path, turn.result.identity.commit)}>{path}</button>) : 'Canonical snapshot metadata'}</span></div>)}</details>}
            <div className="ai-message-controls"><CopyButton text={turn.result.answer} label="Copy answer" /><button onClick={() => download(turn.result.answer, `baton-answer-${shortSha(turn.result.identity.commit)}.md`)}><Download size={12} /> Export answer</button></div>
          </div>
        </article>)}
        {pendingQuestion && <article className="ai-turn"><div className="ai-user-message"><span>You</span><p>{pendingQuestion}</p></div><div className="ai-thinking" role="status"><i /><i /><i /> Selecting evidence from this snapshot…</div></article>}
        <div ref={bottom} />
      </div>
      <div className="ai-composer-area">
        {error && !['inspect', 'analysis'].includes(error.operation) && <ErrorStatus error={error.cause} operation={error.operation}
          primaryAction={message.trim() && <Button disabled={!!busy || retryBlocked || !chatReady} onClick={() => ask(message)}>Retry question</Button>}
          secondaryAction={<Button variant="ghost" onClick={newChat}>Start a fresh chat</Button>} />}
        {ready && inspection && !inspection.provider.configured && <StatusPanel {...repositoryMessage('CONFIGURATION_INCOMPLETE')} technicalDetails={inspection.provider.missing_configuration?.filter(name => ['GEMINI_API_KEY', 'GEMINI_MODEL', 'BATON_ACCESS_KEY'].includes(name)).join(', ')} />}
        {!ready && canOperate && <p className="ai-composer-explanation">{lifecycle === 'ANALYZING' ? 'Analysis is running. Chat will be available when this branch is ready.' : 'Analyze this branch before asking Baton about the repository.'}</p>}
        {stopNotice && <p role="status" className="ai-composer-explanation">{stopNotice}</p>}
        <form className="ai-composer" onSubmit={(event) => { event.preventDefault(); ask(); }}>
          <textarea ref={composer} aria-label="Ask about the connected repository" placeholder={chatReady ? 'Ask about this repository…' : ready ? 'AI chat awaits server configuration' : canOperate ? 'Analyze this branch to ask Baton' : 'Connect a repository to ask Baton'} value={message} maxLength={8000} disabled={!chatReady || !!busy} onChange={(event) => setMessage(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); ask(); } }} />
          <div><span><GitBranch size={11} />{state.repo ? `${state.repo.owner}/${state.repo.repository}` : 'No repository connected'}</span>{busy === 'chat' ? <button type="button" aria-label="Stop waiting for the response" onClick={(event) => { event.preventDefault(); controller.current?.abort(); chatLock.current = null; epoch.current++; setMessage(pendingQuestion); setPendingQuestion(''); setBusy(null); setStopNotice('Stopped waiting. Remote work may still finish. A changed conversation will require New Chat before retrying.'); }}><Square size={14} /></button> : <button type="submit" aria-label="Send repository question" disabled={!chatReady || !!busy || retryBlocked || !message.trim()}><ArrowUp size={18} /></button>}</div>
        </form>
        <p className="ai-composer-footnote">Facts come from canonical evidence. Unknowns remain unknown. Shift + Enter for a new line.</p>
      </div>
    </div>
    {panelOpen && <aside className="ai-evidence-panel" aria-label="Snapshot, artifacts and branch comparison">
      <div className="ai-panel-heading"><span className="ai-eyebrow">Working context</span><Files size={15} /></div>
      <Panel className="ai-snapshot-card" label="SNAPSHOT"><h2>Snapshot</h2>{ready && inspection ? <><div className="ai-snapshot-state"><i />Current · {inspection.completeness.status.toLowerCase()} coverage</div><p>Repository intelligence is synchronized with this branch and commit.</p><dl><dt>Branch</dt><dd>{inspection.identity.branch}</dd><dt>Commit</dt><dd><code>{shortSha(inspection.identity.commit)}</code></dd><dt>Analyzed</dt><dd>{new Date(inspection.identity.analysis_timestamp).toLocaleString()}</dd><dt>Files analyzed</dt><dd>{inspection.completeness.files_analyzed} / {inspection.completeness.files_discovered}</dd><dt>Source omissions</dt><dd>{inspection.completeness.files_omitted}</dd><dt>Budget omissions</dt><dd>{inspection.completeness.budget_omitted_blocks}</dd></dl>
        <details><summary>Ownership & boundaries</summary><p>Editable: {inspection.relevance.editable_files.join(', ') || 'Ownership configuration was not provided.'}</p><p>Protected: {inspection.relevance.protected_files.join(', ') || 'No matching protected paths'}</p><p>Cross-boundary reading: {inspection.relevance.cross_boundary_files.join(', ') || 'None recorded'}</p></details>
        {inspection.omission_manifest.length > 0 && <details><summary>Review {inspection.omission_manifest.length} omissions</summary>{inspection.omission_manifest.map((item, index) => <p key={index}><strong>{item.category}</strong> · {item.source_paths.join(', ') || item.record} · {item.reason}</p>)}</details>}
      </> : <><h3 className="ai-context-state">{lifecycle === 'NOT_ANALYZED' ? 'No analysis snapshot yet' : statusMessage.title}</h3><p>{statusMessage.explanation}</p>{currentHead && <p>Branch {request.branch} · <code title={currentHead}>{shortSha(currentHead)}</code></p>}{canOperate && !['CONNECTING', 'ANALYZING', 'EMPTY_REPOSITORY'].includes(lifecycle) && <Button variant="secondary" onClick={refresh} disabled={!!busy || retryBlocked}>{actionLabel}</Button>}</>}</Panel>
      <section className="ai-artifacts"><div className="ai-panel-title"><h2>Artifacts</h2><span>{artifacts.length.toString().padStart(2, '0')}</span></div><p>Reviewable drafts from the same context.</p>{artifactType === 'prompt' && <select aria-label="Coding agent target" value={promptTarget} onChange={(event) => setPromptTarget(event.target.value)}>{['Codex', 'Anti-Gravity', 'Claude Code', 'Cursor'].map((target) => <option key={target}>{target}</option>)}</select>}<select aria-label="Artifact type" value={artifactType} onChange={(event) => setArtifactType(event.target.value as ArtifactType)}>{Object.entries(artifactNames).map(([kind, label]) => <option key={kind} value={kind}>{label}</option>)}</select><button className="ai-generate" disabled={!ready || !!busy || (artifactType === 'prompt' && !task.trim())} onClick={generateArtifact}><Plus size={14} />{busy === 'artifact' ? 'Preparing…' : 'Generate artifact'}</button>{artifactType === 'prompt' && !task.trim() && <p>Set an explicit task in scope settings to generate a prompt.</p>}
        {(inspectionMatches ? artifacts : []).map((artifact) => <button className={`ai-artifact-item ${activeArtifact === artifact ? 'ai-artifact-active' : ''}`} key={artifact.artifact_type} onClick={() => setActiveArtifact(artifact)}><FileText size={17} /><span>{artifactNames[artifact.artifact_type]}<small>{shortSha(artifact.identity.commit)} · Markdown</small></span></button>)}
      </section>
      <section className="ai-branch-review"><h2>Branch review <ArrowLeftRight size={14} /></h2><p>Compare two existing snapshots. Analyze the comparison branch first.</p><select aria-label="Comparison branch" disabled={!!busy} value={compareBranch} onChange={(event) => { setCompareBranch(event.target.value); setComparison(null); }}><option value="">Choose a branch</option>{branches.filter((branch) => branch.name !== request.branch).map((branch) => <option key={branch.name} value={branch.name}>{branch.name}</option>)}</select><button disabled={!ready || !compareBranch || !!busy} onClick={compare}>{busy === 'compare' ? 'Comparing…' : 'Compare snapshots'}</button>
        {inspectionMatches && comparison && <div className="ai-comparison"><p>{comparison.before.branch} <code>{shortSha(comparison.before.commit)}</code> vs {comparison.after.branch} <code>{shortSha(comparison.after.commit)}</code></p><p>{comparison.changed_blob_paths.length} changed blobs · {comparison.contract_changes.length} contract changes</p><details><summary>View comparison</summary><p>Only in base inventory: {comparison.only_in_before_inventory.join(', ') || 'None'}</p><p>Only in comparison inventory: {comparison.only_in_after_inventory.join(', ') || 'None'}</p><p>Changed: {comparison.changed_blob_paths.join(', ') || 'None'}</p><p>Unknown hashes: {comparison.unknown_blob_paths.join(', ') || 'None'}</p><p>Protected changes: {comparison.protected_changes.join(', ') || 'None'}</p>{comparison.contract_changes.map((change, index) => <p key={index}>{change.method} {change.route} · {change.source_file}<code>{JSON.stringify({ before: change.before, after: change.after })}</code></p>)}{Object.entries(comparison.findings || {}).map(([category, findings]) => <div key={category}><h3>{category.replace(/_/g, ' ')} ? {findings.length} differences</h3>{findings.map((finding) => <details key={finding.record}><summary>{finding.record}</summary><p>{finding.before_branch}</p><Markdown text={finding.before?.text || 'Not retained in base snapshot'} /><p>{finding.after_branch}</p><Markdown text={finding.after?.text || 'Not retained in comparison snapshot'} /></details>)}</div>)}<p>{comparison.warnings.join(' ')}</p></details><button onClick={() => download(JSON.stringify(comparison, null, 2), 'baton-branch-comparison.json')}>Export comparison</button></div>}
      </section>
    </aside>}
    {inspectionMatches && activeArtifact && <div ref={preview} className="ai-artifact-preview" role="dialog" aria-modal="true" aria-label={artifactNames[activeArtifact.artifact_type]}>
      <header><div><span className="ai-eyebrow">Artifact preview</span><h2>{artifactNames[activeArtifact.artifact_type]}</h2><code>{activeArtifact.filename}</code></div><div><CopyButton text={activeArtifact.content} label="Copy" /><button onClick={() => download(activeArtifact.content, activeArtifact.filename)}><Download size={14} /> Download</button><button onClick={() => setActiveArtifact(null)}>Close</button></div></header>
      <div className="ai-artifact-content"><Markdown text={activeArtifact.content} /></div>
    </div>}
  </section>;
}
