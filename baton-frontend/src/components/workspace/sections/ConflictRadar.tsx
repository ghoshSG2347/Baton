import { motion } from 'framer-motion';
import { useState } from 'react';
import { Loader2, Radar, AlertTriangle, GitBranch } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import type { ConflictResult } from '@/types';
import { batonApi } from '@/lib/api/batonApi';
import { DEMO_CONFLICTS } from '@/lib/demo';
import { Button, MonoLabel, Panel, SectionLabel, StatusIndicator, TelemetryLine } from '@/components/ui/primitives';
import { cn } from '@/lib/utils';

type ConflictState = 'idle' | 'loading' | 'success' | 'error';

const DEMO_LANE_FILES: Record<string, string[]> = {
  'member/alex-ui': ['src/App.tsx', 'src/components/Header.tsx', 'src/api/client.ts'],
  'member/sam-api': ['backend/app/main.py', 'backend/app/api/routes/auth.py', 'src/api/client.ts'],
};

export function ConflictRadar({ state }: { state: WorkspaceStateHook }) {
  const [conflictState, setConflictState] = useState<ConflictState>('idle');
  const [result, setResult] = useState<ConflictResult | null>(null);
  const [error, setError] = useState('');
  const [branchesInput, setBranchesInput] = useState(
    state.isDemoMode
      ? 'member/alex-ui\nmember/sam-api'
      : ''
  );

  const hasRepo = state.repo || state.isDemoMode;

  const handleDetect = async () => {
    const branchNames = branchesInput.split('\n').map((b) => b.trim()).filter(Boolean);
    if (branchNames.length < 2) return;
    setConflictState('loading');
    setError('');

    if (state.isDemoMode) {
      setTimeout(() => {
        setResult(DEMO_CONFLICTS);
        setConflictState('success');
      }, 1200);
      return;
    }

    try {
      const branchFiles: Record<string, string[]> = {};
      for (const branchName of branchNames) {
        if (state.repo) {
          try {
            const tree = await batonApi.getTree(state.repo.owner, state.repo.repository, branchName, '', state.githubToken || undefined);
            branchFiles[branchName] = tree.filter((t) => t.type === 'blob').map((t) => t.path);
          } catch {
            branchFiles[branchName] = [];
          }
        }
      }
      const res = await batonApi.detectConflicts(branchFiles, [], state.githubToken || undefined);
      setResult(res);
      setConflictState('success');
    } catch (err) {
      setConflictState('error');
      setError(err instanceof Error ? err.message : 'Conflict detection failed');
    }
  };

  if (!hasRepo) {
    return (
      <div className="p-6 lg:p-8">
        <SectionLabel className="mb-6">CONFLICT RADAR</SectionLabel>
        <Panel>
          <div className="p-12 text-center">
            <p className="text-sm text-baton-text-tertiary mb-2">NO REPOSITORY CONNECTED</p>
            <p className="text-xs text-baton-text-tertiary">Connect a repository to scan for conflicts.</p>
          </div>
        </Panel>
      </div>
    );
  }

  const branchNames = branchesInput.split('\n').map((b) => b.trim()).filter(Boolean);
  const laneFiles = state.isDemoMode ? DEMO_LANE_FILES : {};

  return (
    <div className="p-6 lg:p-8 max-w-6xl">
      <SectionLabel className="mb-6">CONFLICT RADAR</SectionLabel>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Conflict Radar</h1>
      <p className="text-sm text-baton-text-tertiary mb-8">
        Detect shared-file coordination overlap across branches. Not a Git merge engine — a coordination signal.
      </p>

      {/* Input */}
      <div className="flex flex-col sm:flex-row items-start sm:items-end gap-3 mb-6">
        <div className="flex-1 max-w-md">
          <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
            Branches (one per line)
          </label>
          <textarea
            value={branchesInput}
            onChange={(e) => setBranchesInput(e.target.value)}
            placeholder={'member/alex-ui\nmember/sam-api'}
            rows={3}
            className="w-full border border-baton-border bg-baton-near-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono text-[12px] resize-none"
          />
        </div>
        <Button variant="primary" onClick={handleDetect} disabled={conflictState === 'loading' || branchNames.length < 2}>
          {conflictState === 'loading' ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              SCANNING...
            </>
          ) : 'SCAN FOR CONFLICTS'}
        </Button>
      </div>

      {/* Loading */}
      {conflictState === 'loading' && (
        <Panel>
          <div className="p-8">
            <div className="flex items-center gap-3 mb-4">
              <Radar size={16} className="text-baton-accent animate-pulse" />
              <MonoLabel variant="accent">SCANNING BRANCHES</MonoLabel>
            </div>
            <TelemetryLine active />
          </div>
        </Panel>
      )}

      {/* Error */}
      {conflictState === 'error' && (
        <Panel>
          <div className="p-8 text-center">
            <AlertTriangle size={24} className="mx-auto text-baton-warning mb-3" />
            <p className="text-sm text-baton-warning mb-2">SCAN FAILED</p>
            <p className="text-xs text-baton-text-tertiary mb-4">{error}</p>
            <Button variant="secondary" onClick={handleDetect}>RETRY</Button>
          </div>
        </Panel>
      )}

      {/* Results — branch lanes visualization */}
      {conflictState === 'success' && result && (
        <>
          {/* Status bar */}
          <div
            className={cn(
              'border rounded-baton p-4 mb-6 flex items-center justify-between',
              result.conflict_count > 0
                ? 'border-baton-warning/30 bg-baton-near-black'
                : 'border-baton-accent/30 bg-baton-near-black'
            )}
          >
            <div className="flex items-center gap-3">
              <StatusIndicator status={result.conflict_count > 0 ? 'attention' : 'connected'} />
              <MonoLabel variant={result.conflict_count > 0 ? 'warning' : 'accent'}>
                {result.conflict_count > 0
                  ? `${result.conflict_count} POSSIBLE SHARED-FILE CONFLICT${result.conflict_count > 1 ? 'S' : ''}`
                  : 'NO CONFLICTS DETECTED'}
              </MonoLabel>
            </div>
            <span className="font-mono text-[11px] text-baton-text-tertiary">
              {branchNames.length} branches scanned
            </span>
          </div>

          {/* Branch lanes */}
          <Panel label="BRANCH LANES">
            <div className="p-6">
              {branchNames.map((branchName) => (
                <div key={branchName} className="mb-6 last:mb-0">
                  <div className="flex items-center gap-2 mb-3">
                    <GitBranch size={13} className="text-baton-text-tertiary" />
                    <span className="font-mono text-[12px] text-baton-text-highlight">{branchName}</span>
                  </div>
                  <div className="ml-6 flex items-center gap-2 flex-wrap">
                    {(laneFiles[branchName] || []).map((file) => {
                      const isConflict = result.conflicts.some((c) => c.path === file && c.branches.includes(branchName));
                      return (
                        <motion.div
                          key={file}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.2 }}
                          className={cn(
                            'font-mono text-[10px] px-2.5 py-1 rounded-baton border',
                            isConflict
                              ? 'border-baton-warning/40 text-baton-warning bg-baton-black'
                              : 'border-baton-border text-baton-text-secondary bg-baton-black'
                          )}
                        >
                          {file}
                        </motion.div>
                      );
                    })}
                    {(!laneFiles[branchName] || laneFiles[branchName].length === 0) && (
                      <span className="font-mono text-[10px] text-baton-text-tertiary">No files detected</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          {/* Conflict details */}
          {result.conflicts.length > 0 && (
            <div className="mt-6 space-y-3">
              {result.conflicts.map((conflict, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.1 }}
                  className="border border-baton-warning/30 bg-baton-near-black rounded-baton p-5"
                >
                  <div className="flex items-start gap-4">
                    <motion.div
                      className="w-2 h-2 rounded-full bg-baton-warning flex-shrink-0 mt-1.5"
                      animate={{ opacity: [1, 0.3, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                    <div className="flex-1">
                      <MonoLabel variant="warning" className="mb-2 block">
                        POSSIBLE SHARED-FILE CONFLICT
                      </MonoLabel>
                      <div className="font-mono text-[13px] text-baton-text-highlight mb-2">
                        {conflict.path}
                      </div>
                      <div className="flex items-center gap-2 mb-3">
                        {conflict.branches.map((b) => (
                          <span key={b} className="font-mono text-[10px] text-baton-text-tertiary border border-baton-border px-2 py-0.5 rounded-baton">
                            {b}
                          </span>
                        ))}
                      </div>
                      <p className="text-sm text-baton-text-tertiary">{conflict.reason}</p>
                      <p className="text-xs text-baton-text-tertiary mt-2">
                        Both branches are touching this file. Talk before you push further.
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Idle */}
      {conflictState === 'idle' && (
        <Panel>
          <div className="p-12 text-center">
            <Radar size={32} className="mx-auto text-baton-text-tertiary mb-4" />
            <p className="text-sm text-baton-text-tertiary mb-1">NO SCAN PERFORMED</p>
            <p className="text-xs text-baton-text-tertiary">Enter branch names and click SCAN FOR CONFLICTS.</p>
          </div>
        </Panel>
      )}
    </div>
  );
}
