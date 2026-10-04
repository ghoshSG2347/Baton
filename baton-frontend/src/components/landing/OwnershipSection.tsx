import { motion } from 'framer-motion';
import { SectionLabel, MonoLabel } from '@/components/ui/primitives';

const owners = [
  { name: 'MAYA', role: 'Frontend Lead', branch: 'member/maya-ui', folders: ['/frontend', '/components', '/pages'] },
  { name: 'ARJUN', role: 'Backend Lead', branch: 'member/arjun-api', folders: ['/backend', '/api', '/models'] },
  { name: 'SHARED', role: 'Contracts', branch: 'main', folders: ['/contracts'] },
];

export function OwnershipSection() {
  return (
    <section className="relative py-32 px-6 lg:px-8 max-w-6xl mx-auto">
      <SectionLabel className="mb-12">05 — OWNERSHIP</SectionLabel>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-16 text-balance"
      >
        Baton doesn't tell people how to code.
        <br />
        <span className="text-baton-text-secondary">It tells them what they should understand before coding.</span>
      </motion.h2>

      {/* Ownership map */}
      <div className="relative">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {owners.map((owner, i) => (
            <motion.div
              key={owner.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.15 }}
              className={`border ${owner.name === 'SHARED' ? 'border-baton-accent/30' : 'border-baton-border'} bg-baton-near-black rounded-baton p-5`}
            >
              <div className="flex items-center gap-2 mb-3">
                <div className={`w-2 h-2 rounded-full ${owner.name === 'SHARED' ? 'bg-baton-accent' : 'bg-baton-white'}`} />
                <span className="text-lg font-bold tracking-tight">{owner.name}</span>
              </div>
              <div className="font-mono text-[10px] text-baton-text-tertiary uppercase tracking-wider mb-3">
                {owner.role}
              </div>
              <div className="font-mono text-[11px] text-baton-text-secondary mb-2">
                branch: {owner.branch}
              </div>
              <div className="font-mono text-[10px] text-baton-text-tertiary uppercase tracking-wider mb-1">
                OWNERS
              </div>
              <div className="space-y-1">
                {owner.folders.map((folder) => (
                  <div key={folder} className="font-mono text-[11px] text-baton-text-highlight">
                    {folder}
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Cross-boundary edit warning */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="border border-baton-warning/30 bg-baton-near-black rounded-baton p-6"
        >
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-1">
              <motion.div
                className="w-2 h-2 rounded-full bg-baton-warning"
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-2">
                <MonoLabel variant="warning">POSSIBLE OWNERSHIP VIOLATION</MonoLabel>
              </div>
              <p className="text-sm text-baton-text-tertiary leading-relaxed">
                Arjun's branch <span className="font-mono text-baton-text-highlight">member/arjun-api</span> changed
                <span className="font-mono text-baton-text-highlight"> /frontend/api/client.ts</span>,
                which is owned by Maya.
              </p>
              <p className="text-sm text-baton-text-secondary mt-2">
                Review before merging. The team may deliberately allow shared edits.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
