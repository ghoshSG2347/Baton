# Baton Backend Context

## 1. Document purpose

This document is the technical handoff for the Baton V1 backend. It explains the purpose of the service, the implemented architecture, every source area, the HTTP API, request and response behavior, GitHub access, security assumptions, analyzers, generators, deployment configuration, testing, and known limitations.

The backend is designed to sit between a Mission Control frontend and GitHub:

```text
Mission Control frontend
        |
        | HTTP/JSON
        v
Baton backend
        |
        | Read-only GitHub REST API calls
        v
GitHub repository
```

Baton performs deterministic repository inspection and context preparation. It does **not** use an LLM and does not write to GitHub.

---

## 2. Implementation status

The V1 implementation is complete for the supplied specification and contains:

- A stateless FastAPI application.
- Optional shared-key protection for all non-health endpoints.
- Read-only GitHub REST API integration using `httpx`.
- Request-level GitHub token support through `X-GitHub-Token`.
- Repository URL validation restricted to `github.com`.
- Branch, tree, and file inspection endpoints.
- Folder and repository analysis endpoints.
- Deterministic stack, structure, API, frontend, and handoff analysis.
- Markdown context generation with byte and token estimates.
- Prompt generation for downstream AI coding workflows.
- Basic shared-file conflict detection.
- Basic integration-contract comparison utilities.
- CORS configuration for a separately deployed frontend.
- Render deployment configuration.
- Pytest coverage for health, analysis, context, prompt, conflicts, and integration behavior.

The original supplied implementation prompt ended in the middle of the file-filtering section. Where later details were not available, behavior was implemented conservatively using small, deterministic JSON contracts rather than inventing a larger architecture.

---

## 3. Design principles

### 3.1 Stateless operation

The backend does not persist repositories, tokens, users, sessions, analysis results, or generated prompts. Each request performs its work and returns its result.

Benefits:

- No database is required for V1.
- No migration system is required.
- Temporary GitHub tokens are not stored.
- Render instances can be replaced without losing application state.
- The frontend remains responsible for any desired persistence.

### 3.2 Read-only GitHub access

Baton only reads repository metadata, branches, Git trees, and file contents. It does not expose operations that:

- Push commits.
- Create branches.
- Merge pull requests.
- Delete files or repositories.
- Modify issues, pull requests, or settings.
- Execute repository code.

### 3.3 Deterministic processing

The analyzers use ordinary Python text and path processing. They do not reason with an AI model. The output is intended to be supplied later to a user's preferred coding model or coding tool.

### 3.4 Treat repositories as untrusted input

The repository analyzer reads text returned by GitHub but never imports project modules, executes scripts, runs shell commands from the repository, or evaluates repository configuration as code.

### 3.5 Small, transparent dependencies

The backend uses FastAPI, Pydantic, Pydantic Settings, Uvicorn, HTTPX, and Pytest. It intentionally does not use LangChain, OpenAI SDKs, Anthropic SDKs, vector databases, Redis, Celery, or other unnecessary infrastructure.

---

## 4. Project structure

The workspace itself is the backend project root. It must not be nested inside another `backend/backend` directory.

```text
backend workspace/
|
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   │
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── github.py
│   │       ├── analysis.py
│   │       ├── context.py
│   │       ├── prompt.py
│   │       ├── conflicts.py
│   │       └── integration.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── exceptions.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── github.py
│   │   ├── team.py
│   │   ├── analysis.py
│   │   ├── context.py
│   │   ├── prompt.py
│   │   ├── conflict.py
│   │   └── integration.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── github_service.py
│   │   ├── analysis_service.py
│   │   ├── context_service.py
│   │   ├── prompt_service.py
│   │   ├── conflict_service.py
│   │   └── integration_service.py
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── repository_analyzer.py
│   │   ├── stack_analyzer.py
│   │   ├── structure_analyzer.py
│   │   ├── api_analyzer.py
│   │   ├── frontend_analyzer.py
│   │   └── handoff_analyzer.py
│   │
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── context_generator.py
│   │   └── prompt_generator.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── token_budget.py
│       ├── file_filters.py
│       └── text_utils.py
│
├── tests/
│   ├── __init__.py
│   ├── test_health.py
│   ├── test_analysis.py
│   ├── test_context.py
│   ├── test_prompt.py
│   ├── test_conflicts.py
│   └── test_integration.py
│
├── requirements.txt
├── .env.example
├── .python-version
├── render.yaml
└── BACKEND_CONTEXT.md
```

No database, models, repositories, controllers, middleware package, workers, queues, migrations, storage layer, or AI package is included.

---

## 5. Application wiring

### `app/main.py`

`app/main.py` is the application entrypoint. It:

1. Loads settings through `get_settings()`.
2. Creates the FastAPI application with title `Baton Backend` and version `1.0.0`.
3. Installs CORS middleware.
4. Registers the `BatonError` exception handler.
5. Includes the health, GitHub, analysis, context, prompt, conflict, and integration routers.

Business logic is not placed in `main.py`.

### Router prefixes

The health router exposes:

```text
GET /health
```

All business routers are under:

```text
/api/v1/
```

The current route groups are:

```text
/api/v1/github
/api/v1/analysis
/api/v1/context
/api/v1/prompt
/api/v1/conflicts
/api/v1/integration
```

---

## 6. Configuration

### `app/core/config.py`

Settings are defined with Pydantic Settings. Values are read from environment variables and, when available, a local `.env` file.

The configured fields are:

| Setting | Default | Purpose |
|---|---:|---|
| `BATON_ENV` | `development` | Runtime environment label. |
| `BATON_ACCESS_KEY` | empty | Optional shared key for non-health endpoints. |
| `GITHUB_TOKEN` | empty | Server-side GitHub token for private repository access. |
| `FRONTEND_ORIGINS` | `http://localhost:5173` | Comma-separated allowed frontend origins. |
| `MAX_FILE_SIZE_BYTES` | `200000` | Maximum individual file size read by the backend. |
| `MAX_TOTAL_CONTEXT_BYTES` | `2000000` | Maximum generated context size. |
| `MAX_FILES_PER_ANALYSIS` | `100` | Maximum number of file contents loaded during analysis. |

`FRONTEND_ORIGINS` is split on commas and trimmed before being passed to FastAPI's CORS middleware.

### `.env.example`

`.env.example` documents the expected environment variables without including secrets. A deployment should define real values through Render environment settings rather than committing a `.env` file.

Secrets must never be placed in:

- `BACKEND_CONTEXT.md`.
- Source code.
- Test fixtures.
- API responses.
- Git history.

---

## 7. Security model

### 7.1 Shared backend key

`app/core/security.py` contains the optional shared-key dependency:

```http
X-Baton-Key: <BATON_ACCESS_KEY>
```

Behavior:

- If `BATON_ACCESS_KEY` is empty, non-health endpoints are open for local development.
- If `BATON_ACCESS_KEY` is configured, every non-health router requires a matching `X-Baton-Key` header.
- A missing or incorrect value returns HTTP `401`.
- `/health` remains available without the key so Render can perform health checks.

This is intentionally a simple operator key. It is not a user-account system and does not implement users, registration, login, JWTs, OAuth, or sessions.

### 7.2 GitHub token precedence

GitHub access uses this precedence:

```text
X-GitHub-Token request header > GITHUB_TOKEN environment variable > no token
```

The request-level token is used only while handling that request. The service does not write it to a database or file and does not return it.

The server-side `GITHUB_TOKEN` is appropriate for a Render deployment that must inspect private repositories. For public repositories, GitHub can also be accessed without a token, subject to GitHub's unauthenticated rate limits.

### 7.3 URL validation

Repository validation accepts only URLs matching the `github.com/owner/repository` pattern over HTTP or HTTPS. GitLab, Bitbucket, arbitrary hosts, and GitHub Enterprise URLs are rejected.

The validation is deliberately restrictive to prevent the backend from being used as a generic HTTP proxy.

### 7.4 Untrusted repository contents

Repository file contents are treated as data. The backend does not:

- Import Python modules from the repository.
- Run Node, Python, shell, or build commands.
- Invoke package managers.
- Execute configuration files.
- Follow repository-provided commands.
- Interpret Markdown instructions as system instructions.

---

## 8. GitHub service

### `app/services/github_service.py`

`GitHubService` is a small asynchronous HTTP client around GitHub's REST API. It uses `httpx.AsyncClient` with a base URL of:

```text
https://api.github.com
```

Requests include:

```http
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

An authorization header is added only when a token is available:

```http
Authorization: Bearer <token>
```

The service translates HTTPX failures and GitHub error responses into `BatonError` responses for the API layer.

### GitHub operations

| Service method | GitHub operation | Purpose |
|---|---|---|
| `validate_repo_url` | Local validation | Extract owner and repository from a GitHub URL. |
| `repository` | `GET /repos/{owner}/{repo}` | Read repository metadata. |
| `branches` | `GET /repos/{owner}/{repo}/branches` | Read branch names and commit SHAs. |
| `tree` | `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1` | Read repository structure. |
| `file` | `GET /repos/{owner}/{repo}/contents/{path}?ref={branch}` | Read one text file. |

The service does not call GitHub mutation endpoints.

### File limits

The file endpoint checks the configured `MAX_FILE_SIZE_BYTES` value before returning content. Analysis applies both the individual file limit and `MAX_FILES_PER_ANALYSIS`.

Binary-looking extensions are rejected by the file filtering rules, and content decoding is UTF-8 based. Files that cannot be decoded as UTF-8 are treated as unsupported binary content.

---

## 9. HTTP API reference

All examples assume a local server at:

```text
http://localhost:8000
```

Start command:

```bash
uvicorn app.main:app --reload
```

If `BATON_ACCESS_KEY` is configured, add this header to all business requests:

```http
X-Baton-Key: <key>
```

### 9.1 Health

#### `GET /health`

Purpose: Render health checks and local availability checks.

Response:

```json
{
  "status": "ok",
  "service": "baton-backend"
}
```

This endpoint does not call GitHub and does not require a Baton access key.

---

### 9.2 Validate a repository

#### `POST /api/v1/github/validate-repository`

Request:

```json
{
  "repo_url": "https://github.com/owner/repository"
}
```

The backend first validates the host and path shape, then requests repository metadata from GitHub.

Successful response:

```json
{
  "owner": "owner",
  "repository": "repository",
  "default_branch": "main",
  "visibility": "public",
  "accessible": true
}
```

Notes:

- `default_branch` and `visibility` come from GitHub metadata.
- `accessible` is true only after the GitHub metadata request succeeds.
- Invalid repository URL shapes are rejected before any GitHub call.
- A private repository requires a token with sufficient read access.

---

### 9.3 List branches

#### `GET /api/v1/github/branches`

Query parameters:

| Parameter | Required | Description |
|---|---|---|
| `owner` | yes | GitHub repository owner or organization. |
| `repo` | yes | Repository name. |

Example:

```text
GET /api/v1/github/branches?owner=owner&repo=repository
```

Response:

```json
{
  "branches": [
    {
      "name": "main",
      "sha": "0123456789abcdef..."
    }
  ]
}
```

The service requests up to 100 branches in a single GitHub request.

---

### 9.4 Read the repository tree

#### `GET /api/v1/github/tree`

Query parameters:

| Parameter | Required | Description |
|---|---|---|
| `owner` | yes | GitHub repository owner or organization. |
| `repo` | yes | Repository name. |
| `branch` | yes | Branch or ref to inspect. |
| `path` | no | Optional folder prefix. |

Example:

```text
GET /api/v1/github/tree?owner=owner&repo=repository&branch=main&path=src
```

Response:

```json
{
  "items": [
    {
      "path": "src/main.py",
      "mode": "100644",
      "type": "blob",
      "sha": "...",
      "size": 1200,
      "url": "..."
    }
  ]
}
```

The tree endpoint returns structure metadata and does not download file contents. A `path` filter is applied after the recursive tree response is received.

---

### 9.5 Read a single file

#### `GET /api/v1/github/file`

Query parameters:

| Parameter | Required | Description |
|---|---|---|
| `owner` | yes | GitHub repository owner or organization. |
| `repo` | yes | Repository name. |
| `branch` | yes | Branch or ref. |
| `path` | yes | Repository-relative file path. |

Example:

```text
GET /api/v1/github/file?owner=owner&repo=repository&branch=main&path=package.json
```

Response:

```json
{
  "path": "package.json",
  "size": 512,
  "content": "{\"name\": \"example\"}",
  "language": "json"
}
```

The implementation reads the GitHub Contents API response, decodes Base64 content, rejects directories and unsupported binary content, and enforces the configured file-size limit.

---

### 9.6 Analyze a folder

#### `POST /api/v1/analysis/folder`

Request:

```json
{
  "owner": "example",
  "repo": "project",
  "branch": "member1-frontend",
  "folder": "frontend"
}
```

The service:

1. Reads the recursive Git tree for the branch.
2. Restricts the tree to the requested folder prefix.
3. Removes ignored and binary-looking paths.
4. Loads eligible text files up to the configured limits.
5. Runs the deterministic analyzers.
6. Returns structured JSON.

The response includes fields such as:

```json
{
  "metadata": {
    "owner": "example",
    "repo": "project",
    "branch": "member1-frontend",
    "folder": "frontend"
  },
  "stack": {
    "detected": ["React", "TypeScript", "Node.js"],
    "languages": ["json", "typescript"]
  },
  "file_tree": [],
  "important_files": [],
  "routes": [],
  "api_calls": [],
  "environment_variables": [],
  "types": [],
  "mock_data": [],
  "handoffs": [],
  "shared_files": [],
  "stray_files": [],
  "analysis_warnings": []
}
```

The exact arrays depend on the repository contents and the active file limits.

---

### 9.7 Analyze a repository

#### `POST /api/v1/analysis/repository`

Request:

```json
{
  "owner": "example",
  "repo": "project",
  "branch": "main"
}
```

This follows the same analysis pipeline as folder analysis, but analyzes the complete filtered repository tree rather than a folder prefix.

The analyzer is intentionally bounded. It does not attempt to load every file in a large repository if the configured file or count limits are reached.

---

### 9.8 Generate repository context

#### `POST /api/v1/context`

Request:

```json
{
  "owner": "example",
  "repo": "project",
  "branch": "main",
  "folder": "frontend",
  "include_markdown": true
}
```

The endpoint runs analysis and then converts the result into Markdown context. The response contains the structured analysis plus generated context:

```json
{
  "analysis": {},
  "markdown": "# Baton Repository Context\n...",
  "estimated_tokens": 1200
}
```

`estimated_tokens` is a rough estimate based on text length, using approximately four characters per token. It is a planning estimate, not a tokenizer-specific count.

The generated Markdown includes sections for:

- Stack.
- File tree.
- Routes.
- API calls.
- Environment variables.
- Handoffs.
- Important files.

The resulting context is clipped to `MAX_TOTAL_CONTEXT_BYTES`.

---

### 9.9 Generate an AI coding prompt

#### `POST /api/v1/prompt`

Request:

```json
{
  "task": "Add validation to the signup form",
  "context": "# Baton Repository Context\n...",
  "constraints": [
    "Do not modify the API contract",
    "Keep the existing styling system"
  ]
}
```

Response:

```json
{
  "prompt": "You are working on the Baton repository.\n\nTask:\nAdd validation to the signup form\n..."
}
```

The prompt generator is deliberately a template generator. It does not call an AI provider. The generated prompt can be copied into ChatGPT, Claude, Gemini, Cursor, Antigravity, or another coding workflow.

---

### 9.10 Detect shared-file conflicts

#### `POST /api/v1/conflicts`

Request:

```json
{
  "files": ["src/App.tsx"],
  "branches": {
    "member-a": ["src/App.tsx", "src/api.ts"],
    "member-b": ["src/App.tsx"]
  }
}
```

Response:

```json
{
  "conflicts": [
    {
      "path": "src/App.tsx",
      "branches": ["member-a", "member-b"],
      "reason": "shared file changed by multiple branches"
    }
  ],
  "conflict_count": 1
}
```

The current implementation detects path overlap between branch file lists. It does not calculate Git diffs or perform three-way merge analysis.

---

### 9.11 Integration endpoint

#### `POST /api/v1/integration`

Request:

```json
{
  "owner": "example",
  "repo": "project",
  "branch": "main",
  "frontend_branch": "member1-frontend",
  "backend_branch": "member2-backend"
}
```

Response:

```json
{
  "owner": "example",
  "repo": "project",
  "branch": "main",
  "status": "ready",
  "message": "Analyze frontend and backend branches separately to compare integration contracts."
}
```

This is a conservative V1 coordination endpoint. It acknowledges the requested integration comparison context but does not itself fetch and compare two full branch analyses. The reusable comparison function exists in `app/services/integration_service.py` and compares route sets when provided with two analysis dictionaries.

---

## 10. Schemas

The Pydantic schema files define the basic request and response data shapes.

### `app/schemas/github.py`

Contains models for:

- Repository validation input.
- Repository metadata output.
- Branch objects and branch responses.
- Tree items and tree responses.
- File responses.

### `app/schemas/analysis.py`

Contains:

- `AnalysisRequest` with `owner`, `repo`, `branch`, and optional `folder`.
- `RepositoryAnalysisRequest` with `owner`, `repo`, and `branch`.

### `app/schemas/context.py`

Extends the analysis request with `include_markdown`. The current context service always returns the generated Markdown; this flag is retained as part of the planned API shape.

### `app/schemas/prompt.py`

Contains a task, optional context, and a list of constraints.

### `app/schemas/conflict.py`

Contains an optional file list and a branch-to-file-list mapping.

### `app/schemas/integration.py`

Contains repository and branch identifiers for integration work.

### `app/schemas/team.py`

Contains a small `TeamMember` model with a member name and optional branch. It is available for future Mission Control team payloads but is not currently exposed by a route.

---

## 11. Analysis pipeline

### 11.1 `app/services/analysis_service.py`

`AnalysisService.analyze` coordinates repository retrieval and analysis:

1. Calls `GitHubService.tree`.
2. Filters items using `is_relevant`.
3. Keeps tree metadata for the `file_tree` result.
4. Loads eligible blobs one at a time.
5. Enforces `MAX_FILES_PER_ANALYSIS`.
6. Enforces `MAX_FILE_SIZE_BYTES`.
7. Ignores individual file retrieval failures so one problematic file does not abort the complete analysis.
8. Passes the collected metadata and text contents to `RepositoryAnalyzer`.

### 11.2 `app/analyzers/repository_analyzer.py`

This is the coordinator. It combines outputs from:

- Stack analysis.
- Structure analysis.
- API analysis.
- Frontend analysis.
- Handoff analysis.

It also adds placeholders for shared files, stray files, and analysis warnings so the response has a stable high-level shape for Mission Control.

### 11.3 `stack_analyzer.py`

Detects common indicators from paths:

- `.tsx` and `.jsx` imply React.
- `.ts` implies TypeScript.
- `.py` implies Python.
- `requirements.txt` implies Python dependencies.
- `package.json` implies Node.js.

It also reports recognized file languages such as Python, JavaScript, TypeScript, JSON, Markdown, CSS, HTML, YAML, and TOML.

### 11.4 `structure_analyzer.py`

Returns the filtered file tree and identifies common important files:

- `package.json`.
- `requirements.txt`.
- `pyproject.toml`.
- `README.md`.
- `main.py`.
- `App.tsx`.
- `App.jsx`.

### 11.5 `api_analyzer.py`

Uses regular expressions to detect simple patterns:

- Express/FastAPI-style `app.get`, `app.post`, `router.get`, and related route declarations.
- `fetch(...)` calls.
- Common `axios.get`, `axios.post`, and related calls.
- JavaScript `process.env.NAME` references.
- Python `os.environ(...)` and `os.environ_get(...)` references.

This is pattern detection, not a full parser. It may miss dynamically constructed routes and unusual formatting.

### 11.6 `frontend_analyzer.py`

Detects:

- TypeScript-style `interface Name` declarations.
- `type Name` declarations.
- Likely mock-data files based on names such as `mock`, `fixture`, or `fake`.
- Text patterns such as `mockData` and `dummyData`.

### 11.7 `handoff_analyzer.py`

Searches text for lines containing:

- `handoff`.
- `TODO`.
- `FIXME`.

It returns matching paths and matching lines to help teams identify incomplete work or transfer notes.

---

## 12. File filtering

### `app/utils/file_filters.py`

The default ignored directory names are:

```text
node_modules
.git
dist
build
coverage
__pycache__
.venv
venv
assets
```

The default ignored lockfile names are:

```text
package-lock.json
yarn.lock
pnpm-lock.yaml
```

The default binary-looking extensions include:

```text
.png .jpg .jpeg .gif .webp .ico .pdf .zip
.woff .woff2 .ttf .mp3 .mp4 .mov .exe .bin
```

Important source and configuration files are not intentionally excluded, including `package.json`, `requirements.txt`, `pyproject.toml`, TypeScript configuration, source folders, route folders, types, schemas, models, and mock folders.

Filtering is path-based and conservative. It is not a complete MIME detector.

---

## 13. Generators and utilities

### `app/generators/context_generator.py`

Converts analysis JSON into readable Markdown and adds a rough token estimate. The generated document begins with:

```markdown
# Baton Repository Context
```

The output is clipped by byte size using `fit_context`.

### `app/generators/prompt_generator.py`

Creates a simple prompt containing:

1. A Baton repository role statement.
2. The requested task.
3. Constraints as bullet points.
4. The supplied repository context.

### `app/utils/token_budget.py`

Provides:

- `estimate_tokens(text)`: approximately `len(text) / 4`.
- `fit_context(text, max_bytes)`: clips UTF-8 content without breaking a multibyte character and adds a truncation marker.

### `app/utils/text_utils.py`

Provides:

- File-extension language detection.
- Regex-based line extraction.
- Simple text truncation.

---

## 14. Conflict and integration services

### `app/services/conflict_service.py`

Builds a map from file path to branches touching the path. Any path associated with more than one branch is returned as a shared-file conflict.

This is useful for early coordination, but it is not a Git merge engine.

### `app/services/integration_service.py`

The reusable `compare(frontend, backend)` function compares route lists from two analysis results and returns:

- Frontend routes.
- Backend routes.
- Frontend routes without a backend match.
- Backend routes without a frontend match.
- A boolean `compatible` value.

Route strings must have compatible formatting for a direct match.

---

## 15. Error behavior

`app/core/exceptions.py` defines `BatonError`, which carries a message and an HTTP status code. The FastAPI exception handler serializes it as:

```json
{
  "detail": "error message"
}
```

Typical statuses include:

| Status | Meaning |
|---:|---|
| `400` | Invalid repository URL, unsupported path, or invalid request condition. |
| `401` | Missing or invalid `X-Baton-Key`. |
| `404` | GitHub resource was not found, as propagated from GitHub. |
| `413` | File is larger than the configured maximum. |
| `429` | GitHub rate limiting, if returned by GitHub. |
| `502` | Network-level failure when contacting GitHub. |

FastAPI and Pydantic handle malformed request bodies and missing required query parameters with standard validation responses.

---

## 16. Deployment

### Render configuration

`render.yaml` defines a Python web service:

```yaml
services:
  - type: web
    name: baton-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
```

Render should be configured with:

```text
BATON_ENV=production
BATON_ACCESS_KEY=<strong random operator key>
GITHUB_TOKEN=<optional GitHub read token>
FRONTEND_ORIGINS=https://your-frontend.example
MAX_FILE_SIZE_BYTES=200000
MAX_TOTAL_CONTEXT_BYTES=2000000
MAX_FILES_PER_ANALYSIS=100
```

Do not commit the production values.

### Local setup

From the backend workspace:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API should then be available at:

```text
http://localhost:8000
```

Interactive API documentation is provided automatically by FastAPI at:

```text
http://localhost:8000/docs
http://localhost:8000/redoc
```

---

## 17. Testing

The repository includes six focused test modules:

| Test file | Coverage |
|---|---|
| `tests/test_health.py` | Health endpoint response. |
| `tests/test_analysis.py` | Basic deterministic stack/repository analysis. |
| `tests/test_context.py` | Markdown context generation. |
| `tests/test_prompt.py` | Prompt template generation. |
| `tests/test_conflicts.py` | Shared-file conflict detection. |
| `tests/test_integration.py` | Integration endpoint request handling. |

Run the project tests with:

```bash
PYTHONPATH=. pytest -q --import-mode=importlib \
  tests/test_health.py \
  tests/test_analysis.py \
  tests/test_context.py \
  tests/test_prompt.py \
  tests/test_conflicts.py \
  tests/test_integration.py
```

The validation completed successfully with all six project tests passing.

The explicit `--import-mode=importlib` option avoids collisions with an unrelated installed package named `tests` in some sandbox environments.

---

## 18. Frontend integration guidance

The frontend can use the backend in this general sequence:

1. Call `/health` to verify availability.
2. Submit a GitHub URL to `/api/v1/github/validate-repository`.
3. Display the default branch and visibility.
4. Load branches from `/api/v1/github/branches`.
5. Display the tree through `/api/v1/github/tree`.
6. Request individual files through `/api/v1/github/file` when needed.
7. Run folder or repository analysis.
8. Generate Markdown context.
9. Generate a task prompt using the context.
10. Send the resulting prompt to the user's external AI coding workflow.

For production, the frontend should send:

```http
X-Baton-Key: <operator key>
```

The frontend should not expose the server-side `GITHUB_TOKEN` to browsers. A request-level GitHub token can be sent as `X-GitHub-Token` only when the product explicitly wants the operator to provide a temporary token.

---

## 19. Current limitations

The following are deliberate V1 limitations:

1. No persistent database or saved analysis sessions.
2. No user accounts, teams, roles, or login UI.
3. No OAuth flow for GitHub.
4. No GitHub write operations.
5. No webhook processing.
6. No background jobs or queues.
7. No WebSockets or streaming analysis.
8. No LLM calls.
9. No full AST parsing.
10. No full Git diff or merge-conflict analysis.
11. No recursive content retrieval beyond configured analysis limits.
12. No complete language-server or dependency graph analysis.
13. No binary file inspection.
14. No GitHub Enterprise, GitLab, or Bitbucket support.
15. The integration route is a conservative readiness endpoint; the reusable route comparison function is not wired into a complete two-branch fetching workflow.
16. The context `include_markdown` field is retained for API compatibility, while the current service always returns Markdown.
17. The initial tree filtering is path-based and may not identify every generated or binary file.

These constraints keep V1 understandable, deployable, and safe for a small Mission Control operator.

---

## 20. Recommended next steps

If the backend is extended after V1, the safest order is:

1. Add stronger unit tests for GitHub response mapping using mocked HTTPX responses.
2. Add explicit response schemas to every route.
3. Add pagination support for repositories with more than 100 branches or tree entries.
4. Improve file-type detection using response metadata and content sniffing.
5. Add richer route and API-call parsing without executing repository code.
6. Wire the integration endpoint to fetch and compare two branch analyses.
7. Add structured warnings when files are skipped because of limits.
8. Add request correlation IDs and safe operational logging without logging tokens.
9. Add rate-limit-aware GitHub error messages.
10. Add an explicit cache only if performance requires it and if token/repository privacy requirements are defined first.

Any future additions should preserve the core rules: read-only GitHub access, no secret leakage, no repository code execution, no unnecessary infrastructure, and no unapproved architectural expansion.


---

## 21. Master Solution Blueprint audit and correction log

This section records the non-destructive audit performed against `BATON_Master_Solution_Blueprint.md`.

### 21.1 Existing structure preserved

The current workspace is already the backend application root, so the existing `app/` architecture was preserved. The implementation continues to use:

```text
app/
├── api/routes/
├── core/
├── schemas/
├── services/
├── analyzers/
├── generators/
└── utils/
```

The workspace must not be changed into `backend/backend/`. In the final monorepo, this workspace is intended to be placed at `project-root/backend/`.

No working route, service, analyzer, generator, or test was deleted.

### 21.2 Blueprint-aligned corrections applied

The following targeted changes were made:

1. **Repository freshness metadata**
   - Analysis now retains the Git tree snapshot SHA as `metadata.commit`.
   - Analysis now records an actual UTC generation timestamp in `metadata.generated`.
   - Analysis reports `metadata.files_analyzed`.

2. **Omitted-content reporting**
   - Files skipped because of size, count, binary/decoding problems, or retrieval failures are recorded in `metadata.skipped_files`.
   - Analysis warnings state when relevant files were omitted.
   - Context generation returns an `omitted` array in addition to Markdown and the token estimate.

3. **Blueprint `context.md` shape**
   - Generated context now starts with `# Baton Context`.
   - It includes the blueprint sections for source, requesting member, do-not-touch boundaries, stack, structure, rules, source member, completed work, frontend expectations, routes, API calls, types/data shapes, mock data, environment variables, handoff, shared files, integration issues, stray files, not-detected facts, and verification files.
   - Unconfigured Mission Control fields are explicitly labeled rather than invented.
   - The existing `Baton Repository Context` label is retained for compatibility with the earlier V1 output.

4. **File language detection**
   - Individual GitHub file responses now include the detected language when the extension is recognized.

5. **Integration checking**
   - The existing integration endpoint remains backward-compatible when branch pairs are not supplied.
   - When both `frontend_branch` and `backend_branch` are supplied, the backend now performs real read-only analyses of both branches and returns route comparison output.
   - No GitHub write operation is introduced.

6. **Health compatibility**
   - The original `/health` endpoint remains available.
   - A non-documented compatibility alias `/api/health` was added to match the blueprint's Render health-check convention.
   - `render.yaml` now uses `/api/health` for the Render health check.

### 21.3 Blueprint items intentionally not invented

The uploaded blueprint describes product capabilities and a shared-contract philosophy, but it does not provide a frozen route-by-route API table with exact methods, request bodies, response schemas, error codes, and auth rules. Therefore, no new unapproved route families were invented.

The following blueprint features remain explicitly outside the current stateless V1 contract unless a later API contract defines them:

- Mission Control team/member persistence.
- Roles, duties, ownership configuration, and Team Rules storage.
- Repository skeleton initialization and GitHub commits.
- `contracts/api.md` and `contracts/data.md` management.
- Full project structure validation.
- Recent commit extraction.
- Line-level conflict analysis.
- Full two-branch contract/type compatibility analysis.
- Database-backed configuration.

This is intentional: the original V1 implementation rules prohibit databases, authentication systems, GitHub writes, background workers, and extra architecture. The current backend reports missing configuration as `Not configured` or `Not detected` rather than falsely claiming that the capability exists.

### 21.4 Contract caution

The existing route set remains:

```text
GET  /health
GET  /api/health                 compatibility alias
POST /api/v1/github/validate-repository
GET  /api/v1/github/branches
GET  /api/v1/github/tree
GET  /api/v1/github/file
POST /api/v1/analysis/folder
POST /api/v1/analysis/repository
POST /api/v1/context
POST /api/v1/prompt
POST /api/v1/conflicts
POST /api/v1/integration
```

Because the Master Solution Blueprint does not specify replacement payload contracts for these routes, their existing V1 request shapes were preserved to avoid breaking the frontend or existing integrations.
