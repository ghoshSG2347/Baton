# Baton V1 Backend Integration Contract

## 1. Document Purpose

`BACKEND_CONTEXT.md` is the authoritative frontend/backend technical integration contract for **Baton V1**.

Its purpose is to define precisely what the Baton backend provides to frontend consumers (such as the Baton Mission Control frontend built in Bolt.new or standard React/Vite environments), how to invoke its endpoints, what data models to expect, and what operational constraints apply.

### Document Hierarchy

When building or consuming the Baton system, three core documents work in synergy:

1. **`BATON_Master_Solution_Blueprint.md`**: Defines the overall product vision, system architecture, workflow definitions, user personas, and feature intentions for Baton.
2. **`BACKEND_CONTEXT.md` (This Document)**: Defines the frozen, currently implemented technical capabilities, HTTP API endpoints, request/response schemas, error contracts, and runtime boundaries of the Baton V1 backend.
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
│  - FastAPI / Python (Stateless)                         │
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
- **No Embedded LLM**: Baton does **not** host, run, or call an internal LLM. It generates structured context and prompts to be handed off to external LLMs (e.g., Claude, ChatGPT, Cursor, Windsurf) by the user or client.
- **Read-Only Operation**: Baton does **not** push commits, create pull requests, alter branches, or modify repository contents.

---

## 3. V1 Architecture

The Baton V1 backend is designed for zero-state reliability, speed, and simple horizontal scaling:

- **Framework**: FastAPI on Python 3.11+.
- **Stateless Execution**: Every request is standalone. The backend does not maintain sessions, persistent storage, or historical logs.
- **GitHub Client**: Asynchronous HTTP client via `httpx.AsyncClient` communicating directly with `https://api.github.com`.
- **Deterministic Pattern Extraction**: Regex and static AST-like matching across file contents (no arbitrary code execution).
- **No Database**: No PostgreSQL, MySQL, SQLite, MongoDB, or ORM layers.
- **No Message Broker / Background Workers**: No Redis, Celery, BullMQ, or long-running worker pools.
- **No Repository Execution**: Repository code is treated as untrusted text and is never executed, imported, or evaluated.

### What Statelessness Means for the Frontend

Because the backend does not persist data:
- The backend does **not** store user accounts or profiles.
- The backend does **not** persist project history, previous analysis runs, or saved prompts.
- The backend does **not** retain uploaded files or GitHub tokens across requests.
- The frontend is responsible for retaining client-side session state, user preferences, and in-flight workflows in memory or client-side storage (e.g., `localStorage`).

---

## 4. Backend Project Structure

The actual frozen structure of the `baton-backend-v1` codebase is as follows:

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
  *(Note: `branch` is optional and defaults to `""` which resolves to `HEAD` on GitHub).*

---

### Analysis Response Shape (Full Schema)

Both analysis endpoints return the exact same structured analysis JSON object:

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
    "languages": ["json", "markdown", "typescript"]
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
| `metadata.commit` | Git commit SHA of the tree snapshot. | GitHub Git Tree response SHA. |
| `metadata.generated` | ISO-8601 UTC timestamp of analysis. | Timestamp at execution. |
| `metadata.files_analyzed` | Number of files read and inspected. | Read counter. |
| `metadata.skipped_files` | List of file paths omitted due to size limit, count limit, or read errors. | Filter / exception tracker. |
| `stack.detected` | Recognized frameworks/platforms (`React`, `TypeScript`, `Python`, `Node.js`, `Python dependencies`). | Extension & key file heuristics. |
| `stack.languages` | Sorted list of detected programming/data languages. | File extensions. |
| `file_tree` | Filtered list of relevant tree items (`path`, `type`, `size`). | Git tree after `is_relevant` filtering. |
| `important_files` | Key architectural files (`package.json`, `requirements.txt`, `pyproject.toml`, `README.md`, `main.py`, `App.tsx`, `App.jsx`). | Path filename matching. |
| `routes` | Server routes detected in Python/Node files (`"<path>: <route>"`). | Regex `(app\|router).(get\|post\|put\|patch\|delete)`. |
| `api_calls` | Client HTTP endpoints called (`"<path>: <endpoint>"`). | Regex `fetch(...)` or `axios.<method>(...)`. |
| `environment_variables` | Environment variables referenced in code. | Regex `process.env.VAR` or `os.environ['VAR']`. |
| `types` | TypeScript interfaces and type aliases detected. | Regex `interface Name` or `type Name`. |
| `mock_data` | Mock data files and test fixtures. | Paths or contents matching `mock`, `fixture`, `fake`, `dummyData`. |
| `handoffs` | Code markers requiring attention (`path` and matched `items`). | Lines containing `handoff`, `TODO`, `FIXME`. |
| `shared_files` | Shared file collisions (initialized as `[]`). | Analyzer container. |
| `stray_files` | Uncategorized or out-of-structure files (initialized as `[]`). | Analyzer container. |
| `analysis_warnings` | Informational warnings (e.g. omitted files or empty folder). | Omission / empty check. |

---

## 12. File Filtering and Analysis Limits

To protect memory and stay within GitHub API budgets, Baton applies deterministic filtering and strict limits.

### Active Limits (from Configuration)

- `MAX_FILE_SIZE_BYTES`: **200,000 bytes** (~200 KB). Files exceeding this size are skipped.
- `MAX_FILES_PER_ANALYSIS`: **100 files**. The backend reads at most 100 eligible files per analysis request.
- `MAX_TOTAL_CONTEXT_BYTES`: **2,000,000 bytes** (~2 MB). The maximum byte length of generated Markdown context before truncation.

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

Runs repository/folder analysis and formats the structured results into an optimized, standardized Markdown context document ready for ingestion by coding agents.

- **Request Body**:
  ```json
  {
    "owner": "my-org",
    "repo": "my-repo",
    "branch": "main",
    "folder": "",
    "include_markdown": true
  }
  ```
- **Response Shape** (`200 OK`):
  ```json
  {
    "analysis": {
      /* Full structured analysis JSON object */
    },
    "markdown": "# Baton Context\n> Baton Repository Context\n\n## Source\n- Repository: my-org/my-repo\n- Branch: main\n- Commit: 6809b645...\n- Generated: 2026-10-04T12:00:00+00:00\n\n## Requesting Member\n- Name: Not configured\n- Role: Not configured\n- Owns: Not configured\n\n## Do Not Touch\n- No ownership boundaries configured\n\n## Project Stack\n- React\n- TypeScript\n\n## Project Structure\n- package.json\n- src/App.tsx\n\n## Team Rules\n- No team rules supplied\n\n## Source Member\n- Not configured\n\n## Completed Work\n- Deterministic repository scan completed\n\n## Detected Frontend Expectations\n- User\n- ApiResponse\n\n## Routes\n- app/api/routes/users.py: /api/users\n\n## API Calls\n- src/services/api.ts: /api/users\n\n## Types / Data Shapes\n- User\n- ApiResponse\n\n## Mock Data\n- src/mocks/userFixture.json\n\n## Environment Variables\n- DATABASE_URL\n\n## Handoff\n- src/App.tsx\n\n## Shared Files\n- None detected\n\n## Possible Integration Issues\n- None detected\n\n## Stray / Out-of-structure Files\n- None detected\n\n## Not Detected\n- Ownership configuration, contracts, and recent commit subjects were not supplied to this request.\n\n## Files Included for Verification\n- package.json\n- src/App.tsx",
    "estimated_tokens": 420,
    "omitted": []
  }
  ```

### Key Context Properties

- **`markdown`**: Complete structured Markdown formatted with standard Baton sections.
- **`estimated_tokens`**: Deterministic estimation calculated as `len(text) // 4`. (Note: This is an approximation for context budgeting, not an exact BPE tokenizer count).
- **`omitted`**: Array of strings noting any omitted files or notifications if context was truncated to fit `MAX_TOTAL_CONTEXT_BYTES`.

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

1. **Treat the Backend as Completely Stateless**: Do not assume the backend stores projects, users, or results. Manage active workspace state in frontend state/storage.
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
| **Background Jobs / Webhooks** | ❌ Not in Backend | No | Stateless request-response only. |
| **Real-Time WebSockets** | ❌ Not in Backend | No | Standard HTTP REST API. |

---

## 20. What the Backend Does NOT Own

The following responsibilities belong exclusively to the frontend client and external workflows:

- **User Interface & Visual Design**: Component layout, dark/light themes, animations, glassmorphism, responsive navigation.
- **Client State & Persistence**: Retaining active repositories, custom prompt history, team member rosters, and user preferences in `localStorage` or IndexedDB.
- **Clipboard Interactions**: Copying generated context or prompts to the user's clipboard.
- **External AI Execution**: Sending generated prompts to Anthropic Claude, OpenAI ChatGPT, Cursor, Windsurf, or custom LLM endpoints.
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
4. **No Secret Leakage**: The backend never returns server environment variables or the server-side `GITHUB_TOKEN` in response payloads.

---

## 22. V1 Limitations

- **Stateless**: No server-side session, history, or caching across requests.
- **Read-Only**: No Git write or push support.
- **Deterministic Pattern Matching**: Route and type extractors use regex patterns rather than full multi-file compiler AST semantic analysis.
- **Analysis Bounds**: Maximum 100 files analyzed per run; maximum 200 KB per individual file.
- **Supported Provider**: Public or token-authenticated `github.com` repositories only (no GitLab, Bitbucket, or self-hosted GitHub Enterprise Server in V1).
- **Text Files Only**: Binary files (images, audio, archives, compiled binaries) are filtered and cannot be analyzed.

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
