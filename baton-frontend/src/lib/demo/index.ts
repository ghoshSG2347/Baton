import type { AnalysisResult, ConflictResult, IntegrationResult, TeamMember } from '@/types';

export const DEMO_MEMBERS: TeamMember[] = [
  {
    id: 'm1',
    name: 'Maya',
    github: 'maya',
    branch: 'member/maya-ui',
    role: 'Frontend Lead',
    folders: ['/frontend', '/components', '/pages'],
    job: 'Build the user interface and frontend API integration.',
    depends_on: [],
    provides_to: ['Arjun'],
  },
  {
    id: 'm2',
    name: 'Arjun',
    github: 'arjun',
    branch: 'member/arjun-api',
    role: 'Backend Lead',
    folders: ['/backend', '/api', '/models'],
    job: 'Build the API and database required by the frontend.',
    depends_on: ['Maya'],
    provides_to: ['Maya'],
  },
];

export const DEMO_ANALYSIS: AnalysisResult = {
  metadata: {
    owner: 'baton',
    repo: 'demo-project',
    branch: 'member/maya-ui',
    folder: '/frontend',
    commit: 'a1b2c3d4e5f6789',
    generated: new Date().toISOString(),
    files_analyzed: 14,
    skipped_files: ['src/assets/large_graphic.png'],
  },
  stack: {
    detected: ['React', 'TypeScript', 'Vite', 'Tailwind CSS'],
    languages: ['typescript', 'json', 'css', 'markdown'],
  },
  file_tree: [
    { path: 'frontend/package.json', type: 'blob', size: 520 },
    { path: 'frontend/src/App.tsx', type: 'blob', size: 1200 },
    { path: 'frontend/src/main.tsx', type: 'blob', size: 300 },
    { path: 'frontend/src/components/Header.tsx', type: 'blob', size: 850 },
    { path: 'frontend/src/components/Sidebar.tsx', type: 'blob', size: 640 },
    { path: 'frontend/src/services/api.ts', type: 'blob', size: 920 },
    { path: 'frontend/src/types/index.ts', type: 'blob', size: 480 },
    { path: 'frontend/src/mocks/userFixture.json', type: 'blob', size: 340 },
    { path: 'frontend/vite.config.ts', type: 'blob', size: 280 },
  ],
  important_files: [
    'frontend/package.json',
    'frontend/src/App.tsx',
    'frontend/src/services/api.ts',
  ],
  routes: [],
  api_calls: [
    'frontend/src/services/api.ts: GET /api/projects',
    'frontend/src/services/api.ts: POST /api/auth',
    'frontend/src/services/api.ts: GET /api/tasks',
  ],
  environment_variables: ['VITE_API_BASE_URL'],
  types: ['Project', 'Task', 'AuthResponse', 'ApiResponse'],
  mock_data: ['frontend/src/mocks/userFixture.json'],
  handoffs: [
    {
      path: 'frontend/src/App.tsx',
      items: ['// TODO: Integrate authentication flow', '// FIXME: Handle token expiration'],
    },
  ],
  shared_files: [],
  stray_files: [],
  analysis_warnings: ['1 file was skipped due to size limits.'],
};

export const DEMO_CONFLICTS: ConflictResult = {
  conflicts: [
    {
      path: 'src/api/client.ts',
      branches: ['member/alex-ui', 'member/sam-api'],
      reason: 'shared file changed by multiple branches',
    },
  ],
  conflict_count: 1,
};

export const DEMO_INTEGRATION: IntegrationResult = {
  owner: 'baton',
  repo: 'demo-project',
  branch: 'main',
  status: 'analyzed',
  comparison: {
    frontend_routes: ['GET /api/projects', 'POST /api/auth', 'GET /api/tasks'],
    backend_routes: ['GET /api/projects', 'POST /api/auth'],
    unmatched_frontend_routes: ['GET /api/tasks'],
    unmatched_backend_routes: [],
    compatible: false,
  },
};

export const DEMO_ACTIVITIES = [
  { time: '18:42', event: 'frontend branch analyzed', type: 'info' },
  { time: '18:39', event: 'new API route detected', type: 'success' },
  { time: '18:37', event: 'shared file overlap detected', type: 'warning' },
  { time: '18:31', event: 'context generated', type: 'success' },
  { time: '18:28', event: 'repository connected', type: 'info' },
  { time: '18:22', event: 'team configuration saved', type: 'info' },
];

export const DEMO_BRANCHES = [
  { name: 'main', sha: '7fd1a60b01f91b314f59955a4e4d4e80d8edf11d' },
  { name: 'member/maya-ui', sha: 'a1b2c3d4e5f6789' },
  { name: 'member/arjun-api', sha: 'b2c3d4e5f67890a' },
  { name: 'member/alex-ui', sha: 'c3d4e5f67890ab' },
  { name: 'member/sam-api', sha: 'd4e5f67890abc1' },
  { name: 'feature/auth', sha: 'e5f67890abcd12' },
];

export const DEMO_TREE: import('@/types').TreeItem[] = [
  { path: 'frontend/', type: 'tree', size: null, sha: '' },
  { path: 'frontend/src/', type: 'tree', size: null, sha: '' },
  { path: 'frontend/src/App.tsx', type: 'blob', size: 1200, sha: '' },
  { path: 'frontend/src/main.tsx', type: 'blob', size: 300, sha: '' },
  { path: 'frontend/src/services/', type: 'tree', size: null, sha: '' },
  { path: 'frontend/src/services/api.ts', type: 'blob', size: 920, sha: '' },
  { path: 'frontend/src/types/', type: 'tree', size: null, sha: '' },
  { path: 'frontend/src/types/index.ts', type: 'blob', size: 480, sha: '' },
  { path: 'frontend/package.json', type: 'blob', size: 520, sha: '' },
  { path: 'frontend/vite.config.ts', type: 'blob', size: 280, sha: '' },
  { path: 'backend/', type: 'tree', size: null, sha: '' },
  { path: 'backend/app/', type: 'tree', size: null, sha: '' },
  { path: 'backend/app/main.py', type: 'blob', size: 410, sha: '' },
  { path: 'backend/app/api/', type: 'tree', size: null, sha: '' },
  { path: 'backend/app/api/routes/', type: 'tree', size: null, sha: '' },
  { path: 'backend/app/api/routes/projects.py', type: 'blob', size: 680, sha: '' },
  { path: 'backend/app/api/routes/auth.py', type: 'blob', size: 540, sha: '' },
  { path: 'backend/requirements.txt', type: 'blob', size: 120, sha: '' },
  { path: 'contracts/', type: 'tree', size: null, sha: '' },
  { path: 'contracts/api.md', type: 'blob', size: 320, sha: '' },
  { path: 'contracts/data.md', type: 'blob', size: 180, sha: '' },
  { path: 'docs/', type: 'tree', size: null, sha: '' },
  { path: 'docs/PRD_DIGEST.md', type: 'blob', size: 890, sha: '' },
  { path: 'render.yaml', type: 'blob', size: 240, sha: '' },
  { path: 'README.md', type: 'blob', size: 450, sha: '' },
];

export const DEMO_FILE_CONTENT = `import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchProjects() {
  const res = await fetch(\`\${API_BASE}/api/projects\`);
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
}

export async function login(email: string, password: string) {
  const res = await fetch(\`\${API_BASE}/api/auth\`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return res.json();
}

export async function fetchTasks(projectId: string) {
  const res = await fetch(\`\${API_BASE}/api/tasks?project=\${projectId}\`);
  return res.json();
}
`;

export const DEMO_CONTEXT_MARKDOWN = `# Baton Context

## Source
- Repository: baton/demo-project
- Branch: member/maya-ui
- Commit: a1b2c3d
- Generated: ${new Date().toISOString().substring(0, 16)}

## Requesting Member
- Name: Arjun
- Role: Backend
- Owns: /backend

## Do Not Touch
- /frontend
- /components
- /pages

## Project Stack
- React
- TypeScript
- Vite
- Tailwind CSS

## Project Structure
- frontend/package.json
- frontend/src/App.tsx
- frontend/src/services/api.ts
- frontend/src/types/index.ts

## Team Rules
- Only edit files inside your owned folders unless explicitly instructed.
- Match agreed contracts exactly.
- Do not silently invent API shapes.

## Source Member
- Name: Maya
- Role: Frontend
- Branch: member/maya-ui
- Folder: /frontend

## Completed Work
- Frontend API client implemented
- Type definitions created for Project, Task, AuthResponse

## Detected Frontend Expectations
- GET /api/projects
- POST /api/auth
- GET /api/tasks

## Types / Data Shapes
- Project
- Task
- AuthResponse
- ApiResponse

## Mock Data
- frontend/src/mocks/userFixture.json

## Environment Variables
- VITE_API_BASE_URL

## Handoff
- TODO: Integrate authentication flow
- FIXME: Handle token expiration

## Files Included for Verification
- frontend/src/services/api.ts
- frontend/src/types/index.ts`;
