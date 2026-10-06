# GitHub rate-limit and repository-analysis audit

Audited 2026-10-06 against the existing canonical pipeline and the public repository:
https://github.com/ghoshSG2347/Alzheimer-Disease-Prediction-Model

## Root cause

There are two reproducible defects, rather than a broken Authorization header:

1. `useWorkspaceState` restores the repository from browser storage but intentionally initializes the GitHub token to an empty string. That correctly avoids persisting credentials. However, the connected Repository screen previously hid its token input. After a reload, the supplied request token was lost and could not be re-entered without disconnecting. The deployed browser was observed sending `X-GitHub-Token` before reload and sending no token after reload. Requests then use the server fallback, if configured, or public unauthenticated access.
2. The previous repository-state change (`f9e540e`) made **every** frontend analysis request send `force_refresh: true`, including ordinary analysis and retries. This bypassed the existing same-commit snapshot. One normal collection needs 42 file reads for this repository, so repeated full scans can exhaust a 60-request public bucket quickly. Snapshot consumers also performed repeated HEAD checks, a missing-snapshot inspection resolved HEAD twice, and the mounted AI workspace and Repository view requested the same branch listing concurrently.

The configured **local** server token is independently invalid: the existing GitHubService sent it to `/user` and GitHub returned 401. It was not silently downgraded to anonymous access. The local `.env` was left untouched.

**Production qualification:** Render validation returned 429 without a request token and 200 with the valid request token. A subsequent real deployed frontend/backend analysis with the valid token returned 200 and grounded the repository. The original production error did not include upstream rate headers, and Render's private logs/environment were not accessible. Therefore the original production limit cannot honestly be classified as primary versus secondary, or its fallback token source established, from that old response alone. The unauthenticated **primary** limit was reproduced and verified separately through the actual local frontend/backend flow using authoritative GitHub headers.

## Authentication

Verified path:

`Repository.tsx → batonApi.apiRequest → X-GitHub-Token → FastAPI Depends(github_token) → GitHubService → httpx → api.github.com`

- A nonblank request token takes precedence over `GITHUB_TOKEN`.
- Blank/missing request tokens fall back to a nonblank server token; otherwise no Authorization header is sent.
- Every GitHub method uses the existing shared `request` helper and `Authorization: Bearer <resolved token>`.
- No frontend direct GitHub API client or second backend GitHub integration was found. The other httpx client is the existing Gemini provider.
- The actual browser analysis request was observed carrying the valid token; only presence/match booleans were retained.
- The existing Git credential used for the earlier authorized push was accepted by `/user` through the same GitHubService. Account/profile data was discarded. The credential was used only in memory and never printed, written to files, or persisted in browser storage.
- Resolved tokens now retain only their safe source classification (`request`/`server`), fixing misleading diagnostics when a dependency had already selected the server fallback.

## Rate-limit evidence

These are sampled responses, not a claim that the counters remain unchanged:

| Observation | GitHub status | Limit | Remaining | Used | Reset (UTC epoch) | Retry-After |
|---|---:|---:|---:|---:|---:|---|
| Local configured server token, `/user` | 401 | not supplied | not supplied | not supplied | not supplied | absent |
| Accepted Git login, initial `/user` | 200 | 5000 | 4999 | 1 | 1791304297 | absent |
| Public unauthenticated failing file request through Baton | 403 | 60 | 0 | 60 | 1791304600 | absent |
| Final successful local authenticated analysis, final file | 200 | 5000 | 4701 | 299 | 1791304297 | absent |

The public primary-limit reset sample is `2026-10-06T16:36:40Z`; the authenticated reset sample is `2026-10-06T16:31:37Z`.

Baton normalizes the rate-limit API response to HTTP 429 while preserving `upstream_status: 403`, numeric `rate_limit` fields, `rate_limit_kind`, `retry_after`, token-presence and Authorization-presence booleans, and the safe token source. Presence of a header is not presented as proof that GitHub accepted a token: the acceptance diagnostic requires a successful authenticated `/user` request.

Classification:

- Remaining `0`: primary limit.
- Explicit secondary/abuse indication or Retry-After backoff: secondary limit.
- A 429 or rate-limit message without sufficient bucket evidence: unknown subtype, with backoff; no invented primary/secondary classification.
- 401: authentication failure.
- 403 without rate-limit evidence: permission failure.
- 404: not found/inaccessible.
- Connection and timeout failures have separate structured codes.

GitHub's documented guidance requires waiting for the reset when remaining is zero and honoring Retry-After/backoff: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

## Analysis request count

Measured through the actual local React frontend, FastAPI backend, and real GitHub API:

| Operation | HEAD | Repository | Branch list | Recursive tree | Distinct files | Total GitHub requests |
|---|---:|---:|---:|---:|---:|---:|
| First collection after connection supplied a recent authorized HEAD | 0 | 0 | 0 | 1 | 42 | **43** |
| Explicit refresh requiring a fresh HEAD and uncached pinned tree | 1 | 0 | 0 | 1 | 42 | **44** |
| Ordinary same-commit snapshot reuse within the observation window | 0 | 0 | 0 | 0 | 0 | **0** |

Connection, access checks and repository browsing are separate from these analysis counts. An explicitly refreshed same-commit tree may also be reused within the short cache window, reducing the count by one. No source bodies or credentials were logged.

The canonical pipeline already passed one shared content map to its analyzer modules. No duplicate file reads across those modules were found in the real collection. Duplicate tree entries are now ignored before collection, and the existing GitHubService also has a request-local, commit-scoped content cache. It is cleared when collection finishes.

## Duplicate requests and fixes

- Concurrent same-repository/branch/folder analyses with the same authorization scope and store share one collection. A refresh can join a real collection but cannot accidentally be satisfied by a cache-only read.
- Synchronous frontend locks prevent two clicks in one React render from sending two analysis POSTs.
- Concurrent frontend branch-list requests share one in-flight API read.
- Successful HEAD/repository/branch/tree observations are cached and concurrent requests coalesced in the existing GitHubService, scoped by a digest of the resolved token. An unauthenticated request or a different token cannot reuse another token's authorization observation.
- Observations expire after **60 seconds** and are bounded to 256 entries/40 MB; individual entries over 4 MB are not retained. Explicit refresh bypasses the HEAD observation cache.
- Analysis defaults to snapshot reuse. Explicit Refresh/Re-analyze bypasses the snapshot. Invalid or stale cached snapshot identities are recollected.
- Rate-limit backoff is enforced in both the UI and backend. Repeated requests with the same token do not keep calling GitHub before reset/backoff. A different token can be checked without waiting for the previous token's bucket.
- Connection/timeouts/GitHub API failures during collection are propagated instead of silently turning into omitted files and an apparently successful snapshot.
- Successful snapshot consumers reuse canonical intelligence; they do not collect trees or source files. After the 60-second authorization/HEAD observation expires, an access/current-HEAD check may occur, but this is not a repository rescan.

## Backend and frontend changes

Backend adds safe response metadata and metrics, bounded authorization-scoped observations, request-local content reuse, duplicate collection prevention, strict cache identity reuse, correct backoff and timeout handling, and `GET /api/v1/github/access` using the existing GitHubService. That diagnostic is briefly cached/coalesced and returns no account information.

Frontend preserves the existing design. The connected Repository view now provides an optional password input and **Check GitHub access**, explains that tokens must be re-entered after reload, and reports only safe access/bucket metadata. Rate-limit panels show requests remaining and reset time when supplied, distinguish secondary backoff, and disable immediate retries. Tokens remain memory-only. The existing canonical analyzer, snapshot store, context generator, and AI provider/reasoning architecture are retained.

## Files changed

Only these files are part of this change:

1. `baton-backend-v1/app/api/deps.py`
2. `baton-backend-v1/app/api/routes/github.py`
3. `baton-backend-v1/app/core/exceptions.py`
4. `baton-backend-v1/app/services/github_service.py`
5. `baton-backend-v1/app/services/analysis_service.py`
6. `baton-backend-v1/tests/conftest.py` — new
7. `baton-backend-v1/tests/test_github_rate_limits.py` — new
8. `baton-frontend/src/lib/api/batonApi.ts`
9. `baton-frontend/src/lib/workspaceStatus.ts`
10. `baton-frontend/src/hooks/useRetryBackoff.ts` — new
11. `baton-frontend/src/components/ui/StatusPanel.tsx`
12. `baton-frontend/src/components/workspace/sections/Repository.tsx`
13. `baton-frontend/src/components/workspace/sections/Analysis.tsx`
14. `baton-frontend/src/components/workspace/sections/AIWorkspace.tsx`
15. `baton-frontend/tests/repository-states.e2e.cjs`
16. `baton-frontend/tests/github-live.e2e.cjs` — new, opt-in real API test
17. `GITHUB_RATE_LIMIT_AUDIT.md` — this report

No environment file, generated context, snapshot architecture, AI provider, dependency lockfile or general design stylesheet was changed.

## Tests

- Full backend: **250 passed**, one existing Starlette/httpx deprecation warning, **19.37 seconds**.
- Repository-state browser regression: **28 checks passed**, including error categories, primary reset display, secondary backoff expiry without auto-retry, connected token re-entry without persistence, same-snapshot navigation, branch invalidation, late responses and mobile overflow.
- Existing workspace browser regression: passed (grounded answer, protected role payload, pinned commit, artifacts, comparison, branch isolation, memory-only credentials, mobile overflow and explicit refresh).
- Frontend typecheck: passed.
- Frontend lint: passed.
- Frontend production build: passed; only the existing outdated Browserslist data notice.
- Git whitespace check: passed.
- Actual local frontend/backend public test: no-token connection/analysis succeeded with available quota, later produced the verified primary limit when that quota was exhausted; invalid token returned authentication failure; valid token produced grounded analysis with the authenticated bucket. A double click produced one analysis POST, Context Builder returned 200 without collecting source, and reopening the AI workspace did not trigger analysis.
- Actual deployed Vercel/Render frontend/backend test: authenticated analysis **HTTP 200**, **42 files**, **Repository grounded**, commit `3a7a550985975a73805974c0e80f7c720b6dc8f0`. A real browser reload subsequently sent **no request token**; the public snapshot happened to remain accessible in that run. This does not mean anonymous access is guaranteed when its bucket is exhausted.

The final expanded real frontend/backend live regression passed **9 checks**, including invalid-token classification, accepted authenticated bucket, successful analysis with double-click protection, ordinary repeated analysis with **zero GitHub requests**, Context Builder reuse, reopening chat, memory-only credentials, and recovering the authenticated snapshot after browser reload/token re-entry **without a rescan**.

Commands used for backend and frontend verification:

```powershell
# From baton-backend-v1; unique temp directory avoids Windows shared-temp issues
$auditTestTemp = Join-Path $env:TEMP ('baton-rate-' + [guid]::NewGuid().ToString('N'))
python -B -m pytest -q -p no:cacheprovider --basetemp=$auditTestTemp

# From baton-frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
# With BATON_PLAYWRIGHT_PATH, BATON_BROWSER_PATH and BATON_PREVIEW_URL set
node tests/repository-states.e2e.cjs
node tests/workspace.e2e.cjs
node tests/github-live.e2e.cjs
```

The live local test server uses the actual FastAPI application. Its invalid local server fallback was disabled **only in that test process** for the explicit no-token scenario, and the frontend's API URL was overridden **only in the Vite test process** to point at it. Neither environment file was edited. The deployed test uses the actual production frontend and Render backend without mocked routes.

## Remaining risks and publication

- A valid token is optional for public repositories, but their unauthenticated quota is small and may be shared by other traffic from the backend's egress IP. Authentication increases the bucket; it does not eliminate GitHub limits.
- The local configured server token needs replacement/removal by the operator if server fallback is intended. Render's fallback configuration and original upstream error headers were not accessible in this audit; no production secrets were changed.
- Authorization and current HEAD can be up to 60 seconds old while a matching observation is reused. Explicit refresh revalidates HEAD. Changed credentials never share an authorization observation. Snapshot and observation storage remain process-local and do not coordinate separate Render workers or survive restarts.
- The public repository's successful analysis has explicitly reported partial coverage/26 omissions under existing filtering and budgets. No complete coverage is claimed.
- Branch separation is covered by the backend and browser regression fixtures; a real branch switch on a second branch of the named public repository was not performed. Gemini-generated chat was not part of this GitHub audit; opening chat and snapshot consumption were tested.
- New-fix production deployment has not been verified. Git publication status is reported in the chat; testing the already deployed old integration successfully does not assert that the new code is deployed.
