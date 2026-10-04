import { motion } from 'framer-motion';
import { SectionLabel, MonoLabel } from '@/components/ui/primitives';

const frontendRoutes = [
  { method: 'GET', path: '/api/projects', matched: true },
  { method: 'POST', path: '/api/auth', matched: true },
  { method: 'GET', path: '/api/tasks', matched: false },
];

export function IntegrationSection() {
  return (
    <section className="relative py-32 px-6 lg:px-8 max-w-5xl mx-auto">
      <SectionLabel className="mb-12">08 — INTEGRATION</SectionLabel>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-16 text-balance"
      >
        Frontend expects. Backend provides.
        <br />
        <span className="text-baton-text-secondary">Baton checks they match.</span>
      </motion.h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Frontend */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="border border-baton-border bg-baton-near-black rounded-baton"
        >
          <div className="border-b border-baton-border px-4 py-2">
            <MonoLabel>FRONTEND BRANCH — API CALLS</MonoLabel>
          </div>
          <div className="p-4 space-y-2">
            {frontendRoutes.map((route, i) => (
              <motion.div
                key={route.path}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: i * 0.1 }}
                className="flex items-center justify-between font-mono text-[12px]"
              >
                <span className="text-baton-text-highlight">
                  <span className="text-baton-text-tertiary mr-2">{route.method}</span>
                  {route.path}
                </span>
                <span className={route.matched ? 'text-baton-accent' : 'text-baton-warning'}>
                  {route.matched ? 'MATCH' : 'UNMATCHED'}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Backend */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="border border-baton-border bg-baton-near-black rounded-baton"
        >
          <div className="border-b border-baton-border px-4 py-2">
            <MonoLabel>BACKEND BRANCH — ROUTES</MonoLabel>
          </div>
          <div className="p-4 space-y-2">
            {[
              { method: 'GET', path: '/api/projects' },
              { method: 'POST', path: '/api/auth' },
            ].map((route, i) => (
              <motion.div
                key={route.path}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: i * 0.1 }}
                className="flex items-center justify-between font-mono text-[12px]"
              >
                <span className="text-baton-text-highlight">
                  <span className="text-baton-text-tertiary mr-2">{route.method}</span>
                  {route.path}
                </span>
                <span className="text-baton-accent">MATCH</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="mt-6 border border-baton-warning/30 bg-baton-near-black rounded-baton p-5 flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <motion.div
            className="w-2 h-2 rounded-full bg-baton-warning"
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <MonoLabel variant="warning">INTEGRATION CHECK — ATTENTION REQUIRED</MonoLabel>
        </div>
        <span className="font-mono text-[12px] text-baton-text-highlight">
          1 unmatched endpoint
        </span>
      </motion.div>
    </section>
  );
}
