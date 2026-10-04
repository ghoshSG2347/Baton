import { motion } from 'framer-motion';
import { useState } from 'react';
import { Loader2, GitMerge, ArrowRight } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import type { IntegrationResult } from '@/types';
import { batonApi } from '@/lib/api/batonApi';
import { DEMO_INTEGRATION } from '@/lib/demo';
import { Button, MonoLabel, Panel, SectionLabel, StatusIndicator, TelemetryLine } from '@/components/ui/primitives';
import { cn } from '@/lib/utils';

type IntegrationState = 'idle' | 'loading' | 'success' | 'error';

export function Integration({ state }: { state: WorkspaceStateHook }) {
  const [intState, setIntState] = useState<IntegrationState>('idle');
  const [result, setResult] = useState<IntegrationResult | null>(null);
  const [error, setError] = useState('');
  const [frontendBranch, setFrontendBranch] = useState('');
  const [backendBranch, setBackendBranch] = useState('');

  const hasRepo = state.repo || state.isDemoMode;

  const handleCheck = async () => {
    if (!frontendBranch.trim() || !backendBranch.trim()) return;
    setIntState('loading');
    setError('');

    if (state.isDemoMode) {
      setTimeout(() => {
        setResult(DEMO_INTEGRATION);
        setIntState('success');
      }, 1500);
      return;
    }

    try {
      if (!state.repo) return;
      const res = await batonApi.checkIntegration(
        state.repo.owner,
        state.repo.repository,
        state.selectedBranch || 'main',
        frontendBranch,
        backendBranch,
        state.githubToken || undefined
      );
      setResult(res);
      setIntState('success');
    } catch (err) {
      setIntState('error');
      setError(err instanceof Error ? err.message : 'Integration check failed');
    }
  };

  if (!hasRepo) {
    return (
      <div className="p-6 lg:p-8">
        <SectionLabel className="mb-6">INTEGRATION</SectionLabel>
        <Panel>
          <div className="p-12 text-center">
            <p className="text-sm text-baton-text-tertiary mb-2">NO REPOSITORY CONNECTED</p>
            <p className="text-xs text-baton-text-tertiary">Connect a repository to check integration.</p>
          </div>
        </Panel>
      </div>
    );
  }

  const comparison = result?.comparison;

  return (
    <div className="p-6 lg:p-8 max-w-6xl">
      <SectionLabel className="mb-6">INTEGRATION</SectionLabel>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Integration</h1>
      <p className="text-sm text-baton-text-tertiary mb-8">
        Compare frontend API calls with backend routes. Detect unmatched endpoints before they become integration bugs.
      </p>

      {/* Branch inputs */}
      <div className="flex flex-col sm:flex-row items-end gap-3 mb-6">
        <div className="flex-1 max-w-xs">
          <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
            Frontend Branch
          </label>
          <input
            type="text"
            value={frontendBranch}
            onChange={(e) => setFrontendBranch(e.target.value)}
            placeholder="member/maya-ui"
            className="w-full border border-baton-border bg-baton-near-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono"
          />
        </div>
        <div className="flex-1 max-w-xs">
          <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
            Backend Branch
          </label>
          <input
            type="text"
            value={backendBranch}
            onChange={(e) => setBackendBranch(e.target.value)}
            placeholder="member/arjun-api"
            className="w-full border border-baton-border bg-baton-near-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono"
          />
        </div>
        <Button variant="primary" onClick={handleCheck} disabled={intState === 'loading' || !frontendBranch.trim() || !backendBranch.trim()}>
          {intState === 'loading' ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              COMPARING...
            </>
          ) : 'CHECK INTEGRATION'}
        </Button>
      </div>

      {/* Loading */}
      {intState === 'loading' && (
        <Panel>
          <div className="p-8">
            <div className="flex items-center gap-3 mb-4">
              <GitMerge size={16} className="text-baton-accent" />
              <MonoLabel variant="accent">COMPARING BRANCHES</MonoLabel>
            </div>
            <TelemetryLine active />
            <div className="mt-4 font-mono text-[11px] text-baton-text-tertiary space-y-1">
              <div>Analyzing frontend branch for API calls...</div>
              <div>Analyzing backend branch for routes...</div>
              <div>Normalizing and comparing endpoints...</div>
            </div>
          </div>
        </Panel>
      )}

      {/* Error */}
      {intState === 'error' && (
        <Panel>
          <div className="p-8 text-center">
            <p className="text-sm text-baton-warning mb-2">INTEGRATION CHECK FAILED</p>
            <p className="text-xs text-baton-text-tertiary mb-4">{error}</p>
            <Button variant="secondary" onClick={handleCheck}>RETRY</Button>
          </div>
        </Panel>
      )}

      {/* Results */}
      {intState === 'success' && comparison && (
        <>
          {/* Status bar */}
          <div
            className={cn(
              'border rounded-baton p-4 mb-6 flex items-center justify-between',
              comparison.compatible
                ? 'border-baton-accent/30 bg-baton-near-black'
                : 'border-baton-warning/30 bg-baton-near-black'
            )}
          >
            <div className="flex items-center gap-3">
              <StatusIndicator status={comparison.compatible ? 'connected' : 'attention'} />
              <MonoLabel variant={comparison.compatible ? 'accent' : 'warning'}>
                {comparison.compatible ? 'INTEGRATION STATUS — READY' : 'INTEGRATION STATUS — ATTENTION REQUIRED'}
              </MonoLabel>
            </div>
            <span className="font-mono text-[11px] text-baton-text-tertiary">
              {comparison.unmatched_frontend_routes.length + comparison.unmatched_backend_routes.length} unmatched
            </span>
          </div>

          {/* Comparison grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Frontend routes */}
            <Panel label="FRONTEND BRANCH — API CALLS">
              <div className="p-4 space-y-1.5">
                {comparison.frontend_routes.length > 0 ? (
                  comparison.frontend_routes.map((route, i) => {
                    const isUnmatched = comparison.unmatched_frontend_routes.includes(route);
                    return (
                      <motion.div
                        key={route}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.2, delay: i * 0.05 }}
                        className="flex items-center justify-between font-mono text-[12px] py-1.5 px-2 rounded-baton hover:bg-baton-layer-1/50 transition-colors"
                      >
                        <span className={isUnmatched ? 'text-baton-text-highlight' : 'text-baton-text-highlight'}>
                          {route}
                        </span>
                        <span className={isUnmatched ? 'text-baton-warning' : 'text-baton-accent'}>
                          {isUnmatched ? 'UNMATCHED' : 'MATCH'}
                        </span>
                      </motion.div>
                    );
                  })
                ) : (
                  <span className="font-mono text-[11px] text-baton-text-tertiary">NO API CALLS DETECTED</span>
                )}
              </div>
            </Panel>

            {/* Backend routes */}
            <Panel label="BACKEND BRANCH — ROUTES">
              <div className="p-4 space-y-1.5">
                {comparison.backend_routes.length > 0 ? (
                  comparison.backend_routes.map((route, i) => {
                    const isUnmatched = comparison.unmatched_backend_routes.includes(route);
                    return (
                      <motion.div
                        key={route}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.2, delay: i * 0.05 }}
                        className="flex items-center justify-between font-mono text-[12px] py-1.5 px-2 rounded-baton hover:bg-baton-layer-1/50 transition-colors"
                      >
                        <span className="text-baton-text-highlight">{route}</span>
                        <span className={isUnmatched ? 'text-baton-warning' : 'text-baton-accent'}>
                          {isUnmatched ? 'UNMATCHED' : 'MATCH'}
                        </span>
                      </motion.div>
                    );
                  })
                ) : (
                  <span className="font-mono text-[11px] text-baton-text-tertiary">NO ROUTES DETECTED</span>
                )}
              </div>
            </Panel>
          </div>

          {/* Unmatched summary */}
          {(comparison.unmatched_frontend_routes.length > 0 || comparison.unmatched_backend_routes.length > 0) && (
            <div className="border border-baton-warning/30 bg-baton-near-black rounded-baton p-5">
              <MonoLabel variant="warning" className="mb-3 block">UNMATCHED ENDPOINTS</MonoLabel>
              <div className="space-y-2">
                {comparison.unmatched_frontend_routes.map((route) => (
                  <div key={`fe-${route}`} className="flex items-center gap-3 font-mono text-[12px]">
                    <span className="text-baton-text-tertiary">FRONTEND</span>
                    <ArrowRight size={11} className="text-baton-text-tertiary" />
                    <span className="text-baton-warning">{route}</span>
                    <span className="text-baton-text-tertiary text-[10px]">— no matching backend route</span>
                  </div>
                ))}
                {comparison.unmatched_backend_routes.map((route) => (
                  <div key={`be-${route}`} className="flex items-center gap-3 font-mono text-[12px]">
                    <span className="text-baton-text-tertiary">BACKEND</span>
                    <ArrowRight size={11} className="text-baton-text-tertiary" />
                    <span className="text-baton-warning">{route}</span>
                    <span className="text-baton-text-tertiary text-[10px]">— not called by frontend</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-baton-text-tertiary mt-4 pt-3 border-t border-baton-border">
                This is a route-level comparison, not full type compatibility. Check contracts for request/response shape details.
              </p>
            </div>
          )}
        </>
      )}

      {/* Idle */}
      {intState === 'idle' && (
        <Panel>
          <div className="p-12 text-center">
            <GitMerge size={32} className="mx-auto text-baton-text-tertiary mb-4" />
            <p className="text-sm text-baton-text-tertiary mb-1">NO INTEGRATION CHECK PERFORMED</p>
            <p className="text-xs text-baton-text-tertiary">Enter frontend and backend branches, then click CHECK INTEGRATION.</p>
          </div>
        </Panel>
      )}
    </div>
  );
}
