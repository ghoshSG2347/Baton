import { motion } from 'framer-motion';
import { useState } from 'react';
import { UserPlus, Trash2, GitBranch, Folder, Users } from 'lucide-react';
import type { WorkspaceStateHook } from '@/hooks/useWorkspaceState';
import type { TeamMember } from '@/types';
import { Button, MonoLabel, Panel, SectionLabel } from '@/components/ui/primitives';
import { DEMO_MEMBERS } from '@/lib/demo';
import { generateId } from '@/lib/utils';

export function Team({ state }: { state: WorkspaceStateHook }) {
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '', github: '', branch: '', role: '', folders: '', job: '', dependsOn: '', providesTo: '', doNotTouch: '', teamScope: '',
  });

  const members = state.isDemoMode && state.members.length === 0 ? DEMO_MEMBERS : state.members;

  const handleAdd = () => {
    if (!formData.name.trim()) return;
    const member: TeamMember = {
      id: generateId(),
      name: formData.name,
      github: formData.github,
      branch: formData.branch,
      role: formData.role,
      folders: formData.folders.split(',').map((f) => f.trim()).filter(Boolean),
      job: formData.job,
      depends_on: formData.dependsOn.split(',').map((d) => d.trim()).filter(Boolean),
      provides_to: formData.providesTo.split(',').map((p) => p.trim()).filter(Boolean),
      do_not_touch: formData.doNotTouch.split(',').map((p) => p.trim()).filter(Boolean),
      team_scope: formData.teamScope.split(',').map((p) => p.trim()).filter(Boolean),
    };
    state.addMember(member);
    setFormData({ name: '', github: '', branch: '', role: '', folders: '', job: '', dependsOn: '', providesTo: '', doNotTouch: '', teamScope: '' });
    setShowForm(false);
  };

  const handleLoadDemo = () => {
    state.setIsDemoMode(true);
    DEMO_MEMBERS.forEach((m) => state.addMember(m));
  };

  return (
    <div className="p-6 lg:p-8 max-w-6xl">
      <SectionLabel className="mb-6">TEAM & OWNERSHIP</SectionLabel>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Team & Ownership</h1>
      <p className="text-sm text-baton-text-tertiary mb-8">Define who owns what. The operational map of the project.</p>

      {/* Actions */}
      <div className="flex items-center gap-3 mb-6">
        <Button variant="primary" onClick={() => setShowForm(!showForm)}>
          <UserPlus size={14} />
          ADD MEMBER
        </Button>
        {members.length === 0 && (
          <Button variant="secondary" onClick={handleLoadDemo}>
            LOAD DEMO TEAM
          </Button>
        )}
        {state.isDemoMode && (
          <span className="font-mono text-[9px] tracking-wider text-baton-accent border border-baton-accent/30 px-2 py-0.5 rounded-baton uppercase">
            Demo Data
          </span>
        )}
      </div>

      {/* Add form */}
      {showForm && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          <Panel label="NEW MEMBER" className="mb-6">
            <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { key: 'name', label: 'Member Name', placeholder: 'Maya' },
                { key: 'github', label: 'GitHub Username', placeholder: 'maya' },
                { key: 'branch', label: 'Branch', placeholder: 'member/maya-ui' },
                { key: 'role', label: 'Role', placeholder: 'Frontend Lead' },
                { key: 'folders', label: 'Folders (comma-separated)', placeholder: '/frontend, /components' },
                { key: 'job', label: 'Job', placeholder: 'Build the user interface...' },
                { key: 'doNotTouch', label: 'Do not touch (comma-separated)', placeholder: 'database/, deployment/' },
                { key: 'teamScope', label: 'Team scope (comma-separated)', placeholder: 'client/, shared/' },
                { key: 'dependsOn', label: 'Depends On (comma-separated)', placeholder: 'Arjun' },
                { key: 'providesTo', label: 'Provides To (comma-separated)', placeholder: 'Arjun' },
              ].map((field) => (
                <div key={field.key}>
                  <label className="block font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase mb-1.5">
                    {field.label}
                  </label>
                  <input
                    type="text"
                    value={formData[field.key as keyof typeof formData]}
                    onChange={(e) => setFormData({ ...formData, [field.key]: e.target.value })}
                    placeholder={field.placeholder}
                    className="w-full border border-baton-border bg-baton-black rounded-baton px-3 py-2 text-sm text-baton-white placeholder:text-baton-text-tertiary outline-none focus:border-baton-text-tertiary transition-colors"
                  />
                </div>
              ))}
              <div className="md:col-span-2 flex items-center gap-3">
                <Button variant="primary" onClick={handleAdd} disabled={!formData.name.trim()}>
                  SAVE MEMBER
                </Button>
                <Button variant="ghost" onClick={() => setShowForm(false)}>
                  CANCEL
                </Button>
              </div>
            </div>
          </Panel>
        </motion.div>
      )}

      {/* Members grid */}
      {members.length === 0 && !showForm ? (
        <Panel>
          <div className="p-12 text-center">
            <Users size={32} className="mx-auto text-baton-text-tertiary mb-4" />
            <p className="text-sm text-baton-text-tertiary mb-1">No team members configured.</p>
            <p className="text-xs text-baton-text-tertiary">Add a member or load the demo team to begin.</p>
          </div>
        </Panel>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {members.map((member, i) => (
            <motion.div
              key={member.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.1 }}
            >
              <Panel>
                <div className="p-5">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-2 h-2 rounded-full bg-baton-accent" />
                        <span className="text-lg font-bold tracking-tight">{member.name}</span>
                      </div>
                      <MonoLabel>{member.role}</MonoLabel>
                    </div>
                    {!state.isDemoMode && (
                      <button
                        onClick={() => state.removeMember(member.id)}
                        className="text-baton-text-tertiary hover:text-baton-warning transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>

                  {/* Branch */}
                  <div className="flex items-center gap-2 mb-4 font-mono text-[11px] text-baton-text-secondary">
                    <GitBranch size={12} className="text-baton-text-tertiary" />
                    {member.branch}
                  </div>

                  {/* Owners */}
                  <div className="mb-4">
                    <MonoLabel className="mb-2 block">OWNERS</MonoLabel>
                    <div className="space-y-1">
                      {member.folders.map((folder) => (
                        <div key={folder} className="flex items-center gap-2 font-mono text-[11px] text-baton-text-highlight">
                          <Folder size={11} className="text-baton-accent" />
                          {folder}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Dependencies */}
                  {(member.depends_on.length > 0 || member.provides_to.length > 0) && (
                    <div className="grid grid-cols-2 gap-4 pt-4 border-t border-baton-border">
                      {member.depends_on.length > 0 && (
                        <div>
                          <MonoLabel className="mb-1.5 block">DEPENDS ON</MonoLabel>
                          <div className="font-mono text-[11px] text-baton-text-secondary">
                            {member.depends_on.join(', ')}
                          </div>
                        </div>
                      )}
                      {member.provides_to.length > 0 && (
                        <div>
                          <MonoLabel className="mb-1.5 block">PROVIDES TO</MonoLabel>
                          <div className="font-mono text-[11px] text-baton-text-secondary">
                            {member.provides_to.join(', ')}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Job */}
                  {member.job && (
                    <div className="mt-4 pt-4 border-t border-baton-border">
                      <MonoLabel className="mb-1.5 block">JOB</MonoLabel>
                      <p className="text-sm text-baton-text-tertiary">{member.job}</p>
                    </div>
                  )}
                </div>
              </Panel>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
