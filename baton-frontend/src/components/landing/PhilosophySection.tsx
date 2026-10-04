import { motion } from 'framer-motion';
import { SectionLabel } from '@/components/ui/primitives';

export function PhilosophySection() {
  return (
    <section id="philosophy" className="relative py-32 px-6 lg:px-8 max-w-4xl mx-auto">
      <SectionLabel className="mb-12">09 — PHILOSOPHY</SectionLabel>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.05] mb-16 text-balance"
      >
        OWN THE DECISIONS.
        <br />
        <span className="text-baton-text-secondary">RENT THE PLUMBING.</span>
      </motion.h2>

      <div className="space-y-1">
        {[
          { tool: 'GitHub', role: 'stores the code' },
          { tool: 'ChatGPT / Claude', role: 'handles reasoning' },
          { tool: 'Antigravity / Cursor', role: 'handles implementation' },
          { tool: 'Baton', role: 'handles context and coordination', accent: true },
        ].map((item, i) => (
          <motion.div
            key={item.tool}
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.1 }}
            className="flex items-baseline gap-3 py-2 border-b border-baton-border/50 last:border-0"
          >
            <span className={`text-lg font-semibold tracking-tight ${item.accent ? 'text-baton-accent' : 'text-baton-white'}`}>
              {item.tool}
            </span>
            <span className="text-sm text-baton-text-tertiary">
              {item.role}
            </span>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
