# Baton — Final Hardening and Backend Connectivity Audit

## Scope and identity

2026-10-07 (Asia/Calcutta). Repository https://github.com/ghoshSG2347/Baton. Starts clean at 4f3e31d1603bebe4fdabaebc02fbd7fcb354599e on baton-current; fetched origin/main matches. Current branch main is occupied by another checkout; delivery is normal HEAD:main, no force/destructive commands/unrelated checkout changes. Implementation SHA is the commit containing this report; final documentation-only observations may follow. Push/deployment are separately checked.

Scope combines the user's final master hardening brief with the subsequent targeted backend-connectivity audit. New credential/usage work was underway before connectivity steering; the existing AI workspace/provider/analyzer architecture is preserved. Evidence labels: VERIFIED executed with stated scope; OBSERVED source/config inspection; UNKNOWN unavailable evidence. Never treat fixtures, metadata, health or push as deployed AI proof.

## Connectivity root-cause audit

VERIFIED independently before connectivity fixes: DNS for baton-shl3.onrender.com resolves; HTTPS /health and /api/health return 200 without redirect; /api/version returns 200; OpenAPI contains all expected GitHub/analysis/context/prompt/conflict/integration/workspace routes. Canonical production-origin CORS headers and OPTIONS return 200 and accept content-type, GitHub token and new Gemini headers. Runtime bundle's active API base is https://baton-shl3.onrender.com. A localhost string is embedded demo source text, not the active request base. No service worker/proxy/second HTTP client found. Render startup command/health/CORS are correct in tracked configuration. Private deployment environment/log dashboards are inaccessible; they were not fabricated.

VERIFIED actual production baseline: Vercel 4f3e31d -> Render 9f321e0 -> real GitHub connection, explicit analysis/current snapshot, New Chat without inspection/analysis, deterministic artifact/hash, canonical Context Builder, README source, Usage Center, branch invalidation and repository clearing. Therefore the reported earlier network failure is NOT reproduced. Its exact original browser/DNS/CORS/availability cause is UNKNOWN and must not be attributed to GitHub tokens without evidence.

OBSERVED defects that reproduced the misleading state: Overview unconditionally marked REPOSITORY and BRANCH connected; shell inferred connection from remembered repo plus memory token; browser/backend-to-GitHub errors shared one generic title. Unexpected application exceptions could lose readable JSON/CORS semantics. These are confirmed product/error-boundary defects, not proof they caused the original external outage.

## Fixes and responsibilities

| Area | Final change / purpose |
|---|---|
| batonApi | Validates backend origin/path/query/credentials/mixed content/local production configuration; production fallback is canonical Render, not localhost; fetch rejection has dedicated backend-unreachable code |
| workspaceStatus | Distinguishes backend 5xx, browser unreachability, GitHub authentication/permission/quota/not-found/network, snapshot and user AI key/model/provider failures |
| Overview | Connection badges require successful current observation; remembered identity and backend CHECKING/RESPONDED/UNREACHABLE separate |
| WorkspaceShell / Ask Baton | Selected repository label and observed unreachable state; errors cannot keep header claiming connected/grounded |
| SafeJSONResponses | Request-local Gemini key/model scope, finally reset and exact-secret sanitization; safe unexpected 500 JSON with allowlisted-origin CORS; class-only error logging |
| security / secrets | User-request provider scope overrides optional legacy operator setup, validates input bounds, participates in all sanitization |
| existing GeminiProvider | User-owned key/model metadata validation through models.get; same adapter handles generation; safe distinct model/auth/rate/network/timeout/schema errors |
| WorkspaceService | Conversation HMAC additionally binds AI key/model; changed AI scope cannot continue another conversation |
| Repository / workspace state | Accessible user key/model inputs, Validate & Connect and truthful checks, separate revalidation/clear, memory-only key/ready state, synchronous duplicate locks |
| existing usage system | Actual GitHub result/category/file/coalescing/snapshot metrics, quota resource, separate metadata-validation calls; bounded tab aggregates and last-operation summaries |
| shared pending read map | Added tree/file/context/artifact coalescing; credentials/request identity scoped, removed on settlement; no persistent second cache |

No database, scanner, provider abstraction, credential store, state library, autonomous tool, wildcard-origin bypass or duplicate usage pipeline was introduced. GitHub/Google endpoints stay fixed and use their own headers. Optional legacy operator configuration remains explicit; normal request-key usage requires no environment/provider/operator setup.

## Live AI evidence

VERIFIED: existing local key accepted by actual Google model-list and models.get metadata, read into memory only. Model discovery does not certify generation. gemini-2.5-flash-lite metadata passed but actual generation returned safe 404 ai_model_unavailable; an explicit diagnostic repeated that result. Both attempts had one provider request and UNKNOWN token usage, not fake zero. No silent retry occurred.

VERIFIED subsequent live browser journey with gemini-3.5-flash-lite: actual user-entered key/model -> local frontend/FastAPI -> real GitHub Hello-World/master -> real Google -> strict original evidence/citations -> scoped follow-up -> pinned source -> artifact hash -> Context Builder -> Usage Center -> branch/repository invalidation. Snapshot commit 7fd1a60b01f91b314f59955a4e4d4e80d8edf11d. Existing accepted Git login is NOT Fine-grained; exact least-permission certification remains unavailable.

| Measured local operation | GitHub API | Archive downloads | Actual AI generations | Details |
|---|---:|---:|---:|---|
| Explicit analysis | 3 | 1 | 0 | HEAD 1, archive API 1, tree 1; one collected text file; snapshot created; 1845 ms backend/1973 ms browser |
| First question | 0 | 0 | 1 | cache 1/snapshot 1; 2068 input, 97 output, 2165 total; provider 15137 ms |
| Follow-up | 0 | 0 | 1 | same conversation, revision 1 -> 2; 2041 input, 112 output, 2153 total; provider 2372 ms |
| Pinned source | 1 | 0 | 0 | same exact commit; one request; backend 473 ms |
| Artifact | 0 | 0 | 0 | verified SHA-256, 40 ms backend |
| Context | 0 | 0 | 0 | canonical snapshot reuse, 34 ms backend |
| New Chat | 0 | 0 | 0 | zero analysis/inspection requests |

Two successful turns report 4109 input/209 output/4318 total tokens; thinking metadata absent -> UNKNOWN. These are real provider reports for these operations, not account usage/prices/billing certification or averaged performance. Separate failed-model attempts are not included in successful-turn totals. Validation requests do not generate content and are separately counted.

## Tests and regressions

VERIFIED: 335 backend tests pass with unique workspace basetemp from backend root, no pytest cache provider, Python -B. Added cases cover valid/rejected key, unavailable/mismatched/unsupported model, provider status failures, request key overriding server configuration, Gemini-bound history rejection before another provider call, concurrent A/B provider header isolation, request scope cleanup and safe CORS-visible unexpected errors. Existing required-token/archive/paths/grounding/history suites retain coverage. Initial root-cwd basetemp failed one temp-directory setup (334 tests passed); corrected cwd/rerun passes 335. Starlette/httpx deprecation remains.

VERIFIED: frontend typecheck/lint and final production build. Master credential/connectivity browser fixture groups cover invalid/valid/cleared Gemini key, no persisted credentials, exact provider validation response guards, remembered versus unavailable Ask Baton/Overview state and separate backend/GitHub failures. Chrome/Edge pass; existing five-group Phase 3 and seven input groups pass both browsers. Workspace suite and eight product-completion groups pass Chrome, including source, comparison, all nine artifact hashes/downloads, ownership/context/prompt/team/reset behavior. All 29 repository-state cases pass after replacing the obsolete generic server-error expectation with the new explicit title.

VERIFIED input behavior remains native: browser wheel/keyboard and emulated touch, reduced motion, visible pointer/text cursor, focus/dialog/Escape restoration, no permanent overflow lock or Lenis wheel interception. Physical touchpad/mouse hardware inertia remains NOT VERIFIED. New fields retain native input/accessible labels. No fresh UI redesign.

## Archive decision

IMPLEMENTED previously, retained. Analysis-only bounded archive/tree hybrid is materially cheaper than per-file collection for larger repositories; actual current analysis uses three API requests plus one download rather than per-file requests. Browsing/source keep existing tree/content APIs. Existing tests cover commit identity, traversal/absolute/link/expansion/download/entry limits, omission/fallback correctness and redirect credential isolation. No disk extraction/execution or new scanner. Current one-file repository timing is not a memory benchmark; whole-process peak memory was not measured. Prior micrograd/private collection and all-nine-artifact evidence remains historical with its scope.

## Usage and security

One ContextVar response accounting pipeline plus one bounded tab aggregate. Safe counts/allowlisted quota resource only; no credential/prompt/source/response content event storage. Metadata validation and generation are separate; current/session consumption differs from provider account quota. Missing metadata/abandonment remains UNKNOWN. No polling/database. Usage observes requests and does not authorize them or replace canonical truth.

Normal GitHub APIs still require user token before network, public/private alike. Empty-token public test intentionally proves disabled/TOKEN REQUIRED, not anonymous access. All real upstream requests use that credential, no GITHUB_TOKEN/anonymous fallback. Exact user key/model is request scoped and never crosses into GitHub or prompt packets. History binds both providers; no user-key disk write. Actual browser live test confirms keys absent from localStorage/sessionStorage. Response/request/header secrets are sanitized; unexpected logs expose class name only. Generic redaction/instruction hierarchy cannot certify every unknown format/injection. No account/RBAC/multi-worker durability guarantee.

VERIFIED final scan of 34 changed/new/build files: zero actual-credential matches, zero credential-pattern matches and zero tracked .env files. Diff check runs before commit; .env and ignored test results are not staged. Actual credential values are compared in process memory and never printed. PROVIDER_SETUP.md/env examples explain request-key versus optional legacy operator behavior.

## Deployment boundary

Baseline production connectivity and non-provider user journey are VERIFIED as above. New hardening/user-key production deployment is not inferred from push or those older SHAs. Exact safe Vercel/Render markers and strongest available live deployed journey are measured after normal push, then reported/recorded. Dashboard access is unavailable; no settings/keys/model are fabricated. Production baseline has no complete legacy provider environment; request-key flow removes that requirement once new backend is deployed.

## Remaining genuine limitations

Original historical network incident cause UNKNOWN; present health/CORS/baseline journey passes. Latest rollout must be verified after delivery. Fine-grained least-permission live matrix, physical touchpad hardware, multi-worker topology and comprehensive model semantic/security certification remain unverified. Process-memory snapshots/history lose state on restart/eviction; authorization observations last up to 60 seconds. Static extraction/project-type/inventory/route checks are not runtime/merge/payload proof. Stop may leave remote work. Branch pagination, legacy inbound bounds, runtime/dependency pins/CI/tracked generated files remain debt, not authorization for architecture replacement.

## Documentation and delivery

PROJECT_CONTEXT.md rewritten as the latest requested 17-section canonical document and reconciled across architecture, features, credentials, user workflow, intelligence/scope, states, usage, security/input, deployment, tests/limits/evidence. Read again against final code/results. PROJECT_AUDIT.md is this current evidence report, not an appended generic changelog. PROVIDER_SETUP.md and safe env examples updated. Implementation/test files are listed by responsibility above and exact Git diff before commit. Final SHA/push/clean state/latest deployment are reported independently after delivery.

## Exact changed-file inventory

- `PROJECT_AUDIT.md` — Canonical status, evidence or safe setup documentation.
- `PROJECT_CONTEXT.md` — Canonical status, evidence or safe setup documentation.
- `PROVIDER_SETUP.md` — Canonical status, evidence or safe setup documentation.
- `baton-backend-v1/.env.example` — Canonical status, evidence or safe setup documentation.
- `baton-backend-v1/app/api/routes/workspace.py` — Existing API/security/provider/usage implementation.
- `baton-backend-v1/app/core/response_safety.py` — Existing API/security/provider/usage implementation.
- `baton-backend-v1/app/core/secrets.py` — Existing API/security/provider/usage implementation.
- `baton-backend-v1/app/core/security.py` — Existing API/security/provider/usage implementation.
- `baton-backend-v1/app/core/usage.py` — Existing API/security/provider/usage implementation.
- `baton-backend-v1/app/services/ai_provider.py` — Existing API/security/provider/usage implementation.
- `baton-backend-v1/app/services/analysis_service.py` — Existing API/security/provider/usage implementation.
- `baton-backend-v1/app/services/github_service.py` — Existing API/security/provider/usage implementation.
- `baton-backend-v1/app/services/workspace_service.py` — Existing API/security/provider/usage implementation.
- `baton-frontend/.env.example` — Canonical status, evidence or safe setup documentation.
- `baton-frontend/src/App.tsx` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/src/components/workspace/WorkspaceShell.tsx` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/src/components/workspace/sections/AIWorkspace.tsx` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/src/components/workspace/sections/Overview.tsx` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/src/components/workspace/sections/Repository.tsx` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/src/components/workspace/sections/UsageCenter.tsx` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/src/hooks/useWorkspaceState.ts` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/src/lib/api/batonApi.ts` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/src/lib/usage.ts` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/src/lib/workspaceStatus.ts` — Existing user credentials, connectivity/state or usage interface.
- `baton-frontend/tests/repository-states.e2e.cjs` — Regression or opt-in live verification.
- `baton-backend-v1/tests/test_master_hardening.py` — Regression or opt-in live verification.
- `baton-frontend/tests/master-hardening.e2e.cjs` — Regression or opt-in live verification.
- `baton-frontend/tests/master-live.e2e.cjs` — Regression or opt-in live verification.
