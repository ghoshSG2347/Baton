import { ErrorStatus, StatusPanel } from '@/components/ui/StatusPanel';
import { motion } from 'framer-motion';
import { useState, useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import type { AnalysisResult } from '@/types';
import { batonApi } from '@/lib/api/batonApi';
import { DEMO_ANALYSIS } from '@/lib/demo';
import { Button, MonoLabel, Panel, SectionLabel, TelemetryLine } from '@/components/ui/primitives';
import { formatTimestamp, shortSha, formatNumber } from '@/lib/utils';

type AnalysisState = 'idle' | 'loading' | 'success' | 'partial' | 'error';

export function Analysis({ state }: { state: WorkspaceStateHook }) {
  const [analysisState, setAnalysisState] = useState<AnalysisState>('idle');
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(state.isDemoMode ? DEMO_ANALYSIS : null);
  const [error, setError] = useState<Error | null>(null);
  const [folderInput, setFolderInput] = useState(state.selectedFolder || '');

  const epoch = useRef(0);
  const selectedIdentity = `${state.repo?.owner}/${state.repo?.repository}:${state.selectedBranch || state.repo?.default_branch || ''}:${state.selectedFolder}`;
  useEffect(() => {
    epoch.current++; setAnalysis(state.isDemoMode ? DEMO_ANALYSIS : null); setAnalysisState('idle'); setError(null); setFolderInput(state.selectedFolder);
    // Cancel pending analysis responses when this view or identity changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    return () => { epoch.current++; };
  }, [selectedIdentity, state.selectedFolder, state.isDemoMode]);
  const hasRepo = state.repo || state.isDemoMode;

  const handleAnalyze = async () => {
    if (!hasRepo || analysisState === 'loading') return;
    const current = ++epoch.current;
    setAnalysisState('loading');
    setError(null);

    if (state.isDemoMode) {
      setTimeout(() => {
        if (current !== epoch.current) return;
        setAnalysis(DEMO_ANALYSIS);
        setAnalysisState(DEMO_ANALYSIS.analysis_warnings.length > 0 ? 'partial' : 'success');
      }, 1500);
      return;
    }

    try {
      if (!state.repo) return;
      const folder = folderInput || state.selectedFolder || '';
      const result = folder
        ? await batonApi.analyzeFolder(state.repo.owner, state.repo.repository, state.selectedBranch || state.repo.default_branch || '', folder, state.githubToken || undefined)
        : await batonApi.analyzeRepository(state.repo.owner, state.repo.repository, state.selectedBranch || state.repo.default_branch || '', state.githubToken || undefined);
      if (current !== epoch.current) return;
      setAnalysis(result);
      state.markAnalysisComplete();
      setAnalysisState(result.analysis_warnings.length > 0 || result.metadata.skipped_files.length > 0 ? 'partial' : 'success');
    } catch (err) {
      if (current !== epoch.current) return;
      setAnalysisState('error');
      setError(err instanceof Error ? err : new Error('Analysis failed'));
    }
  };

  if (!hasRepo) {
    return (
      <div className="p-6 lg:p-8">
        <SectionLabel className="mb-6">ANALYSIS</SectionLabel>
        <Panel>
          <div className="p-12 text-center">
            <p className="text-sm text-baton-text-tertiary mb-2">NO REPOSITORY CONNECTED</p>
            <p className="text-xs text-baton-text-tertiary">Connect a GitHub repository to begin analysis.</p>
          </div>
        </Panel>
      </div>
    );
  }

  const sections: { label: string; items: string[]; empty: string }[] = analysis ? [
    { label: 'STACK', items: analysis.stack.detected, empty: 'NOT DETECTED' },
    { label: 'LANGUAGES', items: analysis.stack.languages, empty: 'NOT DETECTED' },
    { label: 'IMPORTANT FILES', items: analysis.important_files, empty: 'NONE DETECTED' },
    { label: 'ROUTES', items: analysis.routes, empty: 'NONE DETECTED' },
    { label: 'API CALLS', items: analysis.api_calls, empty: 'NONE DETECTED' },
    { label: 'TYPES', items: analysis.types, empty: 'NONE DETECTED' },
    { label: 'MOCK DATA', items: analysis.mock_data, empty: 'NONE DETECTED' },
    { label: 'ENVIRONMENT VARIABLES', items: analysis.environment_variables, empty: 'NONE DETECTED' },
    { label: 'SHARED FILES', items: analysis.shared_files, empty: 'NONE DETECTED' },
    { label: 'STRAY FILES', items: analysis.stray_files, empty: 'NONE DETECTED' },
  ] : [];

  return (
    <div className="p-6 lg:p-8 max-w-6xl">
      <SectionLabel className="mb-6">ANALYSIS</SectionLabel>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Analysis</h1>
      <p className="text-sm text-baton-text-tertiary mb-8">Deterministic inspection of repository structure, routes, types, and contracts.</p>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-6">
        <div className="flex items-center gap-2 border border-baton-border bg-baton-near-black rounded-baton px-3 py-2 flex-1 max-w-md">
          <MonoLabel>FOLDER</MonoLabel>
          <input
            type="text"
            value={folderInput}
            onChange={(e) => setFolderInput(e.target.value)}
            placeholder="/frontend"
            className="flex-1 bg-transparent text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none font-mono"
          />
        </div>
        <Button variant="primary" onClick={handleAnalyze} disabled={analysisState === 'loading'}>
          {analysisState === 'loading' ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              ANALYZING...
            </>
          ) : analysis ? 'RE-ANALYZE' : 'ANALYZE PROJECT'}
        </Button>
      </div>

      {/* Loading state */}
      {analysisState === 'loading' && (
        <Panel>
          <div className="p-8">
            <div className="flex items-center gap-3 mb-4">
              <Loader2 size={16} className="animate-spin text-baton-accent" />
              <MonoLabel variant="accent">ANALYZING REPOSITORY</MonoLabel>
            </div>
            <TelemetryLine active className="mb-4" />
            <div className="font-mono text-[11px] text-baton-text-tertiary space-y-1">
              <div>Reading file tree...</div>
              <div>Detecting stack and languages...</div>
              <div>Extracting routes and API calls...</div>
              <div>Scanning for types and mock data...</div>
            </div>
          </div>
        </Panel>
      )}

      {/* Error state */}
      {analysisState === 'error' && (
        <ErrorStatus error={error} operation="analysis" primaryAction={<Button variant="secondary" onClick={handleAnalyze}>Retry analysis</Button>} />
      )}

      {/* Results */}
      {analysis && analysisState !== 'loading' && analysisState !== 'error' && (
        <>
          {/* Metadata */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-baton-border mb-6">
            <div className="bg-baton-near-black p-4">
              <MonoLabel>BRANCH</MonoLabel>
              <div className="font-mono text-sm text-baton-text-highlight mt-1">{analysis.metadata.branch || 'Branch unavailable'}</div>
            </div>
            <div className="bg-baton-near-black p-4">
              <MonoLabel>COMMIT</MonoLabel>
              <div className="font-mono text-sm text-baton-text-highlight mt-1">{analysis.metadata.commit ? shortSha(analysis.metadata.commit) : 'Commit unavailable'}</div>
            </div>
            <div className="bg-baton-near-black p-4">
              <MonoLabel>GENERATED</MonoLabel>
              <div className="font-mono text-sm text-baton-text-highlight mt-1">{formatTimestamp(analysis.metadata.generated)}</div>
            </div>
            <div className="bg-baton-near-black p-4">
              <MonoLabel>FILES ANALYZED</MonoLabel>
              <div className="font-mono text-sm text-baton-text-highlight mt-1">{formatNumber(analysis.metadata.files_analyzed)}</div>
            </div>
          </div>

          {/* Partial warning */}
          {analysisState === 'partial' && <StatusPanel severity="warning" title="Analysis completed with limited coverage" explanation={`${analysis.metadata.skipped_files.length} source files were omitted. Review the recorded warnings and omitted paths before relying on an absent feature.`} technicalDetails={[...analysis.analysis_warnings, ...analysis.metadata.skipped_files].join('\n')} />}

          {/* Analysis sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {sections.map((section, i) => (
              <motion.div
                key={section.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
              >
                <Panel label={section.label}>
                  <div className="p-4">
                    {section.items.length > 0 ? (
                      <div className="space-y-1">
                        {section.items.map((item, j) => (
                          <div key={j} className="font-mono text-[11px] text-baton-text-highlight">
                            {item}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="font-mono text-[11px] text-baton-text-tertiary">{section.empty}</span>
                    )}
                  </div>
                </Panel>
              </motion.div>
            ))}
          </div>

          {/* Handoffs */}
          {analysis.handoffs.length > 0 && (
            <div className="mt-6">
              <Panel label="HANDOFFS">
                <div className="p-4 space-y-3">
                  {analysis.handoffs.map((handoff, i) => (
                    <div key={i}>
                      <div className="font-mono text-[11px] text-baton-accent mb-1">{handoff.path}</div>
                      {handoff.items.map((item, j) => (
                        <div key={j} className="font-mono text-[11px] text-baton-text-secondary pl-3">
                          {item}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </Panel>
            </div>
          )}

          {/* File tree */}
          {analysis.file_tree.length > 0 && (
            <div className="mt-6">
              <Panel label={`FILE TREE — ${analysis.file_tree.length} FILES`}>
                <div className="p-4 max-h-64 overflow-y-auto">
                  <div className="space-y-0.5">
                    {analysis.file_tree.map((file, i) => (
                      <div key={i} className="font-mono text-[11px] text-baton-text-secondary">
                        {file.path}
                      </div>
                    ))}
                  </div>
                </div>
              </Panel>
            </div>
          )}
        </>
      )}

      {/* Idle state */}
      {!analysis && analysisState === 'idle' && (
        <Panel>
          <div className="p-12 text-center">
            <p className="text-sm text-baton-text-tertiary mb-1">NO ANALYSIS YET</p>
            <p className="text-xs text-baton-text-tertiary">Click ANALYZE PROJECT to inspect the repository.</p>
          </div>
        </Panel>
      )}
    </div>
  );
}
