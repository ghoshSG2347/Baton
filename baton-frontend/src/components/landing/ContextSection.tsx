import { motion } from 'framer-motion';
import { SectionLabel, MonoLabel } from '@/components/ui/primitives';

const repoTreeNodes = [
  'frontend/', 'frontend/src/', 'frontend/src/App.tsx', 'frontend/src/main.tsx',
  'frontend/src/components/', 'frontend/src/components/Header.tsx',
  'frontend/src/components/Sidebar.tsx', 'frontend/src/services/',
  'frontend/src/services/api.ts', 'frontend/src/types/',
  'frontend/src/types/index.ts', 'frontend/src/mocks/',
  'frontend/src/mocks/userFixture.json', 'frontend/src/hooks/',
  'frontend/src/hooks/useAuth.ts', 'frontend/src/pages/',
  'frontend/src/pages/Dashboard.tsx', 'frontend/src/pages/Settings.tsx',
  'frontend/package.json', 'frontend/vite.config.ts',
  'backend/', 'backend/app/', 'backend/app/main.py',
  'backend/app/api/', 'backend/app/api/routes/',
  'backend/app/api/routes/projects.py', 'backend/app/api/routes/auth.py',
  'backend/app/models/', 'backend/app/models/user.py',
  'backend/app/schemas/', 'backend/app/schemas/project.py',
  'backend/app/services/', 'backend/app/database/',
  'backend/requirements.txt', 'backend/.env.example',
  'contracts/', 'contracts/api.md', 'contracts/data.md',
  'docs/', 'docs/PRD_DIGEST.md', 'docs/ARCHITECTURE.md',
  'render.yaml', 'README.md', '.gitignore',
];

const contextPacket = [
  '# Baton Context',
  '## Source',
  '- Repository: baton/demo-project',
  '- Branch: member/maya-ui',
  '- Commit: a1b2c3d',
  '',
  '## Project Stack',
  '- React, TypeScript, Vite',
  '',
  '## Detected Frontend Expectations',
  '- GET /api/projects',
  '- POST /api/auth',
  '- GET /api/tasks',
  '',
  '## Types / Data Shapes',
  '- Project, Task, AuthResponse',
  '',
  '## Handoff',
  '- TODO: Integrate authentication flow',
  '',
  '## Files Included for Verification',
  '- frontend/src/services/api.ts',
  '- frontend/src/types/index.ts',
];

export function ContextSection() {
  return (
    <section className="relative py-32 px-6 lg:px-8 max-w-6xl mx-auto">
      <SectionLabel className="mb-12">04 — CONTEXT IS THE PRODUCT</SectionLabel>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight leading-tight mb-4 text-balance"
      >
        THE AI DOESN'T NEED
        <br />
        THE WHOLE REPOSITORY.
        <br />
        <span className="text-baton-text-secondary">IT NEEDS THE RIGHT PART.</span>
      </motion.h2>

      {/* Comparison visualization */}
      <div className="mt-20 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Full repository tree */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="border border-baton-border bg-baton-near-black rounded-baton"
        >
          <div className="border-b border-baton-border px-4 py-2 flex items-center justify-between">
            <MonoLabel>FULL REPOSITORY</MonoLabel>
            <span className="font-mono text-[10px] text-baton-text-tertiary">44 files</span>
          </div>
          <div className="p-4 h-80 overflow-hidden">
            <div className="font-mono text-[11px] leading-relaxed">
              {repoTreeNodes.map((node, i) => (
                <motion.div
                  key={node}
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.02, delay: i * 0.015 }}
                  className={`truncate ${node.endsWith('/') ? 'text-baton-text-tertiary' : 'text-baton-text-secondary'}`}
                  style={{ paddingLeft: `${(node.split('/').length - 1) * 12}px` }}
                >
                  {node.endsWith('/') ? '▸' : '•'} {node.split('/').pop()}
                </motion.div>
              ))}
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-baton-near-black to-transparent pointer-events-none" />
          </div>
          <div className="border-t border-baton-border px-4 py-2">
            <span className="font-mono text-[10px] text-baton-text-tertiary">
              ESTIMATED: 18,420 TOKENS
            </span>
          </div>
        </motion.div>

        {/* Right: Focused context packet */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="border border-baton-accent/30 bg-baton-near-black rounded-baton"
        >
          <div className="border-b border-baton-border px-4 py-2 flex items-center justify-between">
            <MonoLabel variant="accent">BATON CONTEXT</MonoLabel>
            <span className="font-mono text-[10px] text-baton-accent">8 files</span>
          </div>
          <div className="p-4 h-80 overflow-hidden">
            <div className="font-mono text-[11px] leading-relaxed">
              {contextPacket.map((line, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.03, delay: i * 0.02 }}
                  className={
                    line.startsWith('#')
                      ? 'text-baton-accent font-semibold'
                      : line.startsWith('-')
                        ? 'text-baton-text-highlight pl-3'
                        : 'text-baton-text-tertiary'
                  }
                >
                  {line || '\u00A0'}
                </motion.div>
              ))}
            </div>
          </div>
          <div className="border-t border-baton-accent/20 px-4 py-2">
            <span className="font-mono text-[10px] text-baton-accent">
              ESTIMATED: 3,280 TOKENS
            </span>
          </div>
        </motion.div>
      </div>

      {/* Token meter */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="mt-12"
      >
        <div className="flex items-center justify-between mb-2">
          <MonoLabel>CONTEXT BUDGET — DEMONSTRATION DATA</MonoLabel>
          <span className="font-mono text-[10px] text-baton-text-tertiary">
            3,280 / 8,000
          </span>
        </div>
        <div className="h-1 bg-baton-border rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-baton-accent rounded-full"
            initial={{ width: 0 }}
            whileInView={{ width: '41%' }}
            viewport={{ once: true }}
            transition={{ duration: 1, delay: 0.3 }}
          />
        </div>
      </motion.div>
    </section>
  );
}
