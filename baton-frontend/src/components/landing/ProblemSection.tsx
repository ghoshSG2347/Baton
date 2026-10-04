import { motion } from 'framer-motion';
import { SectionLabel } from '@/components/ui/primitives';

const problems = [
  'Duplicated work',
  'Stale AI context',
  'Ownership confusion',
  'API assumptions',
  'Late integration',
  'Unnecessary token usage',
];

export function ProblemSection() {
  return (
    <section id="problem" className="relative py-32 px-6 lg:px-8 max-w-6xl mx-auto">
      <SectionLabel className="mb-12">02 — THE PROBLEM</SectionLabel>

      {/* Big typographic statement */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.8 }}
        className="mb-24"
      >
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight leading-tight text-balance">
          GITHUB SYNCHRONIZES THE CODE.
        </h2>
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight leading-tight mt-2 text-balance">
          <span className="text-baton-accent">BATON SYNCHRONIZES THE UNDERSTANDING.</span>
        </h2>
      </motion.div>

      {/* Forked paths visualization */}
      <div className="relative h-[400px] flex items-center justify-center">
        {/* Central source line */}
        <motion.div
          initial={{ scaleY: 0 }}
          whileInView={{ scaleY: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="absolute left-1/2 top-0 -translate-x-1/2 w-px h-16 bg-baton-accent origin-top"
        />

        {/* Fork point */}
        <motion.div
          initial={{ scale: 0 }}
          whileInView={{ scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.3, delay: 0.4 }}
          className="absolute left-1/2 top-16 -translate-x-1/2 w-2 h-2 rounded-full bg-baton-accent"
        />

        {/* Diverging paths */}
        <div className="relative w-full max-w-3xl flex justify-between items-start pt-20">
          {['Frontend AI', 'Backend AI', 'Mission Control', 'GitHub'].map((label, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: -20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.5 + i * 0.1 }}
              className="relative flex-1 text-center"
              style={{ maxWidth: '180px' }}
            >
              {/* Curved line to node */}
              <svg
                className="absolute -top-20 left-1/2 -translate-x-1/2 w-32 h-20"
                style={{
                  transform: `translateX(calc(-50% + ${(i - 1.5) * 30}px)) rotate(${(i - 1.5) * 8}deg)`,
                }}
              >
                <motion.line
                  x1="50%"
                  y1="0"
                  x2="50%"
                  y2="100%"
                  stroke="#303236"
                  strokeWidth="1"
                  initial={{ pathLength: 0 }}
                  whileInView={{ pathLength: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.6 + i * 0.1 }}
                />
              </svg>
              <div className="mb-2 w-2 h-2 rounded-full bg-baton-border mx-auto" />
              <span className="font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase block">
                {label}
              </span>
            </motion.div>
          ))}
        </div>

        {/* Baton reconnection line */}
        <motion.div
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 1.2 }}
          className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full max-w-3xl h-px bg-gradient-to-r from-transparent via-baton-accent to-transparent origin-center"
        />
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 1.5 }}
          className="absolute bottom-0 left-1/2 -translate-x-1/2 -translate-y-6"
        >
          <span className="font-mono text-[10px] tracking-[0.2em] text-baton-accent uppercase">BATON RECONNECTS</span>
        </motion.div>
      </div>

      {/* Problem fragments */}
      <div className="mt-20 grid grid-cols-2 md:grid-cols-3 gap-px bg-baton-border">
        {problems.map((problem, i) => (
          <motion.div
            key={problem}
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.08 }}
            className="bg-baton-black p-6 flex items-center gap-3"
          >
            <span className="w-1 h-1 rounded-full bg-baton-warning" />
            <span className="text-sm text-baton-text-tertiary">{problem}</span>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
