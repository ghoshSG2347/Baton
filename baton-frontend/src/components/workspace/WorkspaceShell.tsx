import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import {
  Activity, GitBranch, Users, BarChart3, FileText, Terminal,
  Radar, GitMerge, RefreshCw, Settings, Menu, X, LogOut,
} from 'lucide-react';
import type { WorkspaceSection } from '@/types';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import { cn } from '@/lib/utils';
import { StatusIndicator, MonoLabel } from '@/components/ui/primitives';

interface WorkspaceShellProps {
  state: WorkspaceStateHook;
  children: React.ReactNode;
  onBackToLanding: () => void;
}

const navSections: {
  group: string;
  items: { id: WorkspaceSection; label: string; icon: typeof Activity }[];
}[] = [
  {
    group: 'MISSION CONTROL',
    items: [
      { id: 'overview', label: 'Overview', icon: Activity },
      { id: 'repository', label: 'Repository', icon: GitBranch },
      { id: 'team', label: 'Team & Ownership', icon: Users },
      { id: 'analysis', label: 'Analysis', icon: BarChart3 },
    ],
  },
  {
    group: 'CONTEXT',
    items: [
      { id: 'context', label: 'Context Builder', icon: FileText },
      { id: 'prompt', label: 'Prompt Builder', icon: Terminal },
    ],
  },
  {
    group: 'COORDINATION',
    items: [
      { id: 'conflicts', label: 'Conflict Radar', icon: Radar },
      { id: 'integration', label: 'Integration', icon: GitMerge },
    ],
  },
];

export function WorkspaceShell({ state, children, onBackToLanding }: WorkspaceShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [demoMenuOpen, setDemoMenuOpen] = useState(false);
  const [clearDemoOpen, setClearDemoOpen] = useState(false);
  const repoName = state.repo ? `${state.repo.owner}/${state.repo.repository}` : 'No repository';

  useEffect(() => {
    if (!clearDemoOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setClearDemoOpen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [clearDemoOpen]);

  return (
    <div className="min-h-screen bg-baton-black text-baton-white flex flex-col">
      {/* Top bar */}
      <header className="flex-shrink-0 h-14 border-b border-baton-border bg-baton-near-black flex items-center justify-between px-4 lg:px-6 z-30 relative">
        {/* Left: logo + repo info */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden text-baton-text-secondary hover:text-baton-white"
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <button
            type="button"
            onClick={onBackToLanding}
            aria-label="Return to Baton landing page"
            className="flex items-center gap-2 text-baton-white hover:text-baton-accent transition-colors"
          >
            <div className="flex items-center gap-1">
              <div className="w-1 h-3.5 bg-baton-accent" />
              <div className="w-1 h-3.5 bg-baton-white/40" />
              <div className="w-1 h-3.5 bg-baton-white/20" />
            </div>
            <span className="text-sm font-bold tracking-tight">BATON</span>
          </button>
          {state.isDemoMode && (
            <div className="relative">
              <button
                type="button"
                onClick={() => setDemoMenuOpen((open) => !open)}
                aria-expanded={demoMenuOpen}
                aria-label="Open demo workspace actions"
                className="font-mono text-[9px] tracking-wider text-baton-accent border border-baton-accent/30 hover:border-baton-accent px-2 py-0.5 rounded-baton uppercase transition-colors"
              >
                Demo Data
              </button>
              {demoMenuOpen && (
                <div className="absolute left-0 top-7 z-40 w-56 border border-baton-border bg-baton-near-black rounded-baton p-3 shadow-2xl">
                  <MonoLabel className="block mb-2">DEMO WORKSPACE</MonoLabel>
                  <p className="text-[11px] leading-relaxed text-baton-text-tertiary mb-3">
                    Demo repository and team data are currently loaded.
                  </p>
                  <button
                    type="button"
                    onClick={() => setClearDemoOpen(true)}
                    className="w-full text-left font-mono text-[10px] tracking-wider text-baton-warning hover:text-baton-white transition-colors uppercase"
                  >
                    Clear Demo Data
                  </button>
                </div>
              )}
              {clearDemoOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setClearDemoOpen(false)}>
                  <div
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="clear-demo-title"
                    className="w-full max-w-sm border border-baton-border bg-baton-near-black rounded-baton p-5"
                    onClick={(event) => event.stopPropagation()}
                  >
                    <MonoLabel variant="warning" className="block mb-2">CLEAR DEMO WORKSPACE?</MonoLabel>
                    <h2 id="clear-demo-title" className="text-lg font-semibold mb-2">Return to empty state</h2>
                    <p className="text-sm leading-relaxed text-baton-text-tertiary mb-5">
                      This removes the loaded repository, team, analysis, context, and coordination data from this browser.
                    </p>
                    <div className="flex justify-end gap-3">
                      <button
                        type="button"
                        onClick={() => setClearDemoOpen(false)}
                        className="rounded-full px-4 py-2 text-xs text-baton-text-secondary hover:text-baton-white transition-colors"
                      >
                        CANCEL
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          state.reset();
                          setClearDemoOpen(false);
                          setDemoMenuOpen(false);
                        }}
                        className="rounded-full bg-baton-warning px-4 py-2 text-xs font-medium text-white hover:brightness-110 transition-colors"
                      >
                        CLEAR DEMO DATA
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Center: repository info */}
        <div className="hidden md:flex items-center gap-4">
          <div className="flex items-center gap-2">
            <GitBranch size={13} className="text-baton-text-tertiary" />
            <span className="font-mono text-[11px] text-baton-text-highlight">{repoName}</span>
          </div>
          {state.selectedBranch && (
            <>
              <span className="text-baton-border">|</span>
              <span className="font-mono text-[11px] text-baton-text-secondary">
                BRANCH {state.selectedBranch}
              </span>
            </>
          )}
          <span className="text-baton-border">|</span>
          <StatusIndicator status={state.repo || state.isDemoMode ? 'connected' : 'idle'} />
          {(state.repo || state.isDemoMode) && (
            <>
              <span className="text-baton-border">|</span>
              <button
                type="button"
                id="header-change-repository-btn"
                onClick={() => state.changeRepository()}
                aria-label="Change repository"
                className="flex items-center gap-1 font-mono text-[10px] tracking-wider text-baton-text-tertiary hover:text-baton-warning transition-colors uppercase"
                title="Exit current repository and connect a new one"
              >
                <LogOut size={11} />
                CHANGE REPO
              </button>
            </>
          )}
        </div>

        {/* Right: actions */}
        <div className="relative flex items-center gap-3">
          <button
            type="button"
            onClick={() => window.location.reload()}
            aria-label="Refresh workspace"
            className="text-baton-text-tertiary hover:text-baton-white transition-colors"
            title="Refresh workspace"
          >
            <RefreshCw size={15} />
          </button>
          <button
            type="button"
            onClick={() => state.setActiveSection('overview')}
            aria-label="Open mission overview"
            className="text-baton-text-tertiary hover:text-baton-white transition-colors"
            title="Mission overview"
          >
            <Activity size={15} />
          </button>
          <button
            type="button"
            onClick={() => setSettingsOpen((open) => !open)}
            aria-label="Open workspace settings"
            className="text-baton-text-tertiary hover:text-baton-white transition-colors"
            title="Workspace settings"
          >
            <Settings size={15} />
          </button>
          {settingsOpen && (
            <div className="absolute right-0 top-8 z-40 w-56 border border-baton-border bg-baton-near-black rounded-baton p-3 shadow-2xl">
              <MonoLabel className="block mb-3">WORKSPACE SETTINGS</MonoLabel>
              <button
                type="button"
                onClick={() => {
                  state.reset();
                  setSettingsOpen(false);
                }}
                className="w-full text-left font-mono text-[10px] tracking-wider text-baton-text-secondary hover:text-baton-warning transition-colors uppercase"
              >
                Reset local workspace
              </button>
              <p className="mt-2 text-[11px] leading-relaxed text-baton-text-tertiary">
                Clears the saved repository and team configuration from this browser.
              </p>
            </div>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-20 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <aside
          className={cn(
            'fixed lg:static w-60 flex-shrink-0 border-r border-baton-border bg-baton-near-black z-20 transition-transform duration-200',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          )}
        >
          <nav className="py-4 px-3 h-full overflow-y-auto flex flex-col">
            <div className="flex-1">
            {navSections.map((section) => (
              <div key={section.group} className="mb-6">
                <div className="px-3 mb-2">
                  <MonoLabel className="text-baton-text-tertiary">{section.group}</MonoLabel>
                </div>
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = state.activeSection === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        state.setActiveSection(item.id);
                        setSidebarOpen(false);
                      }}
                      className={cn(
                        'w-full flex items-center gap-3 px-3 py-2 text-sm rounded-baton transition-all duration-150 relative',
                        isActive
                          ? 'text-baton-white bg-baton-layer-1'
                          : 'text-baton-text-secondary hover:text-baton-text-highlight'
                      )}
                    >
                      {isActive && (
                        <motion.div
                          layoutId="sidebar-active"
                          className="absolute left-0 top-0 bottom-0 w-0.5 bg-baton-accent"
                        />
                      )}
                      <Icon size={14} className={isActive ? 'text-baton-accent' : ''} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            ))}
            </div>

            {/* Change Repository — shown when a repo is connected */}
            {(state.repo || state.isDemoMode) && (
              <div className="mt-auto pt-4 border-t border-baton-border">
                <div className="px-3 mb-2">
                  <MonoLabel className="text-baton-text-tertiary">CONNECTED REPOSITORY</MonoLabel>
                </div>
                <div className="px-3 py-1.5 mb-2">
                  <div className="font-mono text-[11px] text-baton-text-highlight truncate">
                    {state.repo ? state.repo.repository : 'demo-project'}
                  </div>
                  <div className="font-mono text-[10px] text-baton-text-tertiary truncate">
                    {state.repo ? `${state.repo.owner}/${state.repo.repository}` : 'baton/demo-project'}
                  </div>
                </div>
                <button
                  type="button"
                  id="sidebar-change-repository-btn"
                  onClick={() => {
                    setSidebarOpen(false);
                    state.changeRepository();
                  }}
                  aria-label="Exit current repository and connect a new one"
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-baton text-baton-text-secondary hover:text-baton-warning hover:bg-baton-layer-1/50 transition-all duration-150 text-sm"
                >
                  <LogOut size={13} />
                  <span className="font-mono text-[11px] tracking-wider uppercase">← Change Repository</span>
                </button>
              </div>
            )}
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto bg-baton-black">
          <motion.div
            key={state.activeSection}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="min-h-full"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
