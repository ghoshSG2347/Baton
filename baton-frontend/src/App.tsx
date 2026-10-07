import { motion, AnimatePresence, MotionConfig, useReducedMotion } from 'framer-motion';
import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import { LandingPage } from '@/components/landing/LandingPage';
import { WorkspaceShell } from '@/components/workspace/WorkspaceShell';
import { CustomCursor } from '@/components/ui/CustomCursor';
import { useWorkspaceState } from '@/hooks/useWorkspaceState';
import { Overview } from '@/components/workspace/sections/Overview';
import { Repository } from '@/components/workspace/sections/Repository';
import { Team } from '@/components/workspace/sections/Team';
import { Analysis } from '@/components/workspace/sections/Analysis';
import { ContextBuilder } from '@/components/workspace/sections/ContextBuilder';
import { PromptBuilder } from '@/components/workspace/sections/PromptBuilder';
import { ConflictRadar } from '@/components/workspace/sections/ConflictRadar';
import { Integration } from '@/components/workspace/sections/Integration';
const AIWorkspace = lazy(() => import('@/components/workspace/sections/AIWorkspace').then((module) => ({ default: module.AIWorkspace })));
import type { WorkspaceSection } from '@/types';

type Page = 'landing' | 'workspace';

export default function App() {
  const [page, setPage] = useState<Page>('landing');
  const [showWorkspaceIntro, setShowWorkspaceIntro] = useState(false);
  const state = useWorkspaceState();
  const reducedMotion = useReducedMotion();

  const handleEnterWorkspace = useCallback(() => {
    if (reducedMotion) { setPage('workspace'); return; }
    setShowWorkspaceIntro(true);
  }, [reducedMotion]);
  useEffect(() => {
    if (!showWorkspaceIntro) return;
    const timer = window.setTimeout(() => { setPage('workspace'); setShowWorkspaceIntro(false); }, 400);
    return () => window.clearTimeout(timer);
  }, [showWorkspaceIntro]);

  const handleConnectRepo = () => {
    state.setActiveSection('repository');
  };

  const renderSection = (section: WorkspaceSection) => {
    switch (section) {
      case 'ai':
        return null;
      case 'overview':
        return <Overview state={state} onConnectRepo={handleConnectRepo} />;
      case 'repository':
        return null;
      case 'team':
        return <Team state={state} />;
      case 'analysis':
        return <Analysis state={state} />;
      case 'context':
        return <ContextBuilder state={state} />;
      case 'prompt':
        return <PromptBuilder state={state} />;
      case 'conflicts':
        return <ConflictRadar state={state} />;
      case 'integration':
        return <Integration state={state} />;
      default:
        return <Overview state={state} onConnectRepo={handleConnectRepo} />;
    }
  };

  return (
    <MotionConfig reducedMotion="user">
      {page === 'landing' && <CustomCursor />}

      <AnimatePresence mode="wait">
        {page === 'landing' && (
          <motion.div
            key="landing"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <LandingPage onEnterWorkspace={handleEnterWorkspace} />
          </motion.div>
        )}

        {page === 'workspace' && (
          <motion.div
            key="workspace"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <WorkspaceShell key={state.resetVersion} state={state} onBackToLanding={() => setPage('landing')}>
              {(state.activeSection === 'repository' || (state.repo && !state.isDemoMode && !state.githubToken)) && <Repository state={state} />}
              {(!state.repo || state.isDemoMode || state.githubToken) && <>
              <div className="h-full" hidden={state.activeSection !== 'ai'}><Suspense fallback={<div role="status" className="h-full grid place-items-center text-baton-text-tertiary text-sm">Loading workspace…</div>}><AIWorkspace key={`${state.repo?.owner}/${state.repo?.repository}`} state={state} /></Suspense></div>
              {renderSection(state.activeSection)}
              </>}
            </WorkspaceShell>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Transition overlay */}
      {showWorkspaceIntro && (
        <motion.div
          className="fixed inset-0 z-[10001] bg-baton-black pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
        >
          <motion.div
            className="absolute top-0 left-0 right-0 h-0.5 bg-baton-accent"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            style={{ transformOrigin: 'left' }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.2, delay: 0.1 }}
              className="text-center"
            >
              <div className="flex items-center justify-center gap-2 mb-3">
                <div className="w-1 h-4 bg-baton-accent" />
                <div className="w-1 h-4 bg-baton-white/40" />
                <div className="w-1 h-4 bg-baton-white/20" />
              </div>
              <span className="font-mono text-[10px] tracking-[0.3em] text-baton-text-tertiary uppercase">
                ENTERING MISSION CONTROL
              </span>
            </motion.div>
          </div>
        </motion.div>
      )}
    </MotionConfig>
  );
}
