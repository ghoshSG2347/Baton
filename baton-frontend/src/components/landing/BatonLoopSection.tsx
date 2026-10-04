import { motion } from 'framer-motion';
import { SectionLabel } from '@/components/ui/primitives';

const stages = [
  { label: 'GITHUB', desc: 'Connect the repository' },
  { label: 'UNDERSTAND', desc: 'Analyze the real code' },
  { label: 'DEFINE OWNERSHIP', desc: 'Assign branches and folders' },
  { label: 'ANALYZE', desc: 'Extract structure and contracts' },
  { label: 'GENERATE CONTEXT', desc: 'Build the focused packet' },
  { label: 'HANDOFF', desc: 'Transfer to the next teammate' },
  { label: 'AI CODING', desc: 'Prompt into Antigravity / Cursor' },
  { label: 'PUSH', desc: 'Commit completed work' },
  { label: 'REPEAT', desc: 'The loop continues' },
];

export function BatonLoopSection() {
  return (
    <section id="workflow" className="relative py-32 px-6 lg:px-8 max-w-5xl mx-auto">
      <SectionLabel className="mb-12">03 — THE BATON LOOP</SectionLabel>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-16 text-balance"
      >
        A continuous mission pipeline.
      </motion.h2>

      {/* Animated rail */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-[7px] top-0 bottom-0 w-px bg-baton-border" />

        {stages.map((stage, i) => (
          <motion.div
            key={stage.label}
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.4, delay: 0 }}
            className="relative flex items-start gap-6 pb-12 group"
          >
            {/* Node */}
            <div className="relative z-10 flex-shrink-0">
              <motion.div
                className="w-4 h-4 rounded-full border-2 border-baton-border bg-baton-black group-hover:border-baton-accent transition-colors duration-300"
                whileInView={{ borderColor: '#34d59a' }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
                <motion.div
                  className="w-full h-full rounded-full bg-baton-accent"
                  initial={{ scale: 0 }}
                  whileInView={{ scale: 1 }}
                  viewport={{ once: true, margin: '-50px' }}
                  transition={{ duration: 0.3, delay: 0.3 }}
                />
              </motion.div>
            </div>

            {/* Content */}
            <div className="flex-1 pt-0">
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-[10px] text-baton-text-tertiary">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span className="text-lg font-semibold tracking-tight text-baton-white group-hover:text-baton-accent transition-colors duration-300">
                  {stage.label}
                </span>
              </div>
              <p className="text-sm text-baton-text-tertiary mt-1 ml-7">{stage.desc}</p>
            </div>
          </motion.div>
        ))}

        {/* Loop indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="absolute -left-2 top-0 bottom-0 flex items-center"
        >
          <div className="w-4 h-full flex flex-col justify-between">
            <div className="w-px h-full bg-gradient-to-b from-transparent via-baton-accent/20 to-transparent ml-2" />
          </div>
        </motion.div>
      </div>
    </section>
  );
}
