import { motion } from 'framer-motion';
import { SectionLabel, MonoLabel } from '@/components/ui/primitives';

const logLines = [
  { text: '> Baton analyzes branch member/maya-ui', type: 'info' },
  { text: '> Reading frontend/src/services/api.ts', type: 'dim' },
  { text: '> Reading frontend/src/types/index.ts', type: 'dim' },
  { text: '> Detected 3 API calls', type: 'accent' },
  { text: '> Detected 4 type definitions', type: 'accent' },
  { text: '> context.md generated', type: 'success' },
  { text: '> Estimated tokens: 3,280', type: 'info' },
  { text: '', type: 'spacer' },
  { text: '> Member 02 receives context packet', type: 'info' },
  { text: '> Paste into ChatGPT / Claude conversation', type: 'dim' },
  { text: '> Add job: "Implement backend API endpoints"', type: 'dim' },
  { text: '> Planning AI generates focused coding prompt', type: 'accent' },
  { text: '> Paste into Antigravity / Cursor', type: 'dim' },
  { text: '> Implementation begins', type: 'success' },
];

export function HandoffSection() {
  return (
    <section className="relative py-32 px-6 lg:px-8 max-w-5xl mx-auto">
      <SectionLabel className="mb-12">06 — HANDOFF</SectionLabel>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-16 text-balance"
      >
        A structured handoff,
        <br />
        <span className="text-baton-text-secondary">not a vague "frontend is mostly done."</span>
      </motion.h2>

      {/* Terminal log */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="border border-baton-border bg-baton-near-black rounded-baton"
      >
        <div className="border-b border-baton-border px-4 py-2 flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-2 h-2 rounded-full bg-baton-border" />
            <div className="w-2 h-2 rounded-full bg-baton-border" />
            <div className="w-2 h-2 rounded-full bg-baton-border" />
          </div>
          <MonoLabel className="ml-2">BATON — SYSTEM LOG</MonoLabel>
        </div>
        <div className="p-5 font-mono text-[12px] leading-relaxed min-h-[320px]">
          {logLines.map((line, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.1, delay: i * 0.08 }}
              className={
                line.type === 'accent' ? 'text-baton-accent'
                : line.type === 'success' ? 'text-baton-accent'
                : line.type === 'info' ? 'text-baton-text-highlight'
                : line.type === 'dim' ? 'text-baton-text-tertiary'
                : 'text-baton-text-tertiary'
              }
            >
              {line.text || '\u00A0'}
            </motion.div>
          ))}
          <motion.span
            className="inline-block w-2 h-3.5 bg-baton-accent align-middle"
            animate={{ opacity: [1, 0, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        </div>
      </motion.div>
    </section>
  );
}
