# Baton V1 Backend Integration Contract

> Current implementation reference (2026-10-06): [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md) and [PROJECT_AUDIT.md](../PROJECT_AUDIT.md). This V1 contract is historical: the backend now has process-local intelligence snapshots, GitHub observations and conversations, canonical context projections and a Gemini workspace. Use the canonical API inventory and storage/freshness model for current integration work.

## 1. Document Purpose

`BACKEND_CONTEXT.md` is the authoritative frontend/backend technical integration contract for **Baton V1**.

Its purpose is to define precisely what the Baton backend provides to frontend consumers (such as the Baton Mission Control frontend built in Bolt.new or standard React/Vite environments), how to invoke its endpoints, what data models to expect, and what operational constraints apply.

### Document Hierarchy

When building or consuming the Baton system, three core documents work in synergy:

1. **`BATON_Master_Solution_Blueprint.md`**: Defines the overall product vision, system architecture, workflow definitions, user personas, and feature intentions for Baton.
2. **`BACKEND_CONTEXT.md` (This Document)**: Defines the currently implemented technical capabilities, HTTP API endpoints, request/response schemas, error contracts, and runtime boundaries of the Baton V1 backend.
3. **Frontend / UI Design Prompt**: Defines the visual layout, typography, interaction patterns, design tokens, animations, and component behavior for the user interface.

> [!IMPORTANT]
> **Precedence Rule for Frontend Builders (e.g. Bolt.new):**
> - The Master Blueprint defines **WHAT** Baton is conceptually.
> - This contract defines **WHAT** the backend actually supports in V1.
> - The UI prompt defines **HOW** the frontend looks and feels.
> - If the Master Blueprint describes a broad product concept (e.g., persistent user sessions, database history, team management, or automated Git push operations) that is not supported by the V1 backend, the frontend **must not invent or fake backend APIs**. The frontend must consume only what is documented in this contract and handle any client-only state locally.

---

## 2. Baton V1 Backend Role

The Baton V1 backend operates as a high-speed, deterministic context preparation and coordination engine positioned between the frontend interface and GitHub's REST API:

```text
┌─────────────────────────────────────────────────────────┐
│              Baton Frontend / Mission Control           │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP / JSON
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    Baton V1 Backend                     │
│  - FastAPI / Python + bounded snapshot reuse                         │
│  - Deterministic Analyzers & Pattern Extractors         │
│  - Context, Prompt & Coordination Generators            │
└────────────────────────────┬────────────────────────────┘
                             │ Read-only HTTPS (HTTPX)
                             ▼
┌─────────────────────────────────────────────────────────┐
│                  GitHub REST API v3                     │
│  - Public or authenticated repository inspection        │
└─────────────────────────────────────────────────────────┘
```

### System Boundaries and Core Responsibilities

- **Deterministic Coordination**: The backend extracts structure, frameworks, routes, API calls, types, environment variables, mock fixtures, and handoff markers from repository snapshots.
- **Context Synthesis**: It formats structured analysis data into clean, token-budgeted Markdown context packets ready for injection into external coding agents.
- **Prompt Formulation**: It assembles standardized task prompts adhering to Baton coordination rules.
- **Optional Server AI**: Part 3 adds a backend-only Gemini evidence selector. Baton validates selections and renders factual answers from canonical context records. No model is hosted locally and no provider credentials reach the frontend. See section 27.
- **Read-Only Operation**: Baton does **not** push commits, create pull requests, alter branches, or modify repository contents.

---

## 3. V1 Architecture

The Baton V1 backend uses request-scoped GitHub access and bounded process-local intelligence reuse:

- **Framework**: FastAPI on Python 3.11+.
- **Request-Scoped Access**: No sessions or durable project storage. Sanitized intelligence snapshots may be reused from a bounded in-memory store after a fresh GitHub authorization and commit check.
- **GitHub Client**: Asynchronous HTTP client via `httpx.AsyncClient` communicating directly with `https://api.github.com`.
- **Deterministic Pattern Extraction**: Regex and static AST-like matching across file contents (no arbitrary code execution).
- **No Database**: No PostgreSQL, MySQL, SQLite, MongoDB, or ORM layers.
- **No Message Broker / Background Workers**: No Redis, Celery, BullMQ, or long-running worker pools.
- **No Repository Execution**: Repository code is treated as untrusted text and is never executed, imported, or evaluated.

### What Process-Local Reuse Means for the Frontend

Because the backend has no durable storage:
- The backend does **not** store user accounts or profiles.
- The backend does **not** persist project history or saved prompts. Process-local snapshot reuse is an optimization, not durable project history.
- The backend does **not** retain uploaded files or GitHub tokens across requests.
- The frontend is responsible for retaining client-side session state, user preferences, and in-flight workflows in memory or client-side storage (e.g., `localStorage`).

---

## 4. Backend Project Structure

The original route/service structure remains compatible. Section 25 describes the canonical intelligence modules added to this structure:

```text
baton-backend-v1/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app setup, CORS, route registration, error handlers
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                 # Dependency injection (token resolution)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py           # Health check endpoints (/health, /api/health)
│   │       ├── github.py           # GitHub validation, branches, tree, and file endpoints
│   │       ├── analysis.py         # Folder and repository analysis endpoints
│   │       ├── context.py          # Markdown context generation endpoint
│   │       ├── prompt.py           # Prompt assembly endpoint
│   │       ├── conflicts.py        # Path-overlap conflict detection endpoint
│   │       └── integration.py      # Dual-branch endpoint integration comparison
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── api_analyzer.py         # Express/FastAPI routes, fetch/axios calls, env vars
│   │   ├── frontend_analyzer.py    # TypeScript types/interfaces, mock fixture detection
│   │   ├── handoff_analyzer.py     # Handoff markers, TODO/FIXME extraction
│   │   ├── repository_analyzer.py  # Aggregator for repository analysis
│   │   ├── stack_analyzer.py       # Framework & language identification
│   │   └── structure_analyzer.py   # File tree mapping & important file detection
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic BaseSettings & environment variables
│   │   ├── exceptions.py           # BatonError custom exception and JSON handler
│   │   └── security.py             # X-Baton-Key operator access verification
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── context_generator.py    # Structured Markdown context builder & budget trimmer
│   │   └── prompt_generator.py     # Task prompt generator
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── analysis.py             # Pydantic request models for folder/repo analysis
│   │   ├── conflict.py             # Pydantic request model for conflict detection
│   │   ├── context.py              # Pydantic request model for context generation
│   │   ├── github.py               # Pydantic models for GitHub operations
│   │   ├── integration.py          # Pydantic request model for integration analysis
│   │   ├── prompt.py               # Pydantic request model for prompt generation
│   │   └── team.py                 # Pydantic team member model
│   └── utils/
│       ├── __init__.py
│       ├── file_filters.py         # Exclusion lists, ignore patterns, binary checks
│       ├── text_utils.py           # Language inference, line extraction, string truncation
│       └── token_budget.py         # Token estimation (~4 chars/token) and byte fitting
├── tests/
│   ├── __init__.py
│   ├── test_analysis.py            # Analyzer deterministic output & filter tests
│   ├── test_conflicts.py           # Conflict detection unit tests
│   ├── test_context.py             # Markdown context generator & byte trimming tests
│   ├── test_health.py              # Health check, X-Baton-Key, and token precedence tests
│   ├── test_integration.py         # Dual-branch comparison & endpoint normalization tests
│   └── test_prompt.py              # Prompt generation unit tests
├── .env.example                    # Configuration template
├── render.yaml                     # Render deployment specification
├── requirements.txt                # Python dependencies
└── BACKEND_CONTEXT.md              # Authoritative integration contract (this file)
```

---

## 5. Deployment and Base URL

### Local Development

- **Default Backend URL**: `http://localhost:8000`
- **Default Frontend Port**: `http://localhost:5173` (configured as default in `FRONTEND_ORIGINS`)

### Production (Render)

The backend is deployed independently as a Render Web Service running `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

### Frontend Configuration Convention

The frontend must **never hardcode** the backend URL in components. It should read the backend base URL from its environment configuration:

- Example convention (Vite): `import.meta.env.VITE_BATON_API_URL`
- Fallback: `http://localhost:8000`

```typescript
// Example frontend API client setup
const BASE_URL = import.meta.env.VITE_BATON_API_URL || 'http://localhost:8000';
```

---

## 6. CORS / Frontend Access

Cross-Origin Resource Sharing (CORS) is managed via FastAPI's `CORSMiddleware` in `app/main.py`:

- **Configuration Key**: `FRONTEND_ORIGINS` (comma-separated list of allowed origins).
- **Default Value**: `http://localhost:5173`.
- **Allowed Methods**: `["*"]` (GET, POST, OPTIONS, etc.).
- **Allowed Headers**: `["*"]` (including `Content-Type`, `X-Baton-Key`, `X-GitHub-Token`).
- **Credentials**: `allow_credentials=False` (no cookies or ambient credentials are required).

For production deployments, the frontend's hosting domain (e.g., `https://my-baton-app.onrender.com` or `https://my-app.vercel.app`) must be added to the backend's `FRONTEND_ORIGINS` environment variable on Render.

---

## 7. Authentication / Request Headers

The backend supports two optional request headers:

```text
┌────────────────────────────────────────────────────────┐
│                   Incoming HTTP Request                │
│                                                        │
│  X-Baton-Key: <operator-key>                           │  ──► Checked against BATON_ACCESS_KEY
│  X-GitHub-Token: <personal-access-token>               │  ──► Overrides GITHUB_TOKEN for GitHub API
│  Content-Type: application/json                        │
└────────────────────────────────────────────────────────┘
```

### 1. `X-Baton-Key` (Shared Operator Access Gate)

`X-Baton-Key` is an optional shared operator access key for restricting backend access to authorized deployments or clients.

- **Not User Auth**: It is **not** a user login system, does not generate JWTs, and does not represent individual user identities.
- **Behavior**:
  - If the backend environment variable `BATON_ACCESS_KEY` is **empty or unset**: All endpoints are open; no key is required.
  - If `BATON_ACCESS_KEY` is **set**: All endpoints (except `/health` and `/api/health`) require the header `X-Baton-Key: <key>`. Requests missing or providing an invalid key receive `HTTP 401 Unauthorized` with `{"detail": "Invalid or missing X-Baton-Key"}`.
- **Frontend Handling**: The frontend should read this value from its own environment config (e.g. `VITE_BATON_ACCESS_KEY`) if configured, and attach it to API requests.

### 2. `X-GitHub-Token` (Request-Scoped GitHub Token)

Used to authenticate requests to the GitHub REST API for private repositories or to avoid GitHub's unauthenticated rate limits (60 requests/hr).

- **Token Precedence**:
  ```text
  1. Header: X-GitHub-Token (per request)
     ↓ (if not provided)
  2. Backend Environment: GITHUB_TOKEN (server-side fallback)
     ↓ (if not set)
  3. Unauthenticated GitHub API Call (subject to 60 req/hr public rate limit)
  ```
- **Security & Privacy**:
  - Request tokens are ephemeral, request-scoped, and never saved to disk or logs.
  - The frontend must **never expose or attempt to read the server-side `GITHUB_TOKEN`**.
  - If the user provides a Personal Access Token (PAT) in the frontend UI, the frontend passes it via the `X-GitHub-Token` header.

---

## 8. Complete API Reference

All routes return JSON. Non-health routes are prefixed with `/api/v1`.

### Summary Table

| Method | Path | Summary | Auth Required (`X-Baton-Key`) | GitHub Token Supported (`X-GitHub-Token`) |
|---|---|---|---|---|
| `GET` | `/health` | Service health status check | No | No |
| `GET` | `/api/health` | Service health alias (used by Render) | No | No |
| `POST` | `/api/v1/github/validate-repository` | Validates GitHub repo URL & access | If `BATON_ACCESS_KEY` set | Yes |
| `GET` | `/api/v1/github/branches` | Lists up to 100 branches for a repo | If `BATON_ACCESS_KEY` set | Yes |
| `GET` | `/api/v1/github/tree` | Returns recursive Git tree items | If `BATON_ACCESS_KEY` set | Yes |
| `GET` | `/api/v1/github/file` | Reads and decodes a single text file | If `BATON_ACCESS_KEY` set | Yes |
| `POST` | `/api/v1/analysis/folder` | Analyzes a specific directory in a branch | If `BATON_ACCESS_KEY` set | Yes |
| `POST` | `/api/v1/analysis/repository` | Analyzes the entire repository root | If `BATON_ACCESS_KEY` set | Yes |
| `POST` | `/api/v1/context` | Generates structured Markdown context & token estimate | If `BATON_ACCESS_KEY` set | Yes |
| `POST` | `/api/v1/prompt` | Generates a formatted coding task prompt | If `BATON_ACCESS_KEY` set | No |
| `POST` | `/api/v1/conflicts` | Detects shared-file overlaps across branches | If `BATON_ACCESS_KEY` set | No |
| `POST` | `/api/v1/integration` | Compares frontend API calls with backend routes | If `BATON_ACCESS_KEY` set | Yes |

---

## 9. Health Endpoints

Both health endpoints are always public and do not enforce `X-Baton-Key`.

### `GET /health` and `GET /api/health`

- **Purpose**: Verify that the backend service is running and responsive.
- **Render Configuration**: `render.yaml` designates `/api/health` as the active `healthCheckPath`.
- **Request**: No headers or body required.
- **Response Shape** (`200 OK`):
  ```json
  {
    "status": "ok",
    "service": "baton-backend"
  }
  ```

---

## 10. GitHub API Endpoints

All GitHub endpoints perform **read-only** queries against `https://api.github.com`.

### 1. `POST /api/v1/github/validate-repository`

Validates that a URL is a valid `github.com` repository and checks accessibility.

- **Request Body**:
  ```json
  {
    "repo_url": "https://github.com/owner/repository"
  }
  ```
- **Response Shape** (`200 OK`):
  ```json
  {
    "owner": "owner",
    "repository": "repository",
    "default_branch": "main",
    "visibility": "public",
    "accessible": true
  }
  ```
- **Failure Conditions**:
  - Invalid URL structure: `400 Bad Request` (`{"detail": "repo_url must be a public github.com owner/repository URL"}`)
  - Repository not found or inaccessible: `404 Not Found` (`{"detail": "Not Found"}`)

---

### 2. `GET /api/v1/github/branches`

Retrieves the list of branches for a repository (up to 100 branches).

- **Query Parameters**:
  - `owner` (string, required): Repository owner / organization.
  - `repo` (string, required): Repository name.
- **Response Shape** (`200 OK`):
  ```json
  {
    "branches": [
      {
        "name": "main",
        "sha": "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d"
      },
      {
        "name": "feature/api",
        "sha": "4a2c8901e9d8f3310009c91f422894b94f1122aa"
      }
    ]
  }
  ```

---

### 3. `GET /api/v1/github/tree`

Retrieves the recursive Git tree, filtered optionally by a subpath.

- **Query Parameters**:
  - `owner` (string, required)
  - `repo` (string, required)
  - `branch` (string, required)
  - `path` (string, optional, default `""`): Subdirectory prefix to filter items.
- **Response Shape** (`200 OK`):
  ```json
  {
    "items": [
      {
        "path": "src/App.tsx",
        "type": "blob",
        "size": 1420,
        "sha": "95a12f..."
      },
      {
        "path": "src/components",
        "type": "tree",
        "size": null,
        "sha": "88d31a..."
      }
    ]
  }
  ```

---

### 4. `GET /api/v1/github/file`

Fetches and decodes the UTF-8 content of a single file from GitHub.

- **Query Parameters**:
  - `owner` (string, required)
  - `repo` (string, required)
  - `branch` (string, required)
  - `path` (string, required)
- **Response Shape** (`200 OK`):
  ```json
  {
    "path": "src/App.tsx",
    "size": 1420,
    "content": "import React from 'react';\n\nexport function App() {\n  return <div>Hello World</div>;\n}\n",
    "language": "typescript"
  }
  ```
- **Failure Conditions**:
  - Path is a directory: `400 Bad Request` (`{"detail": "Requested path is not a file"}`)
  - Binary file or decode failure: `400 Bad Request` (`{"detail": "Binary files are not supported"}`)
  - File size exceeds limit (`MAX_FILE_SIZE_BYTES` = 200,000 bytes): `413 Payload Too Large` (`{"detail": "File exceeds configured size limit"}`)
  - Not found: `404 Not Found`

---

## 11. Repository Analysis API

The analysis pipeline performs deterministic pattern matching across eligible files in a repository or folder:

```text
GitHub Tree Snapshot
         ↓
File Filtering (Exclude node_modules, .git, lockfiles, binary files)
         ↓
Eligible File Loading (Bounded by MAX_FILES_PER_ANALYSIS & MAX_FILE_SIZE_BYTES)
         ↓
Pattern Analyzers (Stack, Structure, Routes, API Calls, Types, Mock Data, Handoffs)
         ↓
Structured Analysis JSON
```

### 1. `POST /api/v1/analysis/folder`

Analyzes a specific folder within a branch.

- **Request Body**:
  ```json
  {
    "owner": "facebook",
    "repo": "react",
    "branch": "main",
    "folder": "packages/react"
  }
  ```

### 2. `POST /api/v1/analysis/repository`

Analyzes the entire repository (equivalent to calling folder analysis with `folder: ""`).

- **Request Body**:
  ```json
  {
    "owner": "facebook",
    "repo": "react",
    "branch": "main"
  }
  ```
  *(Note: `branch` is optional and defaults to `""`; collection resolves the repository default branch before resolving its commit.)*

---

### Analysis Response Shape (Legacy Fields)

Both analysis endpoints return the same compatible fields below, plus additive `canonical_api` endpoint/consumer records. Existing clients may continue using the legacy fields:

```json
{
  "metadata": {
    "owner": "my-org",
    "repo": "my-project",
    "branch": "main",
    "folder": "",
    "commit": "6809b645b20cb37d0c37107775988d8b1392e21b",
    "generated": "2026-10-04T12:00:00.000000+00:00",
    "files_analyzed": 14,
    "skipped_files": [
      "src/assets/large_graphic.png",
      "data/large_dataset.json"
    ]
  },
  "stack": {
    "detected": ["React", "TypeScript", "Node.js"],
    "languages": ["TypeScript"]
  },
  "file_tree": [
    {
      "path": "package.json",
      "type": "blob",
      "size": 520
    },
    {
      "path": "src/App.tsx",
      "type": "blob",
      "size": 1200
    }
  ],
  "important_files": [
    "package.json",
    "README.md",
    "src/App.tsx"
  ],
  "routes": [
    "app/api/routes/users.py: /api/users"
  ],
  "api_calls": [
    "src/services/api.ts: /api/users"
  ],
  "environment_variables": [
    "DATABASE_URL",
    "PORT"
  ],
  "types": [
    "User",
    "UserProfile",
    "ApiResponse"
  ],
  "mock_data": [
    "src/mocks/userFixture.json"
  ],
  "handoffs": [
    {
      "path": "src/App.tsx",
      "items": [
        "// TODO: Integrate authentication flow",
        "// FIXME: Handle token expiration"
      ]
    }
  ],
  "shared_files": [],
  "stray_files": [],
  "analysis_warnings": [
    "2 relevant files were omitted by analysis limits or could not be read."
  ]
}
```

### Analysis Field Explanations

| Field | Description | Extraction Method |
|---|---|---|
| `metadata.owner` | Repository owner. | Request payload. |
| `metadata.repo` | Repository name. | Request payload. |
| `metadata.branch` | Branch analyzed. | Request payload. |
| `metadata.folder` | Scope folder analyzed (`""` for full repo). | Request payload. |
| `metadata.commit` | Exact Git commit SHA; never a Git tree SHA. | GitHub commit resolution before all file reads. |
| `metadata.generated` | ISO-8601 UTC timestamp of analysis. | Timestamp at execution. |
| `metadata.files_analyzed` | Number of files read and inspected. | Read counter. |
| `metadata.skipped_files` | All known files whose content was omitted (filters, secrets, limits, or read failures). | Canonical completeness projection. |
| `stack.detected` | Recognized frameworks/platforms (`React`, `TypeScript`, `Python`, `Node.js`, `Python dependencies`). | Extension & key file heuristics. |
| `stack.languages` | Sorted list of detected programming/data languages. | File extensions. |
| `file_tree` | Full returned inventory within analysis scope (`path`, `type`, `size`, `sha`, `mode`), including omitted-file metadata. | Commit-pinned Git tree; truncation is explicitly reported. |
| `important_files` | Key architectural files (`package.json`, `requirements.txt`, `pyproject.toml`, `README.md`, `main.py`, `App.tsx`, `App.jsx`). | Path filename matching. |
| `routes` | Server routes as `source_file: METHOD /path`. | Projection of canonical API declarations and supported literal mounts. |
| `api_calls` | Client HTTP endpoints called (`"<path>: <endpoint>"`). | Regex `fetch(...)` or `axios.<method>(...)`. |
| `environment_variables` | Environment variables referenced in code. | Regex `process.env.VAR` or `os.environ['VAR']`. |
| `types` | TypeScript interfaces and type aliases detected. | Regex `interface Name` or `type Name`. |
| `mock_data` | Mock data files and test fixtures. | Paths or contents matching `mock`, `fixture`, `fake`, `dummyData`. |
| `handoffs` | Code markers requiring attention (`path` and matched `items`). | Lines containing `handoff`, `TODO`, `FIXME`. |
| `shared_files` | Shared file collisions (initialized as `[]`). | Analyzer container. |
| `stray_files` | Root-level file paths retained for legacy consumers; this is not evidence of architectural defects. | Canonical structure projection. |
| `analysis_warnings` | Informational warnings (e.g. omitted files or empty folder). | Omission / empty check. |

---

## 12. File Filtering and Analysis Limits

To protect memory and stay within GitHub API budgets, Baton applies deterministic filtering and strict limits.

### Active Limits (from Configuration)

- `MAX_FILE_SIZE_BYTES`: **200,000 bytes** (~200 KB). Files exceeding this size are skipped.
- `MAX_FILES_PER_ANALYSIS`: **100 file-read attempts**. Failures consume the budget too; a file is never fetched twice during one collection.
- `MAX_TOTAL_CONTEXT_BYTES`: **2,000,000 bytes** (~2 MB). Both total collected UTF-8 content and generated Markdown are bounded by this setting. Metadata-only inventory remains available for omitted files.

### Excluded Directories, Files, and Extensions

1. **Ignored Directories**:
   `node_modules`, `.git`, `dist`, `build`, `coverage`, `__pycache__`, `.venv`, `venv`, `assets`
2. **Ignored Filenames**:
   `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
3. **Binary Extensions**:
   `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.ico`, `.pdf`, `.zip`, `.woff`, `.woff2`, `.ttf`, `.mp3`, `.mp4`, `.mov`, `.exe`, `.bin`

### Frontend Guidance for Skipped Files

The frontend should check `analysis.metadata.skipped_files` and `analysis.analysis_warnings`. If files are omitted, the frontend UI should present an indicator informing the user that the analysis represents a bounded subset of the repository.

---

## 13. Context Generation

### `POST /api/v1/context`

Projects an authorized, current canonical snapshot into a detailed briefing. It never collects a tree, reads repository files, invokes an LLM or calls analysis. Explicitly run the repository/folder analysis endpoint first. Missing, stale, wrong-version or differently scoped snapshots return HTTP 409 with: "The repository intelligence snapshot is unavailable/stale and must be refreshed."

The existing owner/repo/branch/folder/include_markdown fields remain supported. New fields are optional; the default context type is `project`.

```json
{
  "owner": "my-org",
  "repo": "my-repo",
  "branch": "main",
  "folder": "",
  "context_type": "role",
  "member": {
    "name": "Developer",
    "role": "Frontend Developer",
    "responsibilities": ["Maintain the Ask Book interface"],
    "ownership": ["client/"],
    "do_not_touch": ["server/", "shared/"],
    "team_scope": ["client/"]
  },
  "task": "Inspect the existing Ask Book integration",
  "constraints": ["Preserve existing request contracts"],
  "max_bytes": 100000,
  "include_markdown": true
}
```

An optional `commit` asserts the expected current branch SHA; a mismatch returns 409. Blank branch resolves the repository default branch. Valid context types are `project`, `role`, `task`, `ai_handoff`; invalid types return 422. `max_bytes` must be at least 1024 and is capped by `MAX_TOTAL_CONTEXT_BYTES`. Impossible Markdown budgets return 413, rather than a successful but unusable implementation briefing.

Responses retain `analysis`, `markdown`, `estimated_tokens`, `omitted` and add `context`. `analysis` is the full legacy projection of the same canonical snapshot, including additive canonical API records. `context` contains identity, completeness, USER member/task configuration, relevance/boundaries, `usable`, a categorized omission manifest and section record metadata. Markdown contains 20 sections (see section 26). `estimated_tokens` uses the existing approximate character-count method, not a tokenizer. With `include_markdown:false`, Markdown is empty and its token estimate is zero; structured completeness/omissions remain available, including `usable:false` for an insufficient briefing budget.

---

## 14. Prompt Generation

### `POST /api/v1/prompt`

Assembles an external coding agent prompt combining a user's task, context, and operational constraints.

- **Request Body**:
  ```json
  {
    "task": "Implement user authentication endpoint in FastAPI",
    "context": "Backend uses FastAPI with Pydantic v2.",
    "constraints": [
      "Do not modify files outside app/api/routes/auth.py",
      "Do not add external dependencies without approval"
    ]
  }
  ```
- **Response Shape** (`200 OK`):
  ```json
  {
    "prompt": "You are working on the Baton repository.\n\nTask:\nImplement user authentication endpoint in FastAPI\n\nConstraints:\n- Do not modify files outside app/api/routes/auth.py\n- Do not add external dependencies without approval\n\nRepository context:\nBackend uses FastAPI with Pydantic v2."
  }
  ```
- **Frontend Usage**: The resulting prompt string is displayed in the UI for one-click copying to the clipboard or passing to an external AI workflow. The backend does not execute the prompt.

---

## 15. Conflict Detection

### `POST /api/v1/conflicts`

Calculates path overlaps across branches or team file assignments.

- **Request Body**:
  ```json
  {
    "files": [],
    "branches": {
      "feature/frontend-auth": [
        "src/App.tsx",
        "src/services/api.ts",
        "package.json"
      ],
      "feature/backend-auth": [
        "app/api/routes/auth.py",
        "package.json"
      ]
    }
  }
  ```
- **Response Shape** (`200 OK`):
  ```json
  {
    "conflicts": [
      {
        "path": "package.json",
        "branches": [
          "feature/frontend-auth",
          "feature/backend-auth"
        ],
        "reason": "shared file changed by multiple branches"
      }
    ],
    "conflict_count": 1
  }
  ```
- **Meaning of "Conflict"**: In Baton V1, conflict detection represents **shared-file coordination overlap**. It identifies where multiple branches or tasks touch identical file paths. It is **not** a Git 3-way merge engine and does not inspect line-level diffs.

---

## 16. Integration Analysis

### `POST /api/v1/integration`

Performs endpoint-level contract comparison between two branches (e.g. a frontend branch making API calls and a backend branch exposing server routes).

### 1. Dual-Branch Comparison (Both Branches Provided)

When both `frontend_branch` and `backend_branch` are provided in the payload:
1. The backend analyzes `frontend_branch` using `AnalysisService` and extracts frontend API calls (`api_calls` or `routes`).
2. The backend analyzes `backend_branch` using `AnalysisService` and extracts backend routes (`routes` or `api_calls`).
3. Source-file prefixes (such as `src/api.ts: ` or `app/routes.py: `) are stripped and endpoints are normalized.
4. It compares the sets of endpoints and identifies matched vs. unmatched routes.

- **Request Body**:
  ```json
  {
    "owner": "my-org",
    "repo": "my-project",
    "branch": "main",
    "frontend_branch": "feature/frontend-ui",
    "backend_branch": "feature/backend-api"
  }
  ```
- **Response Shape** (`200 OK`):
  ```json
  {
    "owner": "my-org",
    "repo": "my-project",
    "branch": "main",
    "status": "analyzed",
    "comparison": {
      "frontend_routes": [
        "GET /api/v1/users",
        "POST /api/v1/login"
      ],
      "backend_routes": [
        "GET /api/v1/users",
        "POST /api/v1/login",
        "GET /health"
      ],
      "unmatched_frontend_routes": [],
      "unmatched_backend_routes": [
        "GET /health"
      ],
      "compatible": true
    }
  }
  ```

### 2. Single-Branch / Readiness State (Branches Omitted)

If either `frontend_branch` or `backend_branch` is missing:

- **Response Shape** (`200 OK`):
  ```json
  {
    "owner": "my-org",
    "repo": "my-project",
    "branch": "main",
    "status": "ready",
    "message": "Provide frontend_branch and backend_branch to run a real integration comparison."
  }
  ```

### Scope of V1 Integration Comparison

- **What it does**: Compares normalized HTTP route paths and methods (e.g. `GET /api/users`) between frontend and backend.
- **What it does NOT do**: It does **not** validate JSON request/response body schemas, TypeScript types against Pydantic models, query parameter types, database constraints, or semantic AI compatibility.

---

## 17. Error Contract

All errors return standard JSON with a `"detail"` string or validation structure.

### Error Status Codes

| Status Code | Reason | Example Response Body |
|---|---|---|
| `400 Bad Request` | Invalid repository URL, non-file path request, or binary file requested. | `{"detail": "repo_url must be a public github.com owner/repository URL"}` |
| `401 Unauthorized` | Missing or invalid `X-Baton-Key` (when `BATON_ACCESS_KEY` is configured). | `{"detail": "Invalid or missing X-Baton-Key"}` |
| `404 Not Found` | Repository, branch, or file does not exist on GitHub. | `{"detail": "Not Found"}` |
| `413 Payload Too Large` | Requested file exceeds `MAX_FILE_SIZE_BYTES` (200 KB). | `{"detail": "File exceeds configured size limit"}` |
| `422 Unprocessable Entity` | Pydantic request body validation failure. | `{"detail": [{"loc": ["body", "task"], "msg": "Field required", "type": "missing"}]}` |
| `429 Too Many Requests` | GitHub API rate limit reached. | `{"detail": "API rate limit exceeded for user..."}` |
| `502 Bad Gateway` | Network error or timeout contacting GitHub API. | `{"detail": "GitHub request failed: [Errno 110] Connection timed out"}` |

### Frontend Error Handling Rules

1. Always inspect `response.status` and parse `response.json().detail`.
2. Differentiate between:
   - **Operator key errors (`401`)**: Prompt user to check the configured `X-Baton-Key`.
   - **GitHub access errors (`404` / `429`)**: Prompt user to provide a GitHub Personal Access Token via `X-GitHub-Token`.
   - **Size limit errors (`413`)**: Notify user that the requested file exceeds the 200 KB limit.
   - **Network/Upstream errors (`502`)**: Surface a clean retry prompt.

---

## 18. Frontend Integration Rules

When building the Baton frontend, follow these strict development rules:

1. **Keep Workspace State in the Client**: Do not assume durable backend project storage. Bounded process-local snapshot reuse does not replace client state.
2. **Do Not Invent Nonexistent APIs**: Do not invent `/api/v1/auth/login`, `/api/v1/projects/save`, `/api/v1/teams/update`, or `/api/v1/git/commit`.
3. **Use a Centralized API Client**: Encapsulate all backend HTTP communication in a dedicated service layer (e.g. `src/services/batonApi.ts`).
4. **Pass Environment-Driven Base URLs**: Read backend URL from `import.meta.env.VITE_BATON_API_URL` (or equivalent) rather than hardcoding `http://localhost:8000`.
5. **Attach Required Headers Consistently**: Include `X-Baton-Key` and `X-GitHub-Token` when configured.
6. **Support All Five UI States**: Every asynchronous view must gracefully handle:
   - *Idle / Uninitialized*
   - *Loading / Processing*
   - *Success / Data Loaded*
   - *Partial / Skipped Files Warning*
   - *Error / Retry*
7. **Handle Skipped Files Explicitly**: When `metadata.skipped_files` or `analysis_warnings` are non-empty, inform the user clearly in the UI.
8. **Treat Markdown and Context as Data**: Render Markdown using safe Markdown renderers (e.g. `react-markdown` with syntax highlighting). Never evaluate context strings as executable JavaScript.
9. **Never Expose Private Server Secrets**: Do not attempt to query or log backend environment variables from the client.

---

## 19. Backend Capability Matrix

This matrix clarifies what is implemented in Baton V1 vs. what is a future vision or client-only concern:

| Capability | Backend V1 Status | Frontend May Use Now? | Implementation Details / Notes |
|---|---|---|---|
| **Repository Validation** | ✅ Supported | Yes | `POST /api/v1/github/validate-repository` |
| **Branch Listing** | ✅ Supported | Yes | `GET /api/v1/github/branches` |
| **Tree Inspection** | ✅ Supported | Yes | `GET /api/v1/github/tree` |
| **File Reading** | ✅ Supported | Yes | `GET /api/v1/github/file` (UTF-8, ≤ 200 KB) |
| **Folder Analysis** | ✅ Supported | Yes | `POST /api/v1/analysis/folder` |
| **Repository Analysis** | ✅ Supported | Yes | `POST /api/v1/analysis/repository` |
| **Context Generation** | ✅ Supported | Yes | `POST /api/v1/context` |
| **Prompt Assembly** | ✅ Supported | Yes | `POST /api/v1/prompt` |
| **Conflict Detection** | ✅ Supported | Yes | `POST /api/v1/conflicts` (Path overlap) |
| **Dual-Branch Integration** | ✅ Supported | Yes | `POST /api/v1/integration` (Route comparison) |
| **Operator Access Key** | ✅ Supported | Yes | Optional `X-Baton-Key` header |
| **User Accounts / Login** | ❌ Not in Backend | Client-side only if needed | No user tables or auth endpoints exist in V1. |
| **Persistent Project Storage** | ❌ Not in Backend | Client-side only (localStorage) | Backend does not retain past analyses. |
| **Team Management API** | ❌ Not in Backend | Client-side state | Schema exists for types, but no DB CRUD endpoints. |
| **GitHub OAuth Flow** | ❌ Not in Backend | Client/PAT based | Frontend passes user PAT via `X-GitHub-Token`. |
| **Git Write / Commit / PR** | ❌ Not Supported | No | Baton is strictly read-only. |
| **LLM Execution / Chat API** | ❌ Not Supported | No | Baton outputs prompts/context for external LLMs. |
| **Background Jobs / Webhooks** | ❌ Not in Backend | No | Request-response only; no scheduled workers. |
| **Real-Time WebSockets** | ❌ Not in Backend | No | Standard HTTP REST API. |

---

## 20. What the Backend Does NOT Own

The following responsibilities belong exclusively to the frontend client and external workflows:

- **User Interface & Visual Design**: Component layout, dark/light themes, animations, glassmorphism, responsive navigation.
- **Client State & Persistence**: Retaining active repositories, custom prompt history, team member rosters, and user preferences in `localStorage` or IndexedDB.
- **Clipboard Interactions**: Copying generated context or prompts to the user's clipboard.
- **External Coding Workflows**: Users can copy/export prompts to their tools. Integrated Gemini selection is exclusively a backend responsibility; the browser never calls a provider.
- **Git Write Operations**: Staging, committing, pushing, or opening PRs via local Git CLI or external tools.

---

## 21. Security and Trust Boundary

```text
┌─────────────────────────────────────────────────────────┐
│               Untrusted Browser / Client                │
└────────────────────────────┬────────────────────────────┘
                             │ Untrusted Inputs (Repo URLs, Branch Names)
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    Baton V1 Backend                     │
│  - Never executes repository code                       │
│  - Bounded string scanning & regex                      │
│  - File size & count limits enforced                    │
└────────────────────────────┬────────────────────────────┘
                             │ Read-Only Queries
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   GitHub Public/Private                 │
└─────────────────────────────────────────────────────────┘
```

1. **Repository Code Is Untrusted**: The backend treats all file contents returned from GitHub as untrusted text. It never runs `eval()`, `exec()`, or sub-processes on repository files.
2. **Frontend XSS Prevention**: The frontend must sanitize and safely render repository text, file trees, and Markdown.
3. **Token Safety**: GitHub tokens passed via `X-GitHub-Token` are held only in request memory and discarded after request completion.
4. **Secret Handling**: Request and server GitHub tokens are removed from collected content before findings are built. Sensitive files are omitted; environment template values and recognizable credential patterns are redacted. GitHub errors use generic text and never echo remote messages or tokens. No raw source archive is retained. See Section 25 for the limits of heuristic redaction.

---

## 22. V1 Limitations

- **No Durable State**: No server-side sessions or durable history. In-memory snapshots are local to a worker, evicted when bounded capacity is reached, and lost on restart/deploy.
- **Read-Only**: No Git write or push support.
- **Deterministic Pattern Matching**: Route and type extractors use regex patterns rather than full multi-file compiler AST semantic analysis.
- **Analysis Bounds**: Maximum 100 file-read attempts, 200,000 bytes per file, and 2,000,000 collected UTF-8 bytes per run. Omitted files and GitHub tree truncation are recorded.
- **Supported Provider**: Public or token-authenticated `github.com` repositories only (no GitLab, Bitbucket, or self-hosted GitHub Enterprise Server in V1).
- **Static Text Analysis**: Binary/model artifacts may be classified from metadata, but are never executed or deserialized. Notebook code cells are parsed as text; notebook outputs are not retained.

---

## 23. Non-Goals

The following are explicitly **non-goals** for Baton V1 and must not be implemented or assumed:

- A multi-tenant user authentication and billing system.
- A database-backed project management platform.
- An automated GitHub write bot or PR merging tool.
- An embedded LLM code generation or agent execution runtime.
- A full-featured online IDE or code editor.
- A CI/CD build runner or automated test executor.

---

## 24. Frontend Quick Reference

### Base URL
- Local: `http://localhost:8000`
- Production: Environment-configured URL (e.g. `VITE_BATON_API_URL`)

### Headers
- `X-Baton-Key`: Optional operator access key (required if backend `BATON_ACCESS_KEY` is set).
- `X-GitHub-Token`: Optional GitHub Personal Access Token (for private repos and higher rate limits).
- `Content-Type`: `application/json`

### Route Cheatsheet

```text
HEALTH:
GET  /health                                 -> {"status":"ok","service":"baton-backend"}
GET  /api/health                             -> {"status":"ok","service":"baton-backend"}

GITHUB:
POST /api/v1/github/validate-repository      -> Body: {"repo_url":"https://github.com/o/r"}
GET  /api/v1/github/branches?owner=&repo=    -> Response: {"branches":[{"name":"...","sha":"..."}]}
GET  /api/v1/github/tree?owner=&repo=&branch=&path= -> Response: {"items":[{"path":"...","type":"..."}]}
GET  /api/v1/github/file?owner=&repo=&branch=&path= -> Response: {"path":"...","size":...,"content":"...","language":"..."}

ANALYSIS:
POST /api/v1/analysis/folder                 -> Body: {"owner":"...","repo":"...","branch":"...","folder":"..."}
POST /api/v1/analysis/repository             -> Body: {"owner":"...","repo":"...","branch":"..."}

CONTEXT & PROMPT:
POST /api/v1/context                         -> Body: {"owner":"...","repo":"...","branch":"...","folder":"","include_markdown":true}
POST /api/v1/prompt                          -> Body: {"task":"...","context":"...","constraints":["..."]}

COORDINATION & INTEGRATION:
POST /api/v1/conflicts                       -> Body: {"files":[],"branches":{"b1":["f1"],"b2":["f1"]}}
POST /api/v1/integration                     -> Body: {"owner":"...","repo":"...","branch":"...","frontend_branch":"...","backend_branch":"..."}
```


## 25. Canonical Repository Intelligence (Part 1)

### Architecture and consumers

`AnalysisService.analyze_intelligence()` is the internal entry point. `app/intelligence/pipeline.py` produces the single `RepositoryIntelligence` dataclass in `models.py`. `RepositoryAnalyzer` and legacy stack, API, frontend-type and handoff entry points now delegate to canonical analysis rather than maintaining conflicting interpretations. Existing analysis/context routes still return compatible projections. Part 1 did not redesign context presentation or prompt generation. Part 2 context behavior is specified in sections 13 and 26.

There is no mandatory LLM, repository execution, database, vector store, Redis, Celery or GitHub write operation. FastAPI, token precedence, CORS and Render configuration are preserved. Future Part 2 consumers should use the canonical model, not reconstruct facts from legacy strings.

### Schema

| Area | Canonical fields |
|---|---|
| Exact state | `owner`, `repo`, `branch`, `commit`, `generated`, `analysis_version`, `project_root`, `snapshot_status`, `repository_metadata` |
| Identity and intent | `project_identity`, `project_summary`, `documentation_sources`, `documentation_content`, `repository_rules`, `requirements` |
| Technologies | `project_types`, `project_type_evidence`, `languages`, `technologies`, `package_dependencies`, `package_scripts` |
| Structure | `file_tree`, `parsed_files`, `directory_classifications`, `components` |
| Relationships and contracts | `dependencies`, `resolved_dependencies`, `data_flows`, `api_endpoints`, `api_consumers`, `types`, `data_models` |
| Data and operations | `data_sources`, `env_variables`, `config_files`, `tests_detected`, deployment findings |
| Truth and coverage | `evidence`, confidence on findings, `conflicts`, `unknowns`, `risks`, `missing_work`, `analysis_warnings`, `completeness`, `user_overrides` |

Snapshots retain the returned scoped file inventory with blob SHA/size/mode, sanitized documentation and parsed structural representations rather than complete source. Documentation references include both commit and blob SHA. File structures include symbols, line numbers, imports, entrypoints, parse status and evidence-based ML stage tags. Python uses `ast.parse`; other languages use bounded patterns. Java/Kotlin package/method and SQL table extraction are foundations, not a compiler-level type system.

`EvidenceStatus` separates DOCUMENTED, OBSERVED, DERIVED, INFERRED, UNKNOWN, CONFLICTING and RECOMMENDED. Requirements are always DOCUMENTED; code evidence is stored separately. Directory classifications are labeled INFERRED with evidence/confidence. Components are DERIVED from classified paths. No recommendations are generated by the core pipeline.

### Discovery and classification

Documentation is discovered first from exact and semantic filenames, documentation paths, nested AGENTS/CLAUDE files, `.builder`, `.cursor`, `.github` instruction files and `.mdc` rules. Dependency `requirements*.txt` files are not mistaken for product requirements. Unrecognized Markdown receives a documentation role. Sanitized document text remains available beyond the legacy excerpt.

Projects may have multiple types: frontend, backend/API, full-stack, ML, data science/pipeline, research, library/SDK, CLI, scripting/automation, mobile, desktop, embedded, game, infrastructure, documentation-only or unknown. Languages derive from file metadata/manifests, and technologies from dependencies/imports/configuration. Documentation, source comments and Python docstrings are excluded from observed technology/code detection. A directory called `backend` containing React is classified by its React/TSX evidence, not its name. Single-file and root components are included; competing evidence is AMBIGUOUS, absent evidence UNKNOWN. Shared domain paths require resolved imports from both frontend and backend consumers.

Deployment findings distinguish actual configuration file presence from explicit documented deployment statements; a platform mention alone does not establish a deployment plan. No deployment or workflow execution is verified.

The semantic map includes directories through three nesting levels and significant files through parsed structures. There is no requirement that a frontend, backend, API or database exists. ML files may identify dataset loading, preprocessing, training, model definitions, evaluation and inference independently. Data sources distinguish datasets, artifacts, fixtures, seeds, static consumed data, configuration and unknown structured files. Detected stage patterns do not prove a complete ML pipeline.

### Intent versus reality and anti-hallucination

Requirements retain explicit text, source section/line, identifiers and priority when supplied. Bullets, numbered lists and modal prose are extracted; fenced code examples are excluded. Matching searches observed symbols and endpoint declarations, never documentation text as implementation.

Unmatched requirements are NOT_DETECTED, not proof they are unimplemented. Symbol matches are PARTIALLY_IMPLEMENTED candidates with LOW confidence, not certification of behavior. Only narrow literal requirements of the form `Expose GET /health.` can be marked IMPLEMENTED from the matching declaration; this confirms endpoint exposure only. No feature-completion percentages are computed. Explicit conflicting claims are preserved without resolving them by guessing.

API declarations and consumers share `ApiEndpoint`. Methods, source files, supported handler/request/response/type references, normalized paths, callers, evidence and confidence are retained. Query/trailing slashes and equivalent parameter forms normalize; path case is preserved. Known literal FastAPI/Express mounts are resolved through local imports. Matching respects methods. External calls are distinguished from local routes. Frontend-only repositories do not automatically receive missing-backend conflicts.

Contradictions include unmatched local API consumers when server declarations exist, present-tense documentation/framework claims versus collected code, documented API mismatches and mechanically opposite instructions. Future/planned statements are not treated as proof of an implementation conflict. Missing evidence can reflect bounded collection; conflict records preserve that uncertainty.

### Snapshot store, authorization and staleness

`SnapshotStore` defines `save`, `load`, `exists`, `invalidate` and `metadata`. `MemorySnapshotStore` is the V1 implementation, injectable into `AnalysisService`. Keys include normalized owner/repository, branch (case-sensitive), exact commit, folder scope and analysis version. Loads/saves return or retain defensive copies. Old analysis versions and unknown commits cannot be reused. Invalidation can target repository, branch, commit or folder. Compatibility module functions remain available.

The default store holds at most 20 entries and approximately 40,000,000 serialized snapshot bytes; Python object overhead is additional. Old entries are evicted in insertion order. Metadata does not include tokens or secret values. Storage is process-local: instances/workers do not share it, and restarts/deployments erase it. Durable cross-instance reuse requires a future storage adapter; no database migration is introduced here.

Every service request resolves the current commit through GitHub with that request's authorization, even before a cache hit. A Git tree SHA is never used as a commit identity. Cache misses fetch the tree and each selected file at the resolved commit, avoiding a moving-branch race. A changed HEAD triggers fresh analysis and a warning; an old commit is never silently returned as the new state. Explicit stale retrieval returns a copied STALE view and does not mutate the historical snapshot. Partial snapshots remain labeled PARTIAL after caching. Empty repositories without a resolvable commit yield uncached PARTIAL intelligence.

### Limits, security and omissions

All three existing collection limits are enforced before and after UTF-8 decoding where applicable. Documentation precedes manifests/config and other files in collection priority. Failed read attempts consume the count budget. Filtering removes content, not inventory metadata. Completeness records known discovered/read/omitted counts, omitted paths, per-file reasons, critical omissions and GitHub tree truncation. A truncated tree is never described as a complete inventory.

Sensitive `.env` files, private keys and known credential files are omitted. Templates retain variable names only. Known request/server token values, recognizable token formats, bearer credentials, credential URLs, private-key blocks and secret assignments are redacted before excerpts, requirements, TODOs, parsed structures or snapshots are created. Environment required/optional status defaults to unknown unless established. No tokens are stored as model fields, logged, or echoed in GitHub errors. Authorization failures abort collection rather than caching misleading results.

Repository instructions are untrusted findings, never commands for the server to execute. Python parsing, JSON/TOML parsing and notebook cell inspection do not import modules, execute scripts, evaluate expressions or load models. A parsed-file representation is not full source and does not contain notebook outputs.

Heuristic redaction cannot recognize every possible secret concealed under an innocuous name or in arbitrary prose. Do not treat snapshots as an audited secret-scanning product. Raw source is deliberately not archived; recognizable secrets and supplied tokens are covered by regression tests.

### Validation and remaining limits

Run `python -B -m pytest -q -p no:cacheprovider` from `baton-backend-v1`. Fixtures include spec-only, README-only, ML, frontend-only, backend-only, BookOS-style, mixed-language, scripts and ambiguous directories. Tests cover rules, requirements, API mismatches, literal mounts, shape references, data relationships, source provenance, save/load/copy/isolation/eviction/staleness, collection budgets, authorization on cache hits, secrets, empty states and no source/notebook execution. Existing route/token/context/prompt/conflict/integration regressions remain in the suite.

Extraction is intentionally conservative. Dynamic routes, nested/aliased mounts, compiler type resolution, semantic feature equivalence, runtime behavior, test coverage and general natural-language contradictions are not established. Non-Python symbol patterns may miss declarations or see source-like text. Missing code is never proof of absence. Part 1 did not build chat, role-context UI, final context presentation or PRD generation. Part 2 adds the context projection documented below; chat and PRD generation remain outside this phase.


## 26. Detailed Context System (Part 2)

### Flow and source of truth

`ContextService` loads through `ContextSnapshotService`, then calls `context_generator.generate(RepositoryIntelligence, ...)`. The canonical dispatch delegates to `context_builder.build`; direct legacy-dictionary library callers retain their old compatibility formatter, which the API never uses. There is one canonical builder for all views. No new AI infrastructure or frontend redesign is introduced.

The loader authorizes each request through GitHub commit resolution before reading the process-local store. It verifies repository, branch, commit, folder and analysis version, refuses stale snapshots, and permits explicitly labeled partial ones. Existing explicit analysis requests may refresh intelligence; context requests never do so. Restarts, eviction or requests reaching a different worker can require explicit analysis because Part 1 storage remains process-local. No durable context or member history is added.

### Views and USER boundaries

Project context includes the scoped inventory. Role/task/AI handoff views seed relevance from USER ownership/team scope, canonical semantic classifications and deterministic task-to-path/symbol/stage/requirement label matches. Relevance matches are INFERRED, never new architectural or feature facts. Unrecognized roles, unmatched scopes or absent task matches fall back to project context with UNKNOWN relevance and an explicit warning. Team scope is not ownership.

Connected files are retained through canonical resolved imports, API callers, related types and data consumers. Closure is bidirectional so shared producers and downstream consumers are visible. This may produce a broad slice in tightly connected projects; it deliberately does not hide cross-boundary dependencies. Directory names alone do not classify a role. Arbitrary roles and duties remain USER statements. Selection does not infer ownership from commit history, tasks or classifications.

Ownership accepts repository-relative file paths, directory prefixes and case-sensitive glob patterns. Backslashes in supplied scopes normalize to slashes. Do-not-touch takes precedence over overlapping ownership. Protected files remain readable in the briefing but are excluded from modification targets. A file must match an explicit ownership scope and no protection scope to become a modification target. Missing ownership says "Ownership configuration was not provided." This is guidance metadata, not a Git/file-write permission enforcement system; the context endpoint performs no writes to repositories.

USER overrides show original classification, corrected value, reason and provenance. They can inform relevance without mutating the canonical observed classification. Project-wide identity, documented requirements, implementation statuses, rules, conflicts and unknowns stay shared across views.

### Markdown structure

1. Context Identity: exact snapshot identity, timestamps, version, view and USER boundaries.
2. Context Completeness: retained collection counts, document/map/comparison coverage, critical omissions, impact and view relevance.
3. Project Identity: categories, languages, tools, evidence and conservative maturity.
4. Product / Project Purpose: quoted author intent, observed characterization and explicitly unknown semantic consistency.
5. Source-of-Truth Documents: roles, authority, scope, important headings, requirement origins and commit/blob provenance.
6. Requirements: every extracted requirement, source/priority, intent, canonical comparison/evidence/confidence/gaps and associated selected paths.
7. Implementation Status: shared status counts and feature-by-feature documented-versus-observed comparison.
8. Canonical Architecture: components, classified responsibilities, local import edges and recorded relationships.
9. Component Map: important source symbols/lines, inputs/outputs, dependencies/dependents, API dependencies, parse status and ownership.
10. Repository Structure: semantic paths, responsibilities/classifications, confidence, evidence and corrections.
11. APIs and Shared Contracts: retained methods/routes, shapes/type references, callers, type fields and boundaries.
12. Data Sources and Processing: categories, consumers, metadata-only artifacts and independently detected ML stages.
13. Dependencies and Integration Constraints: manifest declarations and contracts to preserve.
14. Configuration and Verification: environment names/purpose/required status, scripts, detected tests and verification limits.
15. Deployment and Operational Constraints: observed configuration separate from documented deployment.
16. Role, Duties, Ownership and Rules: USER duties/scopes, modification targets, protected cross-boundary files and scoped repository instructions.
17. Developer Guidance and Next Work: USER task/constraints and investigations derived only from documented requirements/gaps.
18. Conflicts, Risks and Unknowns: both claims/sources, recorded resolution, omissions and analysis/relevance limitations.
19. Evidence, Confidence and Omissions: provenance, references, source omissions/reasons and files outside the selected view.
20. AI Handoff Guidance: explicit task/boundary/evidence/integration/unknown-handling instructions for external coding agents.

Coverage counts have explicit denominators and no invented completion percentages. A complete collection does not establish complete functionality. Document coverage means retained bodies; architecture coverage means classified directory-map entries, not verified runtime topology. Requirement coverage reflects recorded comparisons and uncertainty, not a new semantic reconciliation. PARTIAL snapshot status is preserved. Non-detected implementation remains NOT_DETECTED. Legacy NOT_STARTED/NOT_DETECTABLE/difference statuses receive conservative display labels while the original canonical status remains visible. Purpose equivalence is UNKNOWN; unrelated canonical conflicts are not falsely labeled purpose contradictions.

### Budgets, omissions and safety

The UTF-8 budget applies to rendered Markdown after redaction. Whole supporting records are removed in priority order. Identity, boundaries, shared contracts, rules, conflicts, uncertainty, source omissions and AI guidance are mandatory. Budget omissions identify section and record in Markdown and carry source paths/reason in the structured manifest. Snapshot collection omissions, view relevance exclusions and context budget exclusions are distinct categories. Omitted evidence is never described as complete. If mandatory content cannot fit, direct builder callers receive `usable:false` / INCOMPLETE; API requests for Markdown return 413.

Request/server GitHub tokens and recognizable secret assignments are redacted from USER configuration as well as Markdown. HTML is escaped and text Markdown metacharacters are escaped to keep supplied text from forging briefing headings. Source paragraphs/rules are displayed as evidence, not executed instructions. No source imports, scripts, notebooks, model loads, LLM calls or deployments occur in this phase.

### Small canonical extension and remaining limits

Part 2 needed retained TypeScript property declarations for shared contracts. The Part 1 structural parser now retains simple flat interface/type properties, annotations and optional flags under `field_extraction:flat_declared_properties_only`. Nested/computed/generic/method shapes remain unknown; there is no compiler-level type resolution. Existing older snapshots without fields continue to show UNKNOWN until explicitly refreshed. The builder never parses raw source to fill this gap.

Unrecorded signatures, request/response fields, business responsibilities, runtime control flow and test success stay UNKNOWN. File-level caller associations are explicitly distinguished from per-call bindings. Suggestions investigate recorded gaps; no normal-seeming product features are added. The prompt endpoint is unchanged. Role configuration is per request; no persistence UI, chatbot, retrieval system or Part 3 implementation is included.

Validation: `python -B -m pytest -q -p no:cacheprovider`; see `PART2_VALIDATION_REPORT.md` for results and scope.


## 27. Repository AI Workspace (Part 3)

### Architecture and provider security

Browser ? Baton backend ? configured Gemini endpoint. `AIProvider` is the small selection interface; `GeminiProvider` implements it with existing httpx, without a new SDK dependency. No provider existed before this phase. The adapter uses Google's documented `generateContent` REST interface, `systemInstruction` and JSON-schema selections. Official references: https://ai.google.dev/api/generate-content and https://ai.google.dev/gemini-api/docs/structured-output.

`GEMINI_API_KEY` is a backend SecretStr, excluded from settings serialization/repr. `GEMINI_MODEL` must be supplied in the deployment environment and is validated as a model identifier. No model or credential is supplied by the browser. Authentication uses the `x-goog-api-key` header, never URL parameters or prompt text. Redirects are disabled; the provider host is fixed. Timeout (default 45 seconds), output tokens (default 2000), response size and four concurrent calls are bounded. Requests are not silently retried. Errors never include provider response bodies, headers or exception strings.

`secret_values` extends existing redaction to configured provider/operator secrets. Collection and snapshot storage redact retained model strings/paths; context and workspace inputs/outputs are sanitized. `SafeJSONResponses` filters configured/request secrets from JSON responses across all API routes and limits buffered response size. Validation failures return a generic 422 instead of echoing input. Recognizable Gemini credentials are also redacted. This remains heuristic hygiene rather than a full secret-scanning product.

Chat requires a configured `BATON_ACCESS_KEY` and matching `X-Baton-Key`, in addition to authorized GitHub snapshot loading. Existing endpoints retain optional operator authentication for compatibility. The browser operator key is entered in settings and held in memory; its previous public `VITE_BATON_ACCESS_KEY` binding has been removed. `X-GitHub-Token` remains request-scoped with server fallback. Both keys are excluded from browser persistence. No browser field, environment binding or API response exposes the provider key.

### API contract

All workspace routes use existing `ContextRequest` fields (owner/repo/branch/folder, optional expected commit, view, member, task, constraints and budget). Unknown additional fields are rejected. Defaults use `ai_handoff`; the UI chooses project/role/task based on its explicit scope. Server `AI_CONTEXT_BYTES` (default 120000) caps the requested context budget; the existing total context limit still applies. `include_markdown` is always enabled internally to require a usable briefing.

| Endpoint | Additional input | Result |
|---|---|---|
| `POST /api/v1/workspace/inspect` | None | Identity, completeness, member/task, relevance, sections/evidence records, omissions, Markdown and provider-configured boolean |
| `POST /api/v1/workspace/chat` | `message` (1?8000 chars), optional 32-hex `conversation_id` | Grounded/unknown/out_of_scope status, canonical answer excerpts, citations, bounded actions, identity/coverage/omissions, conversation ID/revision |
| `POST /api/v1/workspace/artifacts` | `artifact_type` | Markdown content, safe filename, SHA256, identity, completeness and omissions |
| `POST /api/v1/workspace/compare` | `compare_branch`, optional `compare_commit` | Two exact identities, coverage, inventory-only differences, changed/unknown blob paths, retained API contract differences and protected changes |

Workspace consumers call Part 2 `ContextService`. They do not call analysis or raw GitHub file/tree collection. Part 2 section metadata now exposes included evidence records with stable per-view IDs, original text and source paths; no second context builder is introduced. Missing/stale/changed/wrong-scope snapshots return 409 and require explicit analysis. Each request authorizes current repository state. A supplied commit asserts current HEAD, not historical checkout support.

### Strict chatbot semantics

The provider selects IDs from supplied current context records and optional typed actions (`inspect`, `verify`, `resolve_conflict`). It cannot return free-form answers, invented features, arbitrary code, tool calls or external factual claims. Extra output fields, nonexistent evidence IDs, grounded answers without evidence, inconsistent statuses, and actions outside selected evidence/explicit ownership fail closed with 502. Protected sources can be quoted for understanding but cannot become action targets. Conflict actions require a retained conflict record.

Baton renders factual answer content from the selected original context excerpts, retaining DOCUMENTED/OBSERVED/DERIVED/INFERRED/UNKNOWN labels. Model selection is a relevance judgment, not new truth: it can select an irrelevant record, but cannot author an unsupported factual assertion. Unknown and outside-scope responses use fixed explicit messages. General conversation, browsing, code execution and automatic repository modifications are not provider capabilities. Recommendations are bounded investigations and never executed changes.

### Conversations, artifacts and comparison

Conversation state is process-local, expires after one hour, holds at most 100 entries and 20 turns each, and stores sanitized questions plus evidence IDs/actions rather than full source answers. Random identifiers are bound with process-keyed HMAC to authorization, repository, branch, commit, folder, analysis identity, view and USER role/task/constraints. Changed bindings/expired state return 409. Optimistic revisions reject concurrent conflicting writes. No credentials are stored as conversation fields. Previous user questions are context data, not implementation evidence. The UI starts fresh on scope/auth/repository/branch/folder changes and preserves applied duties when only the branch changes.

Artifacts: `context`, `handoff`, `prd`, `implementation_plan`, `review`, `prompt`. Context is the existing Markdown; other drafts select existing briefing sections and preserve identity, completeness, USER task/duties/boundaries, uncertainty and omissions. Coding prompts reuse the existing prompt formatter with the connected repository identity and require an explicit USER task. Artifact generation is deterministic and does not spend provider quota. PRD output is an evidence draft of documented intent, not invented requirements. Investigation plans are not generated patches or automatic implementation. No artifact database or server-side repository write is introduced.

Branch comparison loads two independently authorized existing snapshots for the same repository/folder. It compares recorded blob SHAs and retained API declaration shapes/types. Missing SHAs remain unknown; inventory-only differences are not automatically called deleted/unimplemented. Protection scopes apply across the full compared inventories, even outside the selected relevance view. Results do not certify runtime compatibility, perform a Git merge, resolve conflicts, create branches, commit or open a PR.

### Deployment and operation

1. Configure `GEMINI_API_KEY`, `GEMINI_MODEL` (an available model supporting JSON-schema generateContent), and a private `BATON_ACCESS_KEY` in the backend deployment environment. Render declares these with `sync:false`, never values. Do not put secrets in VITE variables, repository files, logs or browser storage.
2. Set frontend `VITE_BATON_API_URL` to the backend URL. Enter the Baton access key in workspace settings, and an appropriate GitHub token when connecting a private repository.
3. Connect/select the repository and branch. Use **Refresh analysis** explicitly. Workspace inspection, chat, artifact and comparison requests thereafter consume the cached canonical snapshots.
4. Add/select a developer in Team & Ownership. Apply optional task/protection/constraints in workspace scope settings. Analyze both branches explicitly before comparing them.

Without provider configuration, artifacts/context/comparison still work with authorized snapshots; chat reports 503 instead of simulating an AI reply. Multiple workers, eviction and restarts can invalidate both snapshots and conversations; V1 has no durable/shared store. The stop button stops browser waiting; it does not promise cancellation of a billable upstream request. Live provider behavior/quota depends on deployment configuration and was not exercised without a key.

Validation and preview details: `PART3_VALIDATION_REPORT.md`.
