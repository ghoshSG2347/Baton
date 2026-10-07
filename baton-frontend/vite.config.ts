import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';
import { execFileSync } from 'node:child_process';

// Public build identity only; never include environment values in the bundle.
let candidate = process.env.VERCEL_GIT_COMMIT_SHA || '';
if (!candidate) {
  try { candidate = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { /* revision unknown outside a Git checkout */ }
}
const revision = /^[0-9a-f]{40}$/.test(candidate) ? candidate : '';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), { name: 'baton-build-revision', transformIndexHtml: () => [
    { tag: 'meta', attrs: { name: 'baton-revision', content: revision }, injectTo: 'head' },
  ] }],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
});
