import { ErrorStatus } from '@/components/ui/StatusPanel';
import { useState, useEffect, useRef } from 'react';
import { Loader2, Download, RotateCcw } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import { batonApi } from '@/lib/api/batonApi';
import { Button, CopyButton, MonoLabel, Panel, SectionLabel, TelemetryLine } from '@/components/ui/primitives';
import { cn } from '@/lib/utils';

type PromptMode = 'chat-first' | 'direct';
type PromptState = 'idle' | 'loading' | 'success' | 'error';

const STARTER_PROMPT = `Read the Baton context before beginning.

Follow the ownership rules.
Only create or edit files inside your owned folders unless explicitly instructed.
Use existing contracts exactly.
Do not silently invent interfaces.
State assumptions before implementing uncertain behavior.

When the task is complete, provide a concise Handoff containing:
- what was completed;
- what it depends on;
- what remains;
- any important assumptions.`;

export function PromptBuilder({ state }: { state: WorkspaceStateHook }) {
  const [grounding, setGrounding] = useState<'canonical' | 'manual'>('canonical');
  const epoch = useRef(0);
  const [mode, setMode] = useState<PromptMode>('chat-first');
  const [promptState, setPromptState] = useState<PromptState>('idle');
  const [generatedPrompt, setGeneratedPrompt] = useState('');
  const [error, setError] = useState<Error | null>(null);
  const [form, setForm] = useState({
    task: '',
    context: '',
    constraints: '',
    ownership: '',
    targetMember: '',
  });

  useEffect(() => {
    epoch.current++; setGeneratedPrompt(''); setPromptState('idle'); setError(null);
    const requestEpoch = epoch;
    return () => { requestEpoch.current++; };
  }, [state.repo, state.selectedBranch, state.selectedFolder, state.members, state.githubToken, state.batonAccessKey, state.analysisRevision, grounding, mode, form]);

  const handleGenerate = async () => {
    if (!form.task.trim()) return;
    const current = ++epoch.current;
    setPromptState('loading');
    setError(null);

    const constraints = form.constraints
      .split('\n')
      .map((c) => c.trim())
      .filter(Boolean);

    if (form.ownership) {
      constraints.push(`Only edit files inside your owned folders: ${form.ownership}`);
    }
    if (form.targetMember) constraints.push(`Target teammate: ${state.members.find((item) => item.id === form.targetMember)?.name || form.targetMember}`);
    constraints.push('State assumptions before implementing uncertain behavior.');

    if (state.isDemoMode) {
      setTimeout(() => {
        if (current !== epoch.current) return;
        const prompt = mode === 'chat-first'
          ? `## Planning AI Instructions\n\nYou are helping plan a coding task for an AI coding agent.\n\n### Task\n${form.task}\n\n### Context\n${form.context || 'See Baton context packet.'}\n\n### Constraints\n${constraints.map((c) => `- ${c}`).join('\n')}\n\n### Ownership\n${form.ownership || 'No ownership boundaries configured.'}\n\n### Target Teammate\n${form.targetMember || 'Not specified'}\n\nGenerate a focused coding prompt for the AI coding agent (Antigravity / Cursor).\nThe prompt should include all necessary context for implementation.\n\n---\n\n### Starter Instructions\n\n${STARTER_PROMPT}`
          : `You are working on the Baton repository.\n\nTask:\n${form.task}\n\nConstraints:\n${constraints.map((c) => `- ${c}`).join('\n')}\n\nRepository context:\n${form.context || 'No additional context provided.'}\n\nOwnership:\n${form.ownership || 'No ownership boundaries configured.'}\n\nTarget:\n${form.targetMember || 'Not specified'}\n\n---\n\n${STARTER_PROMPT}`;
        setGeneratedPrompt(prompt);
        setPromptState('success');
      }, 1200);
      return;
    }

    try {
      let prompt: string;
      if (grounding === 'canonical') {
        if (!state.repo) throw new Error('Connect and analyze a repository, or select Manual input.');
        const member = state.members.find((item) => item.id === form.targetMember);
        const artifact = await batonApi.artifact({ owner: state.repo.owner, repo: state.repo.repository, branch: state.selectedBranch || 'main', folder: state.selectedFolder, context_type: 'ai_handoff', artifact_type: 'prompt', task: form.task, constraints: [...constraints, ...(form.context ? [`User-supplied context (unverified): ${form.context}`] : [])], member: member || form.ownership ? { name: member?.name, role: member?.role, responsibilities: member?.job ? [member.job] : [], ownership: member ? member.folders : form.ownership.split(',').map((item) => item.trim()).filter(Boolean), do_not_touch: member?.do_not_touch || [], team_scope: member?.team_scope || [] } : undefined, target: 'Codex' }, state.githubToken || undefined);
        prompt = artifact.content;
      } else {
        const res = await batonApi.generatePrompt(form.task, form.context, constraints, state.githubToken || undefined, state.repo ? `${state.repo.owner}/${state.repo.repository}` : 'User-supplied project');
        prompt = res.prompt;
      }
      if (current !== epoch.current) return;
      const fullPrompt = mode === 'chat-first'
        ? `## Planning AI Instructions\n\n${prompt}\n\n---\n\n### Starter Instructions\n\n${STARTER_PROMPT}`
        : `${prompt}\n\n---\n\n${STARTER_PROMPT}`;
      setGeneratedPrompt(fullPrompt);
      setPromptState('success');
    } catch (err) {
      if (current !== epoch.current) return;
      setPromptState('error');
      setError(err instanceof Error ? err : new Error('Prompt generation failed'));
    }
  };

  const handleReset = () => {
    setForm({ task: '', context: '', constraints: '', ownership: '', targetMember: '' });
    setGeneratedPrompt('');
    setPromptState('idle');
  };

  const handleDownload = () => {
    const blob = new Blob([generatedPrompt], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'prompt.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 lg:p-8 max-w-6xl">
      <SectionLabel className="mb-6">PROMPT BUILDER</SectionLabel>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Prompt Builder</h1>
      <p className="text-sm text-baton-text-tertiary mb-8">
        Baton hands the baton to the coding agent. The external AI does the reasoning.
      </p>

      <select aria-label="Prompt evidence source" value={grounding} onChange={(e) => setGrounding(e.target.value as typeof grounding)} className="mb-4 border border-baton-border bg-baton-black px-3 py-2 text-sm">
        <option value="canonical">Canonical snapshot</option>
        <option value="manual">Manual input — unverified</option>
      </select>
      {/* Mode toggle */}
      <div className="flex items-center gap-px bg-baton-border mb-6 w-fit rounded-baton overflow-hidden">
        <button
          onClick={() => setMode('chat-first')}
          className={cn(
            'px-5 py-2 text-xs font-medium tracking-wider uppercase transition-colors',
            mode === 'chat-first' ? 'bg-baton-accent text-baton-black' : 'bg-baton-near-black text-baton-text-secondary hover:text-baton-white'
          )}
        >
          CHAT-FIRST
        </button>
        <button
          onClick={() => setMode('direct')}
          className={cn(
            'px-5 py-2 text-xs font-medium tracking-wider uppercase transition-colors',
            mode === 'direct' ? 'bg-baton-accent text-baton-black' : 'bg-baton-near-black text-baton-text-secondary hover:text-baton-white'
          )}
        >
          DIRECT
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-6">
        {/* Left: Inputs */}
        <div className="space-y-4">
          <Panel label="INPUTS">
            <div className="p-5 space-y-4">
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Task
                </label>
                <textarea
                  aria-label="Prompt task"
                  value={form.task}
                  onChange={(e) => setForm({ ...form, task: e.target.value })}
                  placeholder="Implement user authentication endpoint in FastAPI"
                  rows={3}
                  className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none resize-none"
                />
              </div>
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Context
                </label>
                <textarea
                  aria-label="Prompt context"
                  value={form.context}
                  onChange={(e) => setForm({ ...form, context: e.target.value })}
                  placeholder="Paste Baton context or reference the context.md file..."
                  rows={4}
                  className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none resize-none font-mono text-[12px]"
                />
              </div>
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Constraints (one per line)
                </label>
                <textarea
                  aria-label="Prompt constraints"
                  value={form.constraints}
                  onChange={(e) => setForm({ ...form, constraints: e.target.value })}
                  placeholder={"Do not modify files outside app/api/routes/auth.py\nDo not add external dependencies without approval"}
                  rows={3}
                  className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none resize-none font-mono text-[12px]"
                />
              </div>
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Ownership
                </label>
                <input
                  type="text"
                  aria-label="Prompt ownership"
                  value={form.ownership}
                  onChange={(e) => setForm({ ...form, ownership: e.target.value })}
                  placeholder="/backend, /api"
                  className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono"
                />
              </div>
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Target Teammate
                </label>
                <select aria-label="Prompt teammate" value={form.targetMember} onChange={(e) => setForm({ ...form, targetMember: e.target.value })} className="w-full border border-baton-border bg-baton-black px-3 py-2 text-sm">
                  <option value="">Project scope</option>
                  {state.members.map((member) => <option key={member.id} value={member.id}>{member.name} — {member.role}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <Button variant="primary" onClick={handleGenerate} disabled={promptState === 'loading' || !form.task.trim()}>
                  {promptState === 'loading' ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      BUILDING...
                    </>
                  ) : 'BUILD PROMPT'}
                </Button>
                <Button variant="ghost" onClick={handleReset}>
                  <RotateCcw size={14} />
                  RESET
                </Button>
              </div>
            </div>
          </Panel>

          {/* Mode description */}
          <div className="border border-baton-border bg-baton-near-black rounded-baton p-4">
            <MonoLabel variant="accent" className="mb-2 block">
              {mode === 'chat-first' ? 'CHAT-FIRST MODE' : 'DIRECT MODE'}
            </MonoLabel>
            <p className="text-xs text-baton-text-tertiary leading-relaxed">
              {mode === 'chat-first'
                ? 'Context + PRD + job → ChatGPT / Claude → focused coding prompt → Antigravity / Cursor. Recommended for complex tasks.'
                : 'Outputs a direct coding-agent prompt. Skips the planning chat. Useful when you already understand the task.'}
            </p>
          </div>
        </div>

        {/* Right: Generated prompt */}
        <div>
          {promptState === 'loading' && (
            <Panel label="GENERATING PROMPT">
              <div className="p-8">
                <div className="flex items-center gap-3 mb-4">
                  <Loader2 size={16} className="animate-spin text-baton-accent" />
                  <MonoLabel variant="accent">BUILDING PROMPT</MonoLabel>
                </div>
                <TelemetryLine active />
              </div>
            </Panel>
          )}

          {promptState === 'error' && (
        <ErrorStatus error={error} operation="prompt" primaryAction={<Button variant="secondary" onClick={handleGenerate}>Retry request</Button>} />
      )}

          {promptState === 'success' && (
            <Panel>
              <div className="border-b border-baton-border px-4 py-2 flex items-center justify-between">
                <MonoLabel variant="accent">GENERATED PROMPT</MonoLabel>
                <div className="flex items-center gap-4">
                  <CopyButton text={generatedPrompt} label="COPY PROMPT" />
                  <button
                    onClick={handleDownload}
                    className="inline-flex items-center gap-1.5 font-mono text-[10px] tracking-wider text-baton-text-secondary hover:text-baton-accent transition-colors uppercase"
                  >
                    <Download size={12} />
                    DOWNLOAD
                  </button>
                </div>
              </div>
              <div className="p-5 max-h-[600px] overflow-y-auto">
                <pre className="font-mono text-[12px] leading-relaxed text-baton-text-highlight whitespace-pre-wrap break-words">
                  {generatedPrompt}
                </pre>
              </div>
            </Panel>
          )}

          {promptState === 'idle' && (
            <Panel>
              <div className="p-12 text-center">
                <p className="text-sm text-baton-text-tertiary mb-1">NO PROMPT GENERATED</p>
                <p className="text-xs text-baton-text-tertiary">Fill in the task and click BUILD PROMPT.</p>
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
