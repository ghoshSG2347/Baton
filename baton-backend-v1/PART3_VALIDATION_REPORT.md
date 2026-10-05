# BATON Part 3 — AI Workspace Validation

Implemented 2026-10-06. The user authorized proceeding from the stated workspace/chat/artifact/branch-assistant scope after confirming that no further Part 3 requirements would be supplied.

## Delivered product

- A responsive AI workspace within the existing React application: conversation, branch/commit identity, applied developer/task scope, evidence panel, artifacts and branch review. Existing tools and landing remain accessible.
- Server-only Gemini integration behind an `AIProvider` selection interface, using the existing httpx dependency. No provider key or provider SDK reaches the browser.
- Strict repository chat: the model selects current canonical evidence IDs and typed investigation actions. Baton validates the selection and renders factual content from original evidence. Unsupported facts/free-form output are rejected; UNKNOWN and out-of-scope replies are explicit.
- Context, handoff, PRD evidence draft, implementation plan, review and coding-prompt exports with exact identity, completeness and omission metadata. These deterministic artifacts reuse Part 2 sections and the existing prompt formatter.
- Branch comparison over two independently authorized existing canonical snapshots: inventory differences, changed/unknown blob hashes, retained API contract changes and protected-path changes.
- Bounded, transient server conversations with authorization/context binding, expiration, revision checks and limited history. Browser conversation/artifact state is memory-only.

Parts 1 and 2 remain the single analysis/context systems. Part 3 does not scan repositories, independently reconcile features or replace the canonical model. The only shared-layer additions are configured-secret redaction, included context-record metadata and a repository identity parameter for the existing prompt formatter.

## Security audit and implementation

No existing provider integration was found. Existing frontend GitHub tokens were excluded from persistence, but the operator key used a public Vite variable and API errors were logged to the console. Those exposure paths were removed. The operator key is now entered in workspace settings and held in memory. Both GitHub/operator credentials are stripped from persistence, and recognizable credentials in user strings are redacted.

`GEMINI_API_KEY` is a backend masked SecretStr excluded from settings serialization and repr. It is sent only in `x-goog-api-key` to a fixed provider host, never a query string, model prompt, context record or response. Provider errors and validation failures never echo raw credential/input payloads. Configured provider/operator/request secrets are redacted during collection, snapshot storage, context generation and JSON responses. Render references secret variable names with `sync:false`; environment examples contain empty values. Chat additionally requires configured operator authentication.

A recognizable credential-pattern scan of existing Git history found one existing synthetic token in `tests/test_github.py`; the scan printed only a redacted match. No deployment credential was opened or supplied. Pattern scanning/redaction is not a general guarantee against arbitrary concealed secrets.

The provider returns only a selection schema. Nonexistent/out-of-view IDs, extra free-form claims, missing evidence, inconsistent statuses and out-of-ownership/protected actions fail closed. Repository instructions remain quoted data; no provider tools, browsing, scripts, notebook/model execution or automatic Git changes are enabled.

## Validation

| Check | Result |
|---|---|
| Backend complete suite | **166 passed**: existing 132 tests plus 34 Part 3 cases |
| Part 3 suite after final artifact-scope adjustment | **34 passed** |
| Frontend TypeScript | Passed |
| Frontend ESLint | Passed, no errors or warnings |
| Production Vite build | Passed; workspace split into a lazy bundle |
| Browser regression checks | Passed on desktop and 390px mobile viewport |
| `git diff --check` | Passed |

Backend command: `python -B -m pytest -q -p no:cacheprovider` in `baton-backend-v1`. Frontend commands: `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run build` in `baton-frontend`.

Backend tests exercise exact canonical quoting, refusal/unknown behavior, invented IDs/free-form claims, protected reading versus actions, owned action validation, conversation authorization/duty isolation, eviction/TTL/revision/turn limits, all artifact types, required USER prompt tasks, authorized branch comparison/missing snapshots, configured-secret leakage, masked settings, snapshot storage redaction, header-only provider authentication, invalid/truncated/oversized/error/timeout responses, missing configuration, operator access and validation-response safety. Existing canonical/context/integration regressions continue to pass.

Browser checks exercise role payloads with protection scopes, commit pinning, grounded Markdown, artifact preview/download/focus/Escape, branch comparison, preservation of applied duties across branch switches, clearing old chat/artifact/comparison state, memory-only credentials, explicit analysis refresh, closed mobile navigation, Escape handling and horizontal overflow. There are no uncaught page errors.

The first browser harness intercepted frontend source imports; its mock pattern was corrected to backend endpoints only. Browser testing also exposed the developer selector's accessible label and mobile navigation state, both fixed before the successful runs.

Browser fixtures are generated through the actual Part 1/2/3 services by `tests/export_workspace_fixtures.py`. The provider and network are mocked only in isolated tests; the production UI/backend has no simulated AI fallback. Screenshots use the synthetic BookOS repository fixture and are not evidence of a live GitHub/Gemini session.

Preview captures:

- `../baton-frontend/.test-output/workspace-desktop.png`
- `../baton-frontend/.test-output/workspace-mobile.png`

The complete suite reports the pre-existing Starlette/httpx deprecation warning; the production build reports outdated Browserslist data. Neither affects these passed checks. No unrelated dependency update was performed.

## Deployment setup

Configure these in the **backend deployment environment**:

```dotenv
GEMINI_API_KEY=
GEMINI_MODEL=
BATON_ACCESS_KEY=
```

Supply actual values through deployment settings, not this file, Git, frontend environment variables, prompts or chat. Select an available Gemini model supporting JSON-schema `generateContent`. The adapter follows the [official REST reference](https://ai.google.dev/api/generate-content) and [structured-output documentation](https://ai.google.dev/gemini-api/docs/structured-output). Optional settings are `AI_CONTEXT_BYTES` (120000), `AI_TIMEOUT_SECONDS` (45) and `AI_MAX_OUTPUT_TOKENS` (2000).

Frontend configuration contains only the backend URL (`VITE_BATON_API_URL`). Enter the operator access key in workspace settings and a GitHub token if needed. Connect a repository, choose a branch and explicitly refresh analysis. Select a configured developer/apply a task scope, then ask questions or generate artifacts. Analyze both branches before comparing.

Without provider configuration, canonical context, artifacts and branch comparison remain available; chat reports unconfigured status instead of fabricating a response. The local frontend/backend preview runs at `http://127.0.0.1:5173/` and `http://127.0.0.1:8000/` for review. No deployment or live Gemini call was performed.

## Practical limits

Chat is deliberately evidence selection plus exact fact rendering, rather than unrestricted model prose or generated code patches. Selection relevance can be wrong; the server guarantees membership in current evidence, not semantic relevance of every selected excerpt. Retained unknown shapes and runtime limits remain explicit. Artifacts are reviewable evidence drafts/investigation plans, not new product requirements or implementation certification. Branch comparisons do not prove runtime compatibility or perform merges.

Canonical snapshots and conversations remain bounded process-local memory. Eviction, restart or another worker can require explicit refresh/new chat. No durable account/history/member database was added. Navigating away or reloading discards client conversation/artifact state. Authorization comes from the operator key plus GitHub access; USER ownership is guidance configuration, not an organization permission system.

Provider calls have bounded time/concurrency/output and no implicit retries. Stop cancels browser waiting, not necessarily an upstream billable call. Actual model availability, provider quota and live response behavior must be verified with deployment-supplied credentials. Existing pattern/heuristic extraction and redaction limits from Parts 1 and 2 still apply.
