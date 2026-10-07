import { useEffect, useState } from 'react';
import { batonApi, BatonApiError } from '@/lib/api/batonApi';
import { snapshotState } from '@/lib/workspaceStatus';
import { ErrorStatus } from '@/components/ui/StatusPanel';
import type { WorkspaceInspection } from '@/types';
import { motion } from 'framer-motion';
import { GitBranch, FileCode, Database, Activity } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import { StatusIndicator, MonoLabel, Panel, SectionLabel, TelemetryLine } from '@/components/ui/primitives';
import { DEMO_ACTIVITIES } from '@/lib/demo';
import { cn } from '@/lib/utils';

interface OverviewProps {
  state: WorkspaceStateHook;
  onConnectRepo: () => void;
}

export function Overview({ state, onConnectRepo }: OverviewProps) {
  const [inspection, setInspection] = useState<WorkspaceInspection | null>(null);
  const [error, setError] = useState<Error | null>(null);
  useEffect(() => {
    let active = true;
    setInspection(null); setError(null);
    if (state.repo && !state.isDemoMode) {
      batonApi.inspectWorkspace({ owner: state.repo.owner, repo: state.repo.repository, branch: state.selectedBranch || 'main', folder: state.selectedFolder, context_type: 'project', constraints: [] }, state.githubToken || undefined)
        .then((result) => { if (active) setInspection(result); })
        .catch((cause) => { if (active) setError(cause instanceof Error ? cause : new Error('Overview could not be loaded.')); });
    }
    return () => { active = false; };
  }, [state.repo, state.isDemoMode, state.selectedBranch, state.selectedFolder, state.githubToken, state.batonAccessKey, state.geminiKey, state.geminiModel, state.analysisRevision]);
  const status = inspection && state.repo ? snapshotState(inspection, { owner: state.repo.owner, repo: state.repo.repository, branch: state.selectedBranch || 'main', folder: state.selectedFolder, context_type: 'project', constraints: [] }) : 'CHECKING';
  const activities = state.isDemoMode ? DEMO_ACTIVITIES : inspection?.identity.analysis_timestamp ? [{ time: new Date(inspection.identity.analysis_timestamp).toLocaleTimeString(), type: 'info', event: `Snapshot ${inspection.identity.commit.slice(0, 12)} analyzed. ${inspection.completeness.files_omitted} files omitted.` }] : [];
  const hasRepo = state.repo || state.isDemoMode;

  if (!hasRepo) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-3.5rem)] p-6">
        <div className="text-center max-w-md">
          <div className="relative mb-8">
            <TelemetryLine className="w-32 mx-auto" active />
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-2">MISSION CONTROL STANDBY</h2>
          <p className="text-sm text-baton-text-tertiary mb-8">
            No repository connected. Connect a GitHub repository to begin.
          </p>
          <button
            onClick={onConnectRepo}
            className="inline-flex items-center gap-2 bg-baton-accent text-baton-black rounded-full px-6 py-2.5 text-sm font-medium hover:brightness-110 transition-all"
          >
            <GitBranch size={15} />
            CONNECT REPOSITORY
          </button>
        </div>
      </div>
    );
  }

  const confirmed = !error && (state.isDemoMode || !!inspection);
  const backend = state.isDemoMode ? 'DEMO' : error instanceof BatonApiError && error.status === 0 ? 'UNREACHABLE' : inspection || (error instanceof BatonApiError && error.status > 0) ? 'RESPONDED' : 'CHECKING';
  const stats = [
    { label: 'REPOSITORY', value: state.repo ? `${state.repo.owner}/${state.repo.repository}` : 'baton/demo-project', status: confirmed ? 'connected' as const : null, icon: GitBranch },
    { label: 'BRANCH', value: state.selectedBranch || 'main', status: confirmed ? 'connected' as const : null, icon: GitBranch },
    { label: 'BACKEND', value: backend, status: null, icon: Activity },
    { label: 'ANALYSIS', value: state.isDemoMode ? 'DEMO' : error ? 'REQUEST FAILED' : status, status: null, icon: Activity },
    { label: 'FILES', value: state.isDemoMode ? '84 (DEMO)' : inspection?.available ? String(inspection.completeness.files_analyzed) : 'Unknown', status: null, icon: FileCode },
    { label: 'CONTEXT', value: state.isDemoMode ? '3.2K (DEMO)' : inspection?.estimated_tokens !== undefined ? `${inspection.estimated_tokens} EST. TOKENS` : 'Unknown', status: null, icon: Database },
  ];

  return (
    <div className="p-6 lg:p-8 max-w-6xl">
      <SectionLabel className="mb-6">MISSION CONTROL</SectionLabel>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Overview</h1>
      <p className="text-sm text-baton-text-tertiary mb-8">{confirmed ? 'Current repository observations.' : 'Repository identity remembered. Checking current access and analysis separately.'}</p>

      {error && <ErrorStatus error={error} operation="inspect" />}
      {/* Status rail */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-px bg-baton-border mb-8">
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              className="bg-baton-near-black p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <MonoLabel>{stat.label}</MonoLabel>
                <Icon size={12} className="text-baton-text-tertiary" />
              </div>
              <div className="font-mono text-sm text-baton-text-highlight truncate">{stat.value}</div>
              {stat.status && <StatusIndicator status={stat.status} className="mt-2" />}
            </motion.div>
          );
        })}
      </div>

      {/* Project state visual */}
      <Panel label="PROJECT STATE" className="mb-8">
        <div className="p-8">
          <div className="flex items-center justify-center gap-12">
            {(state.isDemoMode ? ['Frontend', 'Backend', 'Shared'] : ['Repository', state.selectedBranch || 'main', status]).map((node, i) => (
              <div key={node} className="relative flex flex-col items-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.3, delay: i * 0.1 }}
                  className="w-24 h-24 border border-baton-border bg-baton-black rounded-baton flex items-center justify-center"
                >
                  <span className="text-sm font-semibold tracking-tight">{node}</span>
                </motion.div>
                {i < 2 && (
                  <div className="absolute top-1/2 left-full w-12 h-px bg-baton-accent/40">
                    <motion.div
                      className="absolute h-full bg-baton-accent w-8"
                      animate={{ x: ['-100%', '100%'] }}
                      transition={{ duration: 2, repeat: Infinity, ease: 'linear', delay: i * 0.5 }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </Panel>

      {inspection && <Panel label="SNAPSHOT IDENTITY" className="mb-8"><div className="p-4 font-mono text-xs break-all">Snapshot commit: {inspection.identity.commit || 'Not analyzed'}<br />Current HEAD: {inspection.identity.current_head || 'Unknown'}<br />Coverage: {inspection.completeness.status}; omitted: {inspection.completeness.files_omitted}</div></Panel>}
      {/* Recent activity */}
      <Panel label="RECENT ACTIVITY">
        <div className="divide-y divide-baton-border">
          {!activities.length && <p className="p-4 text-sm text-baton-text-tertiary">No analyzed snapshot activity available.</p>}
          {activities.map((activity, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2, delay: i * 0.05 }}
              className="flex items-center gap-4 px-4 py-3"
            >
              <span className="font-mono text-[11px] text-baton-text-tertiary w-12">{activity.time}</span>
              <div className={cn(
                'w-1.5 h-1.5 rounded-full',
                activity.type === 'success' ? 'bg-baton-accent'
                : activity.type === 'warning' ? 'bg-baton-warning'
                : 'bg-baton-text-tertiary'
              )} />
              <span className="text-sm text-baton-text-secondary">{activity.event}</span>
            </motion.div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
