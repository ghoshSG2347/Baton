# Baton — User Token / GitHub Access Audit

## Scope and identity

Audit date: 2026-10-07 (Asia/Calcutta). Repository: https://github.com/ghoshSG2347/Baton. Opened clean at `135e3c3` on `baton-current`; fetched and fast-forwarded to current remote-main baseline `fe4059a` before editing. Main is already checked out in another worktree, so delivery uses a normal `HEAD:main` push from this isolated checkout. No force push, reset or unrelated-checkout modification is authorized/needed.

Final implementation commit: the commit containing this report and the reconciled PROJECT_CONTEXT.md. Resolve the full SHA using `git log -1 -- PROJECT_AUDIT.md`; a tracked document cannot embed its own final hash. Push and rollout are checked separately and reported after delivery.

Evidence labels: OBSERVED = inspected source/configuration, VERIFIED = executed test with stated scope, UNKNOWN = no evidence, INFERRED = inference, RECOMMENDATION = future work. Fixture tests are not real Fine-grained PAT or Gemini certification.

## Root causes and fixes

| Finding | Root cause | Final behavior |
|---|---|---|
| Anonymous public-repository quota | Dependency and service both selected request → server → anonymous | Both fallbacks removed; required request header and defensive service network guard |
| Connection did not prove token access | Metadata alone can be readable publicly | /user acceptance, fresh metadata, Contents-read branch list, fresh default HEAD preflight |
| Inconsistent credentials | File preview could use an unvalidated input draft | Every connected operation uses the validated memory credential |
| Refresh claimed connection | Persisted repo identity remained while token disappeared | TOKEN REQUIRED gate, no repository network until reentry; no persisted authentication/quota observation |
| Replacement/clear retained evidence | Token changes left file handoff/UI observations | Re-preflight repository, remove handoff, scoped UI cancellation/reinitialization; clear blocks operations |
| Duplicate quota panels | Independent automatic HEAD inspection and branch request could both fail | Ask Baton branches wait for successful HEAD; failed inspection cannot launch branch load; individual operation error has one owner |
| Many analysis requests | One recursive tree plus per-file reads | Bounded archive + authoritative pinned tree, one canonical pipeline; contents fallback only for archive safety/correctness rejection |
| Archive evidence risk | Archive alone lacks authoritative blob/mode evidence; LFS may expand bytes | Pinned tree preserved; selected bytes must match Git blob SHA; comparisons and document blob provenance retained |
| No rollout identity | Health 200 cannot prove revision | Backend /api/version validates only RENDER_GIT_COMMIT; frontend baton-revision meta uses build SHA |
| Noisy instrumentation | Per-request/analysis metrics were INFO | Debug-only counters/metadata; temporary private download grant redacted in httpx URL logs |

## Authentication, permissions and security

VERIFIED: User memory state → batonApi X-GitHub-Token → required FastAPI dependency → existing GitHubService → Bearer GitHub REST. Public and private routes share the path. Normal user APIs never select GITHUB_TOKEN or anonymous access. Conflict Radar obtains authenticated trees before its pure overlap computation; Integration uses the same AnalysisService credential; context/artifacts/chat/compare authorize snapshot reads through the current credential. Manual prompt formatting and health/revision endpoints do not operate on GitHub.

OBSERVED: UI requests a Fine-grained PAT, selected repository, Metadata: Read and Contents: Read. It asks for no write/admin permissions. Preflight checks actual endpoint access, not a guessed permission list or credential prefix. X-Accepted-GitHub-Permissions is inspected on denied operations as endpoint requirement evidence, never reported as granted permission proof. 404 preserves the ambiguity between nonexistent and inaccessible private resources. Organization approval/policy can restrict access even for collaborators.

VERIFIED: Invalid token produces 401 authentication failure, never quota or anonymous retry. Permission/header failures, missing token, not found, primary/secondary/unknown quota, timeout/network/upstream failure and empty repositories have safe typed contracts. Rate metadata includes limit/remaining/used/reset/resource; cooldown is credential-scoped, bounded and disables immediate retries. No repeated /rate_limit polling occurs. GITHUB_TOKEN remains only a Settings/redaction value or an explicitly supplied diagnostic credential, not automatic user authorization.

OBSERVED/VERIFIED: Password inputs, cleared submitted input, memory-only credential/access key, no browser-storage/URL/query/AI/snapshot persistence. Saved repo accessible=false with no authenticated/source/quota observation. Draft credential never reaches source reads. Replacing a token revalidates this repository; changing repository clears repository-specific state and requires preflight even when the tab retains its credential. Existing authorization observations remain credential-digest scoped for 60 seconds; another credential does not inherit a grant. Explicit preflight refreshes HEAD/branches/metadata. No repository code is executed.

## Request accounting and collection decision

ARCHIVE COLLECTION: IMPLEMENT, analysis-only archive/tree hybrid. No second client, analyzer, snapshot engine, cache, credential store or context system. Generic browsing/pinned source keep existing APIs.

| Real authorized repository | Commit | Before: tree/content collection | Final hybrid cold HEAD | Final files |
|---|---|---|---|---|
| Public Alzheimer-Disease-Prediction-Model | 3a7a550985975a73805974c0e80f7c720b6dc8f0 | 1 tree + 42 files = 43 GitHub collection calls | HEAD + archive API + download redirect + tree = 4 HTTP requests | 42 |
| Private No-Way-Home3 | c05ae393110427f7c15f0f43c8cebf6f2f67b396 | 1 tree + 100 files = 101 GitHub collection calls | HEAD + archive API + download redirect + tree = 4 HTTP requests | 100 |

VERIFIED: Warm HEAD saves one request. Snapshot reuse has zero collection requests; expired 60-second HEAD observation can add one authorization request. Pinned tree can also reuse a credential-scoped immutable observation. Request counters include the download redirect separately; primary GitHub API collection is archive + tree, not the codeload HTTP download. Concurrent identical analysis coalesces; duplicate inventory paths do not create duplicate file reads.

Measured before under tracemalloc: public 28.12 seconds / 7,555,598 peak traced Python bytes; private 133.64 seconds / 6,832,321 bytes. Bounded archive inventory before authoritative-tree reconciliation: about 33 MB public / 26 MB private peak traced bytes; 9.41 / 144.78 seconds under tracing. Final verified hybrid without tracemalloc: public 7.46 seconds, private 54.58 seconds. Traced/untraced runs are not a controlled latency comparison; do not attribute all wall-clock differences to the transport. Download-only engineering checks: public 8,313,015 compressed / 19,739,614 declared expanded bytes / 79 entries / 2.26 seconds; private 6,817,139 / 14,358,285 / 1,326 / 1.84 seconds. Canonical static processing remains significant for the private repository.

Safety: 20 MB streamed download; 40 MB decompressed TAR stream before any PAX/long-name parsing; 10,000 entries; existing 100 attempted text files / 200 KB per file / 2 MB selected total. In-memory reads only. Absolute/traversal/Windows/control-character paths, duplicate members, symlinks/hardlinks/devices and inconsistent commit roots are rejected. The full API ref is the HEAD SHA; public seven-character and private full-SHA root forms are checked. Authoritative tree blob hashes verify selected bytes (including LFS expansion mismatch), and its inventory/modes/SHAs feed the unchanged pipeline. Folder filters, priority, sensitive-path filtering, sanitization and omissions remain intact. Rejected archives use the bounded existing collector; auth/quota/network/API failures never trigger an alternate scan. Oversized/truncated archives cannot become apparently complete snapshots. Memory overhead is bounded but higher than tree/content collection. GITHUB_ARCHIVE_ANALYSIS=false is an explicit operational rollback to the bounded collector.

## Test matrix: request / expected / actual / status

| ID / Request | Expected | Actual | Status |
|---|---|---|---|
| A public + valid token | Authenticated preflight/analysis | Real accepted Git credential, full SHA/blobs, 42 files; Fine-grained subtype unavailable | PARTIAL live; fixture PASS |
| B public + no token | Block before GitHub | Route 401 + UI disabled connect; no repository calls after reload | VERIFIED |
| C public + invalid token | 401, no downgrade | Actual GitHub 401 + browser actionable error | VERIFIED |
| D private + selected Fine-grained token | Private branches/tree/analysis | Real authorized private credential, 100 files, archive/blob proof; not Fine-grained | PARTIAL live; fixture PASS |
| E private + unselected repo | Access denial/not found | /user success followed by safe 404/403 stops preflight | Fixture PASS; live UNKNOWN |
| F missing Contents read | Clear permission failure | Branch endpoint 403 + accepted permissions maps insufficient permissions | Fixture PASS; live UNKNOWN |
| G missing Metadata read | Clear endpoint requirement failure | Metadata endpoint 403 + accepted permissions maps insufficient permissions; no grant inference | Fixture PASS; live UNKNOWN |
| H expired | Authentication failure | 401 fixture stops at /user, no retry | Fixture PASS; live UNKNOWN |
| I revoked | Authentication failure | Same safe 401 lifecycle fixture | Fixture PASS; live UNKNOWN |
| J primary rate limit | Safe quota/reset + blocked retry | Wire classification + credential cooldown + browser disabled actions | Fixture PASS |
| K secondary rate limit | Backoff, no aggressive retry | Wire/browser cooldown expiration, zero auto-analysis | Fixture PASS |
| L repository switching | Old evidence gone; new preflight | Browser clears identity/team/active intelligence; memory credential retained only | PASS |
| M branch switching | Correct current/stale identity | Browser late-result/branch isolation and service commit-pinning | PASS |
| N snapshot reuse | No tree/file/archive collection | Actual warm public reuse 0 collection; private expired HEAD adds authorization read only | VERIFIED |
| O New Chat | No collection; clear draft/session | Workspace fixture assertions: 0 analysis and 0 inspection at click | Fixture PASS |
| P follow-up chat | Reuse snapshot/conversation | Service/browser fixture uses ID and revision; no analysis | Fixture PASS; live Gemini UNKNOWN |
| Q Context Builder | Existing snapshot only | Live HTTP 200 + browser render, no analysis POST | VERIFIED |
| R Prompt Builder | Snapshot artifact, task required | Browser canonical/manual provenance; actual prompt HTTP 200 with task | PASS |
| S Source | Same credential and pinned commit | Live README source HTTP 200, same commit; path guards tested | VERIFIED |
| T Conflict Radar | Same credential; honest overlap/errors | Browser failed branch read preserved; per-branch dedup fixtures | Fixture PASS |
| U Integration | Same credential; bounded canonical analysis | Service/route token headers; browser insufficient evidence presentation | Fixture PASS |
| V artifacts | Snapshot reuse + hashes | All nine actual HTTP 200 with valid inputs, matching hashes; browser previews/downloads | VERIFIED |

## Executed checks and limits

- Backend: 305 passed, 11.45 seconds in final full run; one existing Starlette/httpx deprecation warning.
- Frontend typecheck/lint/build: PASS; no lint warnings. Existing Browserslist age warning remains.
- Workspace browser suite: PASS, grounded fixture chat/citations/source/compare, New Chat/follow-up/expired sessions, token isolation/mobile/refresh.
- Repository states browser: 29 passed, including quota cooldown/error classification/late results/branch and repository switching.
- Product completion browser: 8 passed, builders, team edit/delete/reload, measured Overview, integration unknown, nine artifact previews/downloads, settings/reset.
- Live GitHub browser: 9 passed, actual React → local FastAPI → GitHub; no-token blocking, invalid token, accepted bucket, double-click one analysis, reuse, context, secrecy and refresh/reentry without rescan.
- Actual public/private GitHub service runs: both preflights, exact commit-pinned analysis, 5000-request authenticated core bucket, archive downloads/hybrid blob verification and reuse verified.
- Local live artifact/source HTTP checks: nine artifact kinds and pinned README pass; missing-task prompt correctly returned 422 before valid-task retry.
- No real Fine-grained PAT was safely available. The existing Git credential was never written/logged/returned and was identified only as not Fine-grained. No live missing-scope/expired/revoked token was created or guessed.
- Live Gemini stops at inspection: configured=false. First/follow-up response quality, quota and production chat remain UNKNOWN; fixture success is not provider certification.

Earlier implementation failures were corrected: Windows pytest temporary directory permissions required a unique explicit basetemp; old tests expected anonymous fallback; a private archive used full-SHA rather than public short-SHA roots; a refresh browser assertion still expected the old anonymous inspection; one live run was invalidated by frontend hot reload and rerun cleanly. Final results above are successful executed runs, not claims that these earlier failures passed.

## Deployment and configuration verification

VERIFIED before delivery: Vercel HTML 200 and Render /api/health 200. Old production no-token repository validation returned 429/github_rate_limit/token_source=none. Existing accepted request credential privately validated No-Way-Home3 with HTTP 200, correct canonical Vercel Origin/CORS and no secret echo, but old response lacked authenticated/token_source fields. Therefore pre-delivery deployment was old; a Git push is not rollout proof.

OBSERVED: Existing Render start/build configuration, Vercel rewrite, operator-key/provider/CORS/build-time API variables remain. Normal repository authorization uses the request credential, never server GITHUB_TOKEN. .env.example now distinguishes diagnostics and exposes bounded archive controls. Provider secrets remain backend-only; no tracked actual environment values. Backend /api/version and frontend baton-revision markers permit post-push SHA comparison; missing/null/mismatched values mean unverified/stale, not success. Final delivery report records post-push checks; dashboard/root/build settings remain unavailable.

## Remaining limitations

Real least-permission Fine-grained/public/private/collaborator/selection/lifecycle matrix and live Gemini remain unverified. GitHub itself can restrict organization/resource-owner/collaborator token access. Token subtype is not inferred as a security claim. Snapshots/conversations/observations remain process-local; restart/eviction/worker separation can lose state. Existing authorization observations have a 60-second lifetime. Branch listing remains first 100; content/archive limits produce real omissions. Static aliases/wrappers and payload compatibility are incomplete; Conflict Radar inventory is not merge-hunk detection. Private canonical processing is still comparatively slow. Archives add bounded memory overhead and can require fallback for symlinks/LFS expansion/large/truncated trees. Broader request-size/runtime pinning/CI/tenancy debt remains outside this task.

## Security and documentation consistency

VERIFIED/OBSERVED: No repository execution/import; no PAT forwarding to codeload; no token/account profile/upstream-body response; sanitized canonical file/context/evidence/provider boundaries unchanged. Transport query grants redacted at INFO and debug diagnostics use categories/counts/allowlisted quota only. Executed scan of every tracked file and the implementation diff found zero existing Git credential or configured-secret matches. Staged whitespace and secret review are repeated before commit. Credentials are excluded from browser storage and AI payloads; synthetic test credentials are inert strings, not real secrets. No environment file, generated dump/build, bytecode or credentials are staged.

PROJECT_CONTEXT.md was revised in place for current product/token/preflight/security/cache/archive/snapshot/refresh/test/deployment/provider behavior and reread against source/tests/runtime configuration. Obsolete optional-token/server-fallback statements were removed from the canonical current reference. GITHUB_TOKEN_GUIDE.md records the user-facing read-only minimum and official links. Historical V1/audit documents are explicitly historical, not current contracts.

## Exact intended files changed

- `PROJECT_AUDIT.md`
- `.gitignore`
- `GITHUB_TOKEN_GUIDE.md`
- `PROJECT_CONTEXT.md`
- `baton-backend-v1/.env.example`
- `baton-backend-v1/app/api/deps.py`
- `baton-backend-v1/app/api/routes/github.py`
- `baton-backend-v1/app/api/routes/health.py`
- `baton-backend-v1/app/core/config.py`
- `baton-backend-v1/app/services/analysis_service.py`
- `baton-backend-v1/app/services/github_service.py`
- `baton-backend-v1/tests/conftest.py`
- `baton-backend-v1/tests/test_ai_workspace.py`
- `baton-backend-v1/tests/test_context_system.py`
- `baton-backend-v1/tests/test_github.py`
- `baton-backend-v1/tests/test_github_archive.py`
- `baton-backend-v1/tests/test_github_rate_limits.py`
- `baton-backend-v1/tests/test_health.py`
- `baton-backend-v1/tests/test_integration.py`
- `baton-backend-v1/tests/test_intelligence_service.py`
- `baton-backend-v1/tests/test_product_completion.py`
- `baton-backend-v1/tests/test_repository_states.py`
- `baton-frontend/src/App.tsx`
- `baton-frontend/src/components/workspace/WorkspaceShell.tsx`
- `baton-frontend/src/components/workspace/sections/AIWorkspace.tsx`
- `baton-frontend/src/components/workspace/sections/Repository.tsx`
- `baton-frontend/src/hooks/useWorkspaceState.ts`
- `baton-frontend/src/lib/api/batonApi.ts`
- `baton-frontend/src/lib/workspaceStatus.ts`
- `baton-frontend/src/types/index.ts`
- `baton-frontend/tests/github-live.e2e.cjs`
- `baton-frontend/tests/product-completion.e2e.cjs`
- `baton-frontend/tests/repository-states.e2e.cjs`
- `baton-frontend/tests/workspace.e2e.cjs`
- `baton-frontend/vite.config.ts`
