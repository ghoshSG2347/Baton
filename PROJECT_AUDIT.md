# Baton — Phase 3 AI Workspace and Usage Audit

## Scope and delivery

2026-10-07; repository https://github.com/ghoshSG2347/Baton. Baseline 0835042f3e833966a4b68d758578b7c7e8cce22b on clean baton-current matched fetched origin/main. Delivery is normal HEAD:main, never force. The implementation identity is the commit containing this audit, resolved through Git history. Deployment verification is separate from compilation, push and health.

Evidence labels: OBSERVED = inspected implementation/configuration; VERIFIED = executed check within stated scope; UNKNOWN = unavailable evidence. Google transport fixtures are never live Gemini certification.

## Prior Usage Center audit

PARTIAL at baseline: GitHub account quota and request/cache debug counters existed, but there was no Usage Center, current-conversation/session accounting or provider token reporting. Existing snapshot/context/Gemini/evidence services were retained. No database, metrics endpoint, polling service, new analyzer or parallel intelligence pipeline was created.

## Findings and delivered fixes

| Finding | Fix and verified behavior |
|---|---|
| Follow-ups sent only an ID; revision conflicts could consume provider calls | Follow-ups require revision, scope includes constraints, stale/limit/concurrent turns reject before provider work |
| Immediate duplicate submits could race React state | Synchronous browser request lock; server reserves each active existing conversation |
| Stop could resubmit its restored question | Prevent default click before Stop becomes Send; browser regression proves exactly one request and pending cleanup |
| Navigation/fresh-chat behavior could discard state or rescan | Existing mounted AI workspace retained; both fresh-chat controls share reset/focus behavior and zero analysis/inspection |
| Provider metadata discarded | Existing Gemini response supplies strict numeric usageMetadata; missing values UNKNOWN; rejected billable responses retain reported counts |
| Unsafe/indistinguishable provider failure presentation | Safe auth/rate/timeout/network/invalid-response codes, bounded retry delay, no upstream-body disclosure or automatic retries |
| StrictMode duplicated source reads | One existing ephemeral read coalescer now covers branches, inspection and source, scoped by request and credentials and removed after settlement |
| No visible consumption accounting | One request-local numeric ContextVar response header and bounded memory-only tab aggregate; separate current conversation, session and account quota |

Scope binds repository/branch/full commit/folder/member/task/context/constraints/credential. History remains process-memory bounded (100 conversations, TTL one hour, 20 turns, four previous turns supplied). User project/folder corrections remain USER_PROVIDED and never mutate canonical repository facts. Secret/authorization requests are refused without provider calls. Canonical fact rendering, exact evidence ID/action validation, ownership constraints, schema and untrusted repository instruction boundaries remain enforced; semantic model correctness is not guaranteed by schema validation.

## Executed checks

VERIFIED: 323 backend tests pass. The initial Windows default-temp permission error was resolved by a unique workspace basetemp; it was not an application failure. Existing Starlette/httpx deprecation and inaccessible pytest cache warning remain. Python -B avoids generated tracked bytecode changes.

VERIFIED: frontend typecheck, lint and production build. Chrome and Edge each pass five grouped Phase 3 fixture checks: immediate duplicate prevention, first/follow-up continuity with ID/revision, exact synthetic accounting and current/session resets, Stop/abandoned UNKNOWN handling, typed timeout and missing metadata. Existing workspace suite passes. Repository-state suite passes 29 checks, product-completion suite eight checks, input-reliability suite seven Chrome groups; prior input task also verified Edge and production native input behavior. Fixtures are not live provider evidence. Physical touchpad hardware remains unverified.

VERIFIED: actual assembled local frontend -> FastAPI -> real GitHub -> real snapshot/context/retrieval/Gemini adapter -> explicitly mocked Google HTTP transport -> strict validated evidence -> citations -> follow-up -> pinned source -> artifact/hash -> Context Builder -> Usage Center -> branch/repository invalidation. Repository octocat/Hello-World, master, commit 7fd1a60b01f91b314f59955a4e4d4e80d8edf11d. Credential is an accepted existing Git login, not a Fine-grained PAT; it stayed in process/browser memory, never source/output/storage.

| Actual local operation | GitHub API | Archive downloads | Provider requests | Other measured results |
|---|---:|---:|---:|---|
| Explicit cold analysis | 3 | 1 | 0 | 2407 ms backend; 2522 ms browser; valid pinned snapshot |
| First chat | 0 | 0 | 1 mocked | cache 1, snapshot 1; 36 ms backend |
| Follow-up | 0 | 0 | 1 mocked | same conversation/revision; cache 1, snapshot 1; 38 ms backend |
| Pinned source | 1 | 0 | 0 | exactly one source request; 488 ms backend |
| Artifact | 0 | 0 | 0 | verified hash; 39 ms backend |
| Context | 0 | 0 | 0 | canonical reuse; 52 ms backend |
| New Chat | 0 | 0 | 0 | zero analysis/inspection requests |

Mocked Google reports 101 input, 9 output, 115 total and 5 thinking tokens per turn, with 10/11 ms mocked transport latency. These numbers verify metadata propagation only; they are synthetic, not real Gemini consumption, prices or quota. Total is provider-reported rather than inferred from input+output. Missing token fields and abandoned operations display UNKNOWN; Stop cannot certify remote cancellation/billing.

VERIFIED: real public karpathy/micrograd analysis at 7bc720e951fe422b8f8814aa5aa1b64121d26b4c collected 11 files, used two GitHub API calls plus one archive download with warm HEAD, and completed backend analysis in 2011 ms. All nine artifact types returned HTTP 200, correct SHA-256 and zero additional GitHub/provider requests. Real private ghoshSG2347/No-Way-Home3 access preflight returned 200/private. The earlier token task verified its bounded private analysis; this phase did not repeat that collection. Frontend/backend/ML/docs-rich/docs-poor patterns have fixture coverage; real semantic certification across all project types is not claimed.

## Provider and production boundary

LIVE GEMINI UNVERIFIED. Production inspection before delivery reports configured=false. The inspected local key alone has no model/operator setting; no model was guessed and no authentication bypass was used. The checkout has no complete Gemini runtime. Inspection safely exposes missing names/model status after rollout; provider keys remain backend-only. PROVIDER_SETUP.md documents actual setup and live acceptance. No first/follow-up request contacted Google in this audit.

At baseline Vercel serves 0835042; Render reports 89b3801c50a71e30de960b21b65e446aa724c921. VERIFIED after push: implementation 9f321e0214a11c5864c171a981316c0128ead957 matches remote main; clean checkout. Render /api/version reports that exact SHA. At 16:00 UTC Vercel still serves 0835042 after repeated revision checks; latest frontend/Usage Center deployment is UNVERIFIED. The exact-latest production harness correctly refuses that mismatched revision. A separate temporary run explicitly expecting preceding 0835042 passes actual deployed frontend/new Render/real GitHub connection, explicit analysis/current Hello-World snapshot, New Chat with zero analysis/inspection, unavailable Gemini/disabled composer, deterministic artifact/hash, canonical Context Builder, README source, branch invalidation and repository clearing. It explicitly records new Usage Center absent. No APIs were mocked in this run.

Production analysis uses two API requests plus one archive download with warm HEAD, backend 1436 ms; README source uses one API request, 565 ms. New backend numeric usage headers are observed on production responses. Production inspection exposes configured=false, model=null, missing GEMINI_API_KEY/GEMINI_MODEL/BATON_ACCESS_KEY, model_validation=UNVERIFIED. No first/follow-up live Google response, live token usage or latest frontend UI is certified. A marker match establishes revision, not live AI quality. Documentation follow-up records implementation observations; its own deployment is checked separately.

## Usage and security

One ContextVar per API request resets in finally and carries only allowlisted numeric counts/quota. X-Baton-Usage is exposed through existing CORS; no raw bodies, identity, questions or credentials are in that header. Frontend stores totals and one last-operation summary in tab memory only. Credential change clears account quota; late prior-scope responses cannot restore it. Session data clears on reload and current usage clears on New Chat. GitHub account quota differs from Baton consumption; Gemini billing/account quota is UNKNOWN.

No credential fallback, browser credential persistence, repository execution, provider frontend SDK or new database was introduced. Provider errors do not echo upstream bodies. Existing redaction remains defense-in-depth, not a guarantee for all unknown secret formats. Final scan of 37 changed/new/build files found zero inspected-credential or credential-pattern matches. git diff --check passed. Ignored .env and test outputs are excluded.

## Remaining limits

- Complete backend key/model/operator configuration and a live first/follow-up Google response remain unavailable; model validity, billable usage and semantic provider quality are UNVERIFIED.
- Exact user-owned Fine-grained selection, least permissions, expiration/revocation are fixture-covered, not certified using the accepted existing credential.
- Project classification is static/heuristic. micrograd also receives Frontend Application because of web assets; this does not establish a runnable frontend. No analyzer rebuild was performed.
- Snapshots/conversations are process-local, lack worker sharing/durability and expire on restart. Four provider requests per process is not a deployment-wide limit.
- Stop cancels browser waiting; remote provider work may complete and a next stale revision may require New Chat.
- Live production settings/worker topology and physical touchpad hardware remain outside demonstrated evidence. Existing dependency/version/CI limits remain documented in canonical context.

## Changed responsibilities

Backend: app/core/usage.py; main middleware/CORS; chat revision schema; Gemini metadata/errors; GitHub counters/quota; snapshot/analysis reuse accounting; conversation reservation; scoped chat checks and safe readiness. Tests: test_phase3.py, revision-aware existing tests and explicit local-only phase3_runtime.py.

Frontend: src/lib/usage.ts; UsageCenter; navigation/App/types; credential quota reset; batonApi response accounting and ephemeral read coalescing; AI revision/duplicate/Stop/fresh-chat/error behavior; typed workspace status. Browser tests: corrected existing workspace continuity; phase3 fixtures, assembled local real-GitHub/mock-Google harness and opt-in production harness.

Documentation: PROJECT_CONTEXT.md reconciled, this audit, PROVIDER_SETUP.md and backend .env.example. No ignored environment, outputs, screenshots or credentials are part of delivery. Earlier token/archive delivery 89b3801 and input delivery ccbc51/0835042 remain historical evidence, not substituted for Phase 3 acceptance.
