# Baton — Project Context

## 1. Product Purpose

OBSERVED: Baton is a read-only repository information and coordination workspace. It connects a user's GitHub repository, statically analyzes bounded files, retains canonical RepositoryIntelligence and generates scoped working context, constrained Gemini answers and reviewable Markdown artifacts. It helps prepare development work; it does not edit/execute the connected repository, commit there, create PRs, merge branches or prove runtime correctness.

Document date: 2026-10-07, Asia/Calcutta. Final hardening/connectivity pass starts at 4f3e31d1603bebe4fdabaebc02fbd7fcb354599e on clean baton-current, matching fetched origin/main. Repository: https://github.com/ghoshSG2347/Baton. Remote delivery targets main through normal HEAD:main because main belongs to another checkout. The implementation identity is the commit containing this context/audit, resolved with Git history. No credentials belong in documentation.

Evidence labels: VERIFIED = executed within stated scope; OBSERVED = inspected implementation; IMPLEMENTED = present in source, not automatically live-certified; NOT VERIFIED / UNKNOWN = insufficient evidence; KNOWN ISSUE = demonstrated limitation; INFERRED = plausible interpretation. Fixtures, Google model metadata, health 200, push and deployment markers establish different facts.

## 2. Current Architecture

OBSERVED: React 18 / TypeScript / Vite 5 / Tailwind / Framer Motion -> one batonApi JSON client -> FastAPI -> existing GitHubService -> bounded collection -> RepositoryIntelligence 1.1 -> MemorySnapshotStore -> existing Context/Workspace/Retrieval/Artifacts -> existing GeminiProvider -> strict evidence validation and original-record rendering. No second credential manager, provider abstraction, analyzer, snapshot service, usage store or database was created.

Browser useWorkspaceState owns nonsecret localStorage configuration and memory-only credentials. AI workspace stays mounted but hidden during other sections, retaining chat; other sections mount selectively and lose component-local results. There is no URL router/deep-link state. Frontend interfaces mirror backend Pydantic contracts; important response identities, validation, artifacts/hashes, source and chat continuity have runtime guards.

Backend SafeJSONResponses maintains request-local AI credentials in a ContextVar and resets them in finally. Existing request-local UsageResponses supplies safe measurements on the same response. FastAPI dependencies require user GitHub credentials; request AI credentials override optional legacy operator settings. There is no account/RBAC system, background queue, repository code execution or cross-worker state service.

Deployment: Vercel frontend https://baton-sigma-six.vercel.app; Render backend https://baton-shl3.onrender.com. Build/run settings and independently observed revisions are in section 12. Public health alone cannot certify provider or repository access.

## 3. Repository Structure

| Area | Responsibility |
|---|---|
| baton-frontend/src/App.tsx, main.tsx | Landing/internal workspace navigation, lazy mounted AI, reduced motion |
| src/hooks/useWorkspaceState.ts | Nonsecret configuration, memory credentials, scope changes, source handoff, reset |
| src/lib/api/batonApi.ts | One API URL/header/error/response-guard path; ephemeral read coalescing |
| src/lib/usage.ts, sections/UsageCenter.tsx | One bounded tab aggregate and quota/consumption presentation |
| components/workspace/WorkspaceShell.tsx | Navigation, selected repository, reachability observation, settings/mobile controls |
| sections/Repository.tsx, Analysis.tsx, Overview.tsx | Credential/connect/preflight, explicit collection and actual observations |
| sections/AIWorkspace.tsx | Grounded context/chat/revisions, artifacts, source, comparison, cancellation |
| sections/ContextBuilder.tsx, PromptBuilder.tsx, Team.tsx | Canonical/manual exports and local manual team configuration |
| sections/ConflictRadar.tsx, Integration.tsx | Explicit inventory overlap and route-level branch comparison |
| components/ui/CustomCursor.tsx, SignalField.tsx, index.css | Decorative capability-limited visuals; native interaction baseline |
| baton-backend-v1/app/api/routes, schemas | Routes, dependencies and authoritative input schemas |
| app/core/security.py, secrets.py, response_safety.py | Request credential scope, optional operator boundary, secret sanitization/safe errors |
| app/core/usage.py | Request-local upstream counts, token reports, quota and response metadata |
| app/services/github_service.py, analysis_service.py | One authorized GitHub client/cache/backoff/collection and analysis orchestration |
| app/intelligence, analyzers | Typed canonical static facts, extraction/reconciliation and snapshot store |
| app/services/context_snapshot.py, context_service.py; generators | Authorized exact-identity context projections/relevance/rendering |
| app/services/workspace_service.py, workspace_retrieval.py, workspace_artifacts.py | Scoped grounding/history, bounded retrieval and deterministic exports |
| app/services/ai_provider.py, conversations.py | One Gemini adapter and bounded process-memory conversations |
| tests, frontend/tests | Backend regression, browser fixtures and explicit opt-in live harnesses |
| AGENTS.md, PROJECT_CONTEXT.md, PROJECT_AUDIT.md, PROVIDER_SETUP.md | Continuing engineering rules, canonical behavior and evidence |

Generated dependencies/dist/test outputs, bytecode and ignored environment files are not additional architecture. Existing tracked bytecode/build-info debt is not silently cleaned up.

## 4. Current Features

OBSERVED: Authenticated repository URL/access preflight; branch/tree/file browsing; explicit repository/folder analysis; evidence-aware static project classification; process-memory snapshots; project/role/task/AI handoff projections; manual Team & Ownership; Context Builder; canonical or explicitly USER_PROVIDED manual prompts; nine deterministic Markdown artifact types with verified content hashes; scoped Gemini chat with evidence/citations/labeled reasoning; pinned source; existing-snapshot comparison; inventory overlap radar; route-level integration checks; memory-only Usage Center.

| Surface | Actual boundary |
|---|---|
| Repository | GitHub acceptance, selected repository/Contents-read/HEAD checks; first 100 branches only |
| Analysis | Explicit bounded static collection, never automatically triggered by opening Chat/Context/artifacts |
| Overview | Actual inspection/coverage/HEAD; remembered identity is separate from backend response and access |
| Working context / Context Builder | Existing exact-folder snapshot, member/task/constraints/byte budget; estimates are not provider usage |
| AI | Existing records, constrained selection/reasoning; no autonomous tools or repository writes |
| Prompt Builder | Existing canonical prompt artifact; manual mode formats unverified operator text |
| Team | Local manual role/duties/folder ownership; guidance, not GitHub permissions |
| Conflict Radar | File inventory overlap, not changed-line merge-conflict detection; failed branch reads surface errors |
| Integration | Explicit dual-branch analysis and method/path matching; no payload/type/runtime compatibility proof |
| Compare | Two authorized retained snapshots, commit/blob/contracts/records, no Git merge |
| Artifacts | context, handoff, prd, technical_design, tasks, implementation_plan, review, prompt, onboarding; prompt needs task |
| Usage | Actual response measurements, no billing estimates, persistent events, polling or metrics database |

Demo fixtures remain marked synthetic; they do not certify live services. Supabase is an unused dependency, not a database feature.

## 5. Current User Flow

OBSERVED: Enter Mission Control -> Repository -> repository URL + user Fine-grained GitHub PAT + user Gemini key/model -> Validate & Connect -> choose branch/folder -> explicitly Analyze -> canonical snapshot -> Working context -> New Chat -> question -> original evidence/citations -> follow-up ID/revision -> artifacts/source/compare -> Usage Center -> safe branch/repository change/reset.

GitHub-only connection is allowed for context/exports, with AI explicitly unavailable. Successful checks reflect executed upstream operations, not credential presence. Model validation proves metadata acceptance/support, not generation quota. Users do not configure .env or need an operator key for user-owned provider requests. Connected, analyzed, current snapshot and AI readiness remain separate.

Keys stay in tab memory; reload retains nonsecret repository/team/model configuration but requires credential re-entry. Remembered repo.accessible=false and quota/auth observations are not persisted. Changing GitHub token revalidates access; clearing blocks repository operations. Repository change clears repository-specific UI/team/source/history while keeping memory credentials for the next connection. Reset clears credentials/configuration and returns a clean workspace.

## 6. GitHub Integration

OBSERVED: Memory user token -> batonApi X-GitHub-Token -> required FastAPI dependency -> existing GitHubService -> GitHub REST Bearer header. No service falls back to server GITHUB_TOKEN or anonymous requests. Missing token returns github_token_required before network, including public repositories. The connectivity brief's empty-token public test intentionally stops at TOKEN REQUIRED; no anonymous mode was introduced.

Repository URL grammar accepts only github.com owner/repository without embedded credentials, query, fragment, extra path, empty/dot names or arbitrary hosts. Direct service owner/repo fields are also validated. Fixed upstream hosts, quoted ref/path and source inventory checks reduce traversal/SSRF risk.

Acceptance is a real /user request, followed by fresh repository metadata, branches/Contents-read and HEAD. The UI asks selected-repository Metadata: Read and Contents: Read, no writes/admin/Actions/PR/delete grants. These match the currently used repository, branches, tree, commit, content and archive endpoints in official [branches](https://docs.github.com/en/rest/branches/branches), [trees](https://docs.github.com/en/rest/git/trees) and [contents/archive](https://docs.github.com/en/rest/repos/contents) docs. Endpoint capability checks do not infer token subtype or complete grant list; accepted-permission response headers describe requirements, not grants. Live checks used an accepted existing Git credential, not a Fine-grained PAT; least-permission/expiration/revocation remain fixture-covered.

Observations are credential digest/path/params scoped, TTL 60 seconds, bounded 256 entries/40 MB with 4 MB per entry. Pending reads/analyses coalesce by credential/event loop. Explicit preflight/analysis refresh bypass relevant observations. Existing revocation/HEAD observation window remains. Backoff is credential scoped and bounded; x-ratelimit headers and retry-after determine primary/secondary waiting. No automatic aggressive retries or quota polling.

Analysis-only archives were already implemented and retained: bounded 20 MB compressed/40 MB expanded/10,000 entries, expected commit root, no extraction to disk/execution, traversal/absolute/link/sensitive-entry filtering, authoritative tree/blob inventory, omissions and bounded fallback. User PAT is not forwarded to codeload redirects; private temporary grant queries are scrubbed from httpx logs. File/collection limits remain 100 attempts, 200 KB/file and 2 MB text. Browsing/pinned source continue using tree/content APIs.

## 7. AI Integration

IMPLEMENTED: User Gemini key/model -> Baton X-Gemini-Key/X-Gemini-Model -> request-local ContextVar -> existing GeminiProvider -> Google HTTPS x-goog-api-key. Browser never calls Google directly. Keys are absent from URL/body evidence/history/snapshots/usage/returned JSON. Request scope is reset in finally and concurrent requests retain separate credentials.

POST /api/v1/workspace/provider/validate performs bounded [models.get](https://ai.google.dev/api/models), checks exact selected model plus generateContent support and returns safe key/model metadata state. Input checks reject blank/whitespace/oversized keys and malformed model IDs; they do not prove validity. Invalid key/access, unavailable model, rate limit, network, timeout and provider failure are distinct. No generation occurs during validation. Generation can fail after metadata success: live gemini-2.5-flash-lite metadata passed but generation returned 404; that is not marked working.

VERIFIED locally with actual Google/GitHub: gemini-3.5-flash-lite first/follow-up, strict original evidence/citations, pinned source, artifacts/context, usage and branch/repository invalidation. First reports 2068 input/97 output/2165 total tokens; follow-up 2041/112/2153. Thinking metadata absent -> UNKNOWN. This is one model/account/time observation, not permanent availability/billing certification or broad production reliability certification.

Optional GEMINI_API_KEY/GEMINI_MODEL/BATON_ACCESS_KEY remain backend-only legacy operator configuration. Explicit legacy server-provider chat requires operator authorization. Request keys take precedence and bypass the legacy configuration requirement for the user's own read-only work. Operator key is not an account/tenancy system. See PROVIDER_SETUP.md; never use VITE_GEMINI or expose operator credentials.

Existing Gemini REST schema/temperature/output/timeout budgets remain: four concurrent generation requests/process, no streaming or silent billable retry. AI_CONTEXT_BYTES=120000, AI_INPUT_BYTES=32000, timeout 45 sec and output cap 2000 defaults. No provider framework, embeddings/vector service or second adapter was added.

## 8. Repository Intelligence

OBSERVED: One RepositoryIntelligence 1.1 is canonical truth. Static analyzers extract languages, technology/dependencies, documentation/intent, components, routes/calls, environment variable names, data sources, requirements/conflicts and provenance. Documentation/specification intent is distinguished from observed declarations and inferred relationships. Static declarations/project-type heuristics are not runtime product certification; web assets caused micrograd's additional Frontend Application label in the prior audit.

MemorySnapshotStore keys owner/repo/branch/full commit/project root/model 1.1; serialized byte bounds/entry caps and sanitization apply. Reads authorize current HEAD through the request GitHub credential, validate snapshot/version/identity and do not collect files. Same commit/branch/folder reuses; new HEAD is stale; another branch/folder requires its own snapshot; repository changes invalidate local scope. Explicit older-snapshot continuation is marked stale, not current. Stores lack durability/worker sharing and expire across restart/eviction.

Context Model 2.0 preserves identity, member/task/protected scopes, completeness, record IDs, source commit/blob/path, omissions and unknown/conflicting boundaries. Lexical/intent retrieval selects at most 32 records plus mandatory boundaries and four previous turns; it is not semantic vector search. Named-file questions may fetch one pinned region. Backend validates exact supplied evidence IDs, actions/ownership/reasoning modes, then renders repository facts from original records. INFERRED/RECOMMENDATION/GENERAL_EXPLANATION prose remains labeled model output, not proven repository truth. USER_PROVIDED corrections do not mutate canonical facts.

Conversation binding includes repository/branch/commit/folder/member/task/context/constraints/GitHub credential and Gemini key/model under process-random HMAC. Up to 100 conversations, one-hour TTL, 20 turns; follow-ups require returned ID/revision. Stale revisions/limits/concurrent turns reject before provider work. New Chat clears draft/history/ID/revision/errors/current usage and restores composer focus while preserving snapshot/role/task/artifacts/session totals; zero inspection/analysis/GitHub calls. Stop restores draft and cancels local waiting; prevents button-default resubmission, but remote work/billing may finish.

## 9. Error/State Model

KNOWN ISSUE corrected: Overview and shell previously implied live CONNECTED from repository presence. Overview now shows confirmed observations only after inspection, removes repository/branch connection badges on error and separately shows backend CHECKING/RESPONDED/UNREACHABLE. Shell labels repository SELECTED and observes unreachable state through the existing usage response state. Ask Baton stops claiming connected/grounded after failed inspection/analysis. Persisted identity never proves access or a snapshot.

| Condition | Classification / user behavior |
|---|---|
| No user GitHub token | github_token_required, TOKEN REQUIRED, no network/fallback |
| Invalid/expired token | github_authentication_failure, replace token |
| Repository/resource denial | github_permission_failure / github_insufficient_permissions; not blindly rate limited |
| Missing/inaccessible repository | github_not_found; selected private access may be missing |
| Primary/secondary quota | github_rate_limit; safe remaining/reset/backoff, explicit retry only |
| Browser has no HTTP response | baton_backend_unreachable, Can't reach Baton right now; remembered state separate |
| Invalid API origin/path/mixed content/local production URL | baton_api_configuration, deployment-address guidance before fetch |
| Backend responds 5xx | baton_backend_failure / server-error presentation; not token/network rejection |
| Baton cannot reach GitHub | github_network_failure; Baton responded, GitHub unavailable |
| No/stale/invalid snapshot | snapshot_required / snapshot_stale / snapshot_invalid; explicit analyze/refresh |
| User AI key/model invalid/unavailable | ai_key_invalid / ai_model_unavailable etc.; replace/revalidate |
| Provider rate/timeout/network/invalid output | ai_provider_*; separate safe Gemini error, no fabricated answer |
| Expired/changed/limited/busy history | conversation_*; clear unusable local history/fresh chat, no rescan |

Browser fetch rejection cannot distinguish DNS, CORS, browser restriction and outage by itself. Do not guess. Technical details are collapsible; no raw stack trace/upstream body/credential display. Unexpected backend exceptions now produce safe 500 JSON with allowlisted-origin CORS and class-only logging, so a server exception need not masquerade as a CORS/network failure. No wildcard-origin shortcut.

## 10. Usage Tracking

OBSERVED: One request-local ContextVar records actual GitHub API attempts/successes/failures/rate-limited responses, archive downloads, fixed-category request breakdown, cache/coalesced/snapshot reads, collected files, successful snapshot creation, Gemini generation/metadata-validation requests and elapsed time. Existing X-Baton-Usage header exposes allowlisted bounded metadata through CORS; no usage endpoint/polling/database/content history exists.

One memory-only tab aggregate stores current conversation/session numeric counts, account quota/resource, fixed operation totals and last-operation/last-GitHub-operation summaries. GitHub quota limit/used/remaining/reset/resource is separate from Baton consumption. Header absence, invalid counts, transport failures and abandoned operations remain UNKNOWN, never fake zero. Credential change clears GitHub quota; AI credential change resets current conversation without discarding unrelated quota. Late prior-scope responses do not restore old quota/history. Reload clears usage; New Chat preserves session totals.

Gemini prompt/candidate/total/thinking counts come only from usageMetadata. Total is not inferred by sum; context character/token estimate is separately labeled. Average provider latency derives from measured provider latency/request count; validation does not generate tokens and is separate. No Gemini account-wide quota, billing, prices, costs or unlimited usage claim. Usage is observation, not repository/authentication truth.

## 11. Security

OBSERVED/VERIFIED within tests: memory credentials excluded from localStorage/sessionStorage, URLs, source evidence, prompts, snapshots, compact history, usage, logs and safe JSON. GitHub and Gemini credentials are forwarded only to their own fixed providers. Known/configured/request credentials are scrubbed from analysis/projections/response boundaries; generic credential patterns are defense-in-depth, not proof all unknown formats are removed.

Repository instructions are untrusted data in the provider system prompt; records are quoted/validated and never executed. No repository imports/eval/shell/subprocess execution, archive extraction or autonomous tools. Source/file traversal/sensitive paths/inventory/size checks apply. Environment templates may be analyzed with values sanitized but cannot be displayed through generic protected-file browsing. No arbitrary outbound provider host or insecure origin wildcard.

Request credential ContextVar isolation and Gemini-bound history are tested across concurrent users; GitHub observations/backoff/collection are credential scoped. Canonical authorized repository snapshots may be reused across authorized credentials. There is no account/tenant/RBAC system, durable multi-user isolation claim or global per-deployment budget; process-local state/60-second observations/multi-worker limitations remain. Legacy inbound schemas and whole-request body budgets remain debt.

Cursor/scroll/accessibility: native cursor/text/pointer never hidden; CustomCursor is optional aria-hidden pointer-events:none decoration only for fine hover/no coarse pointer/no reduced motion. Lenis/wheel/touch interception and transition body overflow lock were removed in the preceding input pass and remain absent. Native nested scroll, global focus-visible outlines, reduced-motion static SignalField/no RAF, MotionConfig, New Chat focus, modal/demo traps and settings/mobile Escape restoration remain. New key/URL/model inputs have accessible labels and native password/text behavior. Automated wheel/keyboard and emulated touch pass; physical touchpad/mouse hardware inertia is NOT VERIFIED.

## 12. Deployment

OBSERVED: Vercel rewrites SPA paths; public VITE_BATON_API_URL must be backend origin only, no /api suffix/query/credentials. batonApi strips trailing slash, validates origin/path/mixed content and uses canonical Render fallback in production rather than localhost. Development defaults localhost:8000. Vite values are build-time; rebuild after URL changes. No service worker, axios client or proxy was found. Browser never calls provider directly.

Render installs backend requirements and starts uvicorn app.main:app --host 0.0.0.0 --port $PORT; health /api/health, alias /health, safe /api/version. CORS allows canonical production origin and configured local origins, methods/custom headers including user credentials, exposes X-Baton-Usage, no wildcard-origin bypass. Monorepo root settings/worker count/runtime version pins/private dashboards remain unverified/not pinned in tracked config. No Docker/automated production CI.

VERIFIED connectivity audit before changes: DNS resolves, HTTPS works, /health and /api/health 200 without redirect, /api/version 200, all expected OpenAPI routes present, production-origin OPTIONS 200 including GitHub/Gemini headers. Actual bundle uses https://baton-shl3.onrender.com; a localhost string elsewhere is demo source text, not active API configuration. Browser production connect/analysis/snapshot/New Chat/context/artifact/source/Usage/branch/repository path passes. Vercel revision 4f3e31d; Render revision 9f321e0 at audit. Private Vercel env/Render logs were inaccessible; public runtime behavior was measured.

The reported historical network failure was NOT reproduced; its exact originating DNS/CORS/browser/availability cause remains UNKNOWN. Confirmed contributing product defects were misleading unconditional connection labels and combined error classification. VERIFIED after push: Vercel and Render both reported f3c96b4df82d913eb7eddf5b5acd16fc3f20c864; health aliases/OpenAPI/preflight returned 200, the user-provider route is present and a real deployed user-key Gemini two-turn journey passed. One preceding generation was rejected with ai_provider_invalid_response (502); no silent retry or fabricated answer. Private rollout logs remain unavailable. Subsequent documentation/test-only delivery can have a newer SHA; this statement certifies the implementation revision above.

## 13. Tests

VERIFIED: 335 backend tests after hardening, including request-key/model metadata, provider routing, AI-bound revision isolation, concurrent user credential separation, safe CORS-visible unexpected exceptions, existing required-token/archive/snapshot/grounding/history suites. Initial root-cwd basetemp path failed one temporary-directory setup; rerun from backend with unique workspace basetemp passes. Starlette/httpx deprecation warning remains.

VERIFIED: frontend typecheck/lint/build and browser fixture scopes recorded in PROJECT_AUDIT.md. Master credential/connectivity checks pass Chrome/Edge; existing five-group Phase 3, workspace, eight product-completion and seven input groups pass, including touch emulation and responsive overflow. All 29 repository-state cases pass after updated backend-error classification. Fixture success is not live Google evidence.

VERIFIED live local: actual browser/frontend/FastAPI/GitHub/Gemini two-turn journey on Hello-World/master/7fd1a60b01f91b314f59955a4e4d4e80d8edf11d, real provider token reports, exact pinned source, artifact hash, context/usage and scope invalidation. Previous public micrograd/private access/archive and nine artifact checks remain historical evidence with their scope, not repeated claims. Actual production implementation f3c96b4df82d913eb7eddf5b5acd16fc3f20c864 also passes the full user-key two-turn path. A preceding actual generation was rejected safely, so this is bounded acceptance evidence, not a guarantee of every provider response.

NOT VERIFIED: exact Fine-grained least-permission token, physical touchpad gestures, all real project-type semantic classifications, all possible prompt injection/secret formats, multi-worker topology or future model availability. No code coverage percentage measured.

## 14. Known Limitations

- Historical browser connectivity incident root cause unavailable; present production health/CORS/connect flow works.
- Model metadata availability does not guarantee generation, schema acceptance or quota. One production generation returned ai_provider_invalid_response; an explicit independent repeat passed. Strict rejection remains necessary; the precise rejected field was not captured on that first attempt.
- Snapshots/history/observations are bounded process memory, not durable/shared across workers.
- Static wrapper/alias/dynamic API extraction is shallow; project labels/inventory overlap/route matching do not prove runtime features/merge/payload compatibility.
- Branch lists stop at 100; collection/text/context/output budgets can omit important evidence and disclose omissions.
- Generic credential-pattern redaction and instruction hierarchy are not absolute secret/injection protection.
- Stop cancels browser waiting, not guaranteed remote generation; a later stale revision may need New Chat.
- Legacy schemas lack consistent whole-body bounds; dependencies/runtime pins/CI and tracked generated files remain debt.

## 15. Remaining Work

P0: No reproducible current service outage remains; implementation rollout and full production journey are verified. If the browser incident recurs, capture safe actual URL/status/preflight evidence to establish its cause.

P1: Provider-response/grounding robustness without weakening evidence rejection; user-owned Fine-grained least-permission/expiry/revocation live certification; physical touchpad hardware check; deployment topology/worker-sharing requirements; consistent inbound schema/body bounds and production runtime/dependency pins/CI.

P2: Focused wrapper/alias extraction improvements and fuller reasoning relevance validation; durable state only if explicitly required by deployment needs. No database or architecture replacement is authorized merely by this list.

## 16. Verification Evidence

Commands: git status/branch/remote/log/fetch and remote SHA; python -B -m pytest -q -p no:cacheprovider with unique workspace basetemp; npm.cmd run typecheck/lint/build; browser harnesses with actual Chrome/Edge; safe direct DNS/HTTP/OpenAPI/CORS and deployed bundle/marker checks. Read exact outcomes, changed responsibilities and measured limitations in PROJECT_AUDIT.md.

Actual local analysis: 3 GitHub API requests (HEAD, archive API, tree) + 1 archive download, one collected text file, snapshot created; 1845 ms backend/1973 ms browser. First/follow-up: zero GitHub requests/collection, cache/snapshot reuse, one actual generation each; 15137/2372 ms provider. Source: one GitHub request, 473 ms. Artifact/context: zero GitHub/provider requests, 40/34 ms backend. New Chat: zero inspection/analysis requests. These are individual measurements, not averages/benchmarks/guaranteed costs.

Live Google totals across two successful turns: 4109 input, 209 output, 4318 total; thinking UNKNOWN. Separate unavailable-model attempts report no token counts and are not silently treated as zero usage. Provider metadata validation is separately counted.

Production baseline: /health, /api/health, /api/version, OpenAPI and CORS OPTIONS 200; authenticated public connection/analysis/context/artifact/source and latest baseline Usage Center pass. VERIFIED implementation rollout f3c96b4df82d913eb7eddf5b5acd16fc3f20c864 and real production Gemini acceptance separately after push. Production analysis: two API requests plus one archive download, one file, snapshot created, 1566 ms backend/2901 ms browser. First/follow-up: zero GitHub requests, one actual generation each, 2068/97/2165 and 2041/108/2149 input/output/total tokens, 1396/1764 ms provider. Successful-turn totals: 4109 input, 205 output, 4314 total; thinking UNKNOWN. Earlier rejected production generation: 2068 input, 114 output, 2182 total, 2171 ms provider, 502 ai_provider_invalid_response. Total provider-reported tokens across these three production generations: 6496. Failed generation is retained, not hidden or treated as zero.

## 17. Change Log

2026-10-07: Master hardening plus connectivity steering adds normal user Gemini key/model validation and request scope, AI credential-bound history, richer existing usage measurements, strict API-origin validation, distinct backend/GitHub/AI errors, CORS-visible safe unexpected errors, honest Overview/shell/Ask Baton connection observations and expanded shared idempotent read coalescing. Preserves canonical intelligence/snapshots/provider/native interaction/archive architecture. Context/audit/provider setup reconciled with live local Google and production connectivity evidence. Implementation f3c96b4df82d913eb7eddf5b5acd16fc3f20c864 committed and pushed normally to main, remote SHA verified; both production markers match and full live user-key journey verified with the failed attempt retained. Final evidence/test diagnostic follow-up is separate.
