import { motion } from 'framer-motion';
import { SectionLabel, MonoLabel } from '@/components/ui/primitives';

export function ConflictRadarSection() {
  return (
    <section className="relative py-32 px-6 lg:px-8 max-w-5xl mx-auto">
      <SectionLabel className="mb-12">07 — CONFLICT RADAR</SectionLabel>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-16 text-balance"
      >
        Two branches. One file.
        <br />
        <span className="text-baton-text-secondary">Catch it before it becomes a merge problem.</span>
      </motion.h2>

      {/* Branch lane visualization */}
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="border border-baton-border bg-baton-near-black rounded-baton p-8"
      >
        {/* Alex lane */}
        <div className="flex items-center gap-4 mb-2">
          <span className="font-mono text-[11px] text-baton-text-highlight w-20">ALEX</span>
          <div className="font-mono text-[10px] text-baton-text-tertiary">member/alex-ui</div>
        </div>
        <div className="flex items-center gap-2 ml-24 mb-4">
          <motion.div
            className="h-px bg-baton-text-secondary"
            initial={{ width: 0 }}
            whileInView={{ width: '60%' }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          />
          <motion.div
            className="w-2 h-2 rounded-full bg-baton-accent"
            initial={{ scale: 0 }}
            whileInView={{ scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.3, delay: 0.8 }}
          />
        </div>

        {/* Convergence point */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 1 }}
          className="ml-24 pl-[60%] -mt-2 mb-2"
        >
          <div className="border border-baton-warning/40 bg-baton-black rounded-baton px-4 py-3 inline-block">
            <MonoLabel variant="warning">SHARED FILE DETECTED</MonoLabel>
            <div className="font-mono text-[12px] text-baton-text-highlight mt-1.5">
              src/api/client.ts
            </div>
          </div>
        </motion.div>

        {/* Sam lane */}
        <div className="flex items-center gap-4 mb-2 mt-4">
          <span className="font-mono text-[11px] text-baton-text-highlight w-20">SAM</span>
          <div className="font-mono text-[10px] text-baton-text-tertiary">member/sam-api</div>
        </div>
        <div className="flex items-center gap-2 ml-24">
          <motion.div
            className="h-px bg-baton-text-secondary"
            initial={{ width: 0 }}
            whileInView={{ width: '60%' }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.3 }}
          />
          <motion.div
            className="w-2 h-2 rounded-full bg-baton-accent"
            initial={{ scale: 0 }}
            whileInView={{ scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.3, delay: 1.1 }}
          />
        </div>

        {/* Explanation */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 1.4 }}
          className="mt-8 pt-6 border-t border-baton-border"
        >
          <p className="text-sm text-baton-text-tertiary leading-relaxed">
            Both branches are touching <span className="font-mono text-baton-text-highlight">src/api/client.ts</span>.
          </p>
          <p className="text-sm text-baton-text-secondary mt-1">
            Talk before you push further.
          </p>
          <div className="mt-4 flex items-center gap-4">
            <MonoLabel variant="warning">POSSIBLE SHARED-FILE CONFLICT</MonoLabel>
            <span className="font-mono text-[10px] text-baton-text-tertiary">
              Not a guaranteed merge conflict — a coordination signal.
            </span>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}
