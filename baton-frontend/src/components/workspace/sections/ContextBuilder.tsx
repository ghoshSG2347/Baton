import { motion } from 'framer-motion';
import { useState } from 'react';
import { Loader2, Download, RefreshCw } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import type { ContextResult } from '@/types';
import { batonApi } from '@/lib/api/batonApi';
import { DEMO_CONTEXT_MARKDOWN } from '@/lib/demo';
import { Button, CopyButton, MonoLabel, Panel, SectionLabel, TelemetryLine } from '@/components/ui/primitives';
import { shortSha, formatTimestamp, formatNumber } from '@/lib/utils';

type ContextState = 'idle' | 'loading' | 'success' | 'error';

export function ContextBuilder({ state }: { state: WorkspaceStateHook }) {
  const [ctxState, setCtxState] = useState<ContextState>('idle');
  const [result, setResult] = useState<ContextResult | null>(null);
  const [markdown, setMarkdown] = useState<string>('');
  const [tokens, setTokens] = useState(0);
  const [omitted, setOmitted] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [config, setConfig] = useState({
    folder: state.selectedFolder || '',
    purpose: '',
    targetMember: '',
    budget: '8000',
  });

  const hasRepo = state.repo || state.isDemoMode;

  const handleGenerate = async () => {
    if (!hasRepo) return;
    setCtxState('loading');
    setError('');

    if (state.isDemoMode) {
      setTimeout(() => {
        setMarkdown(DEMO_CONTEXT_MARKDOWN);
        setTokens(3280);
        setOmitted([]);
        setResult({
          analysis: {} as never,
          markdown: DEMO_CONTEXT_MARKDOWN,
          estimated_tokens: 3280,
          omitted: [],
        });
        setCtxState('success');
      }, 1500);
      return;
    }

    try {
      if (!state.repo) return;
      const res = await batonApi.generateContext(
        state.repo.owner,
        state.repo.repository,
        state.selectedBranch || 'main',
        config.folder,
        true,
        state.githubToken || undefined
      );
      setMarkdown(res.markdown);
      setTokens(res.estimated_tokens);
      setOmitted(res.omitted);
      setResult(res);
      setCtxState('success');
    } catch (err) {
      setCtxState('error');
      setError(err instanceof Error ? err.message : 'Context generation failed');
    }
  };

  const handleDownload = () => {
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'context.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  const budget = parseInt(config.budget) || 8000;
  const budgetPercent = Math.min(100, (tokens / budget) * 100);

  if (!hasRepo) {
    return (
      <div className="p-6 lg:p-8">
        <SectionLabel className="mb-6">CONTEXT BUILDER</SectionLabel>
        <Panel>
          <div className="p-12 text-center">
            <p className="text-sm text-baton-text-tertiary mb-2">NO REPOSITORY CONNECTED</p>
            <p className="text-xs text-baton-text-tertiary">Connect a GitHub repository to generate context.</p>
          </div>
        </Panel>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-6xl">
      <SectionLabel className="mb-6">CONTEXT BUILDER</SectionLabel>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Context Builder</h1>
      <p className="text-sm text-baton-text-tertiary mb-8">Generate a focused, token-budgeted Markdown context packet from the repository.</p>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        {/* Left: Configuration */}
        <div className="space-y-4">
          <Panel label="CONFIGURATION">
            <div className="p-5 space-y-4">
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Repository
                </label>
                <div className="font-mono text-[12px] text-baton-text-highlight">
                  {state.repo ? `${state.repo.owner}/${state.repo.repository}` : 'baton/demo-project'}
                </div>
              </div>
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Branch
                </label>
                <div className="font-mono text-[12px] text-baton-text-highlight">
                  {state.selectedBranch || 'main'}
                </div>
              </div>
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Folder
                </label>
                <input
                  type="text"
                  value={config.folder}
                  onChange={(e) => setConfig({ ...config, folder: e.target.value })}
                  placeholder="/frontend"
                  className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono"
                />
              </div>
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Purpose / Task
                </label>
                <textarea
                  value={config.purpose}
                  onChange={(e) => setConfig({ ...config, purpose: e.target.value })}
                  placeholder="Backend integration handoff"
                  rows={2}
                  className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none resize-none"
                />
              </div>
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Target Teammate
                </label>
                <input
                  type="text"
                  value={config.targetMember}
                  onChange={(e) => setConfig({ ...config, targetMember: e.target.value })}
                  placeholder="Arjun"
                  className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none"
                />
              </div>
              <div>
                <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                  Budget (tokens)
                </label>
                <input
                  type="text"
                  value={config.budget}
                  onChange={(e) => setConfig({ ...config, budget: e.target.value })}
                  className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2 text-sm text-baton-white outline-none font-mono"
                />
              </div>
              <Button
                variant="primary"
                onClick={handleGenerate}
                disabled={ctxState === 'loading'}
                className="w-full"
              >
                {ctxState === 'loading' ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    GENERATING...
                  </>
                ) : 'GENERATE CONTEXT'}
              </Button>
            </div>
          </Panel>

          {/* Token budget */}
          {ctxState === 'success' && (
            <Panel label="CONTEXT BUDGET">
              <div className="p-5">
                <div className="flex items-center justify-between mb-2">
                  <MonoLabel>ESTIMATED TOKENS</MonoLabel>
                  <span className="font-mono text-[12px] text-baton-accent">
                    {formatNumber(tokens)} / {formatNumber(budget)}
                  </span>
                </div>
                <div className="h-1 bg-baton-border rounded-full overflow-hidden mb-3">
                  <motion.div
                    className="h-full bg-baton-accent rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${budgetPercent}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <div className="font-mono text-[10px] text-baton-text-tertiary uppercase">
                  {Math.round(budgetPercent)}% of budget used
                </div>
                {omitted.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-baton-border">
                    <MonoLabel variant="warning" className="mb-2 block">OMITTED</MonoLabel>
                    <div className="space-y-1">
                      {omitted.map((item, i) => (
                        <div key={i} className="font-mono text-[11px] text-baton-text-tertiary">{item}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Panel>
          )}
        </div>

        {/* Right: Generated context preview */}
        <div>
          {ctxState === 'loading' && (
            <Panel label="BATON CONTEXT">
              <div className="p-8">
                <div className="flex items-center gap-3 mb-4">
                  <Loader2 size={16} className="animate-spin text-baton-accent" />
                  <MonoLabel variant="accent">GENERATING CONTEXT</MonoLabel>
                </div>
                <TelemetryLine active />
                <div className="mt-4 font-mono text-[11px] text-baton-text-tertiary space-y-1">
                  <div>Analyzing branch files...</div>
                  <div>Extracting routes and API calls...</div>
                  <div>Detecting types and mock data...</div>
                  <div>Formatting Markdown context...</div>
                  <div>Estimating token count...</div>
                </div>
              </div>
            </Panel>
          )}

          {ctxState === 'error' && (
            <Panel label="ERROR">
              <div className="p-8 text-center">
                <p className="text-sm text-baton-warning mb-2">CONTEXT GENERATION FAILED</p>
                <p className="text-xs text-baton-text-tertiary mb-4">{error}</p>
                <Button variant="secondary" onClick={handleGenerate}>RETRY</Button>
              </div>
            </Panel>
          )}

          {ctxState === 'success' && (
            <Panel>
              <div className="border-b border-baton-border px-4 py-2 flex items-center justify-between flex-wrap gap-2">
                <MonoLabel variant="accent">BATON CONTEXT</MonoLabel>
                <div className="flex items-center gap-4">
                  <CopyButton text={markdown} label="COPY" />
                  <button
                    onClick={handleDownload}
                    className="inline-flex items-center gap-1.5 font-mono text-[10px] tracking-wider text-baton-text-secondary hover:text-baton-accent transition-colors uppercase"
                  >
                    <Download size={12} />
                    DOWNLOAD
                  </button>
                  <button
                    onClick={handleGenerate}
                    className="inline-flex items-center gap-1.5 font-mono text-[10px] tracking-wider text-baton-text-secondary hover:text-baton-accent transition-colors uppercase"
                  >
                    <RefreshCw size={12} />
                    REFRESH
                  </button>
                </div>
              </div>
              {/* Metadata header */}
              <div className="border-b border-baton-border px-4 py-2 grid grid-cols-2 md:grid-cols-3 gap-2">
                <div>
                  <span className="font-mono text-[9px] text-baton-text-tertiary uppercase">BRANCH</span>
                  <div className="font-mono text-[11px] text-baton-text-highlight">{state.selectedBranch || 'main'}</div>
                </div>
                <div>
                  <span className="font-mono text-[9px] text-baton-text-tertiary uppercase">COMMIT</span>
                  <div className="font-mono text-[11px] text-baton-text-highlight">{result ? shortSha(result.markdown.match(/commit[:\s]+([a-f0-9]+)/i)?.[1] || '') : 'a1b2c3d'}</div>
                </div>
                <div>
                  <span className="font-mono text-[9px] text-baton-text-tertiary uppercase">GENERATED</span>
                  <div className="font-mono text-[11px] text-baton-text-highlight">{formatTimestamp(new Date().toISOString())}</div>
                </div>
              </div>
              {/* Markdown preview */}
              <div className="p-5 max-h-[600px] overflow-y-auto">
                <pre className="font-mono text-[12px] leading-relaxed text-baton-text-highlight whitespace-pre-wrap break-words">
                  {markdown}
                </pre>
              </div>
            </Panel>
          )}

          {ctxState === 'idle' && (
            <Panel>
              <div className="p-12 text-center">
                <p className="text-sm text-baton-text-tertiary mb-1">NO CONTEXT GENERATED</p>
                <p className="text-xs text-baton-text-tertiary">Configure the options and click GENERATE CONTEXT.</p>
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
