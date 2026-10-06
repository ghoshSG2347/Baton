# Repository analysis states — audit and implementation report

## Root Causes Found

The displayed unavailable state comes from WorkspaceService.inspect catching a missing canonical snapshot. Inspection intentionally does not run analysis. The missing cache entry alone does not prove that analysis never ran: snapshots are bounded, process-local and are not restored after a backend restart. Production history/logs were unavailable, so the screenshot cannot distinguish a first analysis from cache loss.

The code audit identified these definite defects before editing:

1. AIWorkspace hard-coded “Repository grounded” and treated any available inspection as ready without checking repository, branch, folder or current HEAD.
2. Commit display used the analyzed commit, ignoring the known current_head when analysis was absent or stale.
3. Missing/stale analysis shared error treatment, generic refresh wording and duplicated internal warning text. Role/ownership configuration was mixed into the failure presentation.
4. The existing analyzer returned a cache hit for an unchanged commit; the refresh button could not force collection again.
5. The earlier GitHub error normalization converted 409 into 502, defeating the existing empty-repository checks.
6. Ask Baton remains mounted when navigating to Analysis. Successful analysis in that separate view did not notify it to inspect the newly created snapshot.
7. Branch-loading failures were swallowed. Repository branch lists did not hydrate for a previously connected repository. Branch/file/analysis results lacked cancellation in some views.
8. Analysis used a hard-coded main fallback rather than the repository’s default branch.
9. Missing-inspection response fields did not match the complete frontend identity/coverage contract. The bounded store could refuse a snapshot without the analysis operation reporting that failure.

The canonical store already keys snapshots by repository + branch + commit + folder + analysis version. No second analyzer, cache, scanner or context engine was introduced.

## Files Changed

- `baton-backend-v1/app/api/routes/analysis.py`
- `baton-backend-v1/app/schemas/analysis.py`
- `baton-backend-v1/app/services/analysis_service.py`
- `baton-backend-v1/app/services/context_service.py`
- `baton-backend-v1/app/services/context_snapshot.py`
- `baton-backend-v1/app/services/github_service.py`
- `baton-backend-v1/app/services/workspace_service.py`
- `baton-backend-v1/tests/export_workspace_fixtures.py`
- `baton-backend-v1/tests/test_context_system.py`
- `baton-backend-v1/tests/test_workspace_final.py`
- `baton-frontend/src/components/workspace/sections/AIWorkspace.css`
- `baton-frontend/src/components/workspace/sections/AIWorkspace.tsx`
- `baton-frontend/src/components/workspace/sections/Analysis.tsx`
- `baton-frontend/src/components/workspace/sections/ConflictRadar.tsx`
- `baton-frontend/src/components/workspace/sections/ContextBuilder.tsx`
- `baton-frontend/src/components/workspace/sections/Integration.tsx`
- `baton-frontend/src/components/workspace/sections/PromptBuilder.tsx`
- `baton-frontend/src/components/workspace/sections/Repository.tsx`
- `baton-frontend/src/hooks/useWorkspaceState.ts`
- `baton-frontend/src/lib/api/batonApi.ts`
- `baton-frontend/src/types/index.ts`
- `baton-frontend/tests/workspace.e2e.cjs`
- `baton-backend-v1/tests/test_repository_states.py`
- `baton-frontend/src/components/ui/StatusPanel.css`
- `baton-frontend/src/components/ui/StatusPanel.tsx`
- `baton-frontend/src/lib/workspaceStatus.ts`
- `baton-frontend/tests/repository-states.e2e.cjs`
- `REPOSITORY_STATES_REPORT.md`

## Backend Fixes

- Added optional force_refresh to the existing analysis request and service; normal cache reuse remains the default. Explicit frontend analysis/refresh bypasses a matching cache entry and re-runs the same collection/pipeline.
- Verify that the generated result is retained in the existing bounded store. Failed refresh does not replace the last valid snapshot with a failed result.
- Preserve GitHub commit-query 409 as empty_repository. Empty inspection is a normal state and does not repeatedly fail through the recovery path.
- Distinguish snapshot_required, snapshot_stale and snapshot_invalid errors and return explicit inspection state, current HEAD, full identity/coverage shape, and canonical project classifications.
- AI configuration readiness checks the existing required provider and operator settings. It is separate from snapshot validity.
- The context generator, canonical intelligence model and provider reasoning behavior are unchanged. Project classifications are taken from the canonical model through ContextService.

## Frontend Fixes

- Ready requires an available canonical inspection whose repository, branch, folder and analyzed commit match the current HEAD, with a valid snapshot identity/status.
- Current HEAD is displayed independently of whether analysis exists, including during analysis and after an operation failure when HEAD was previously resolved.
- Scope and request epochs prevent late branch/analysis responses from becoming current. Branch changes clear conversation/artifacts/comparison; repository changes remount/reset the active workspace.
- Completed Analysis-view work signals the existing Ask Baton workspace to re-inspect. Returning to Ask Baton checks HEAD without discarding a still-current conversation.
- Repository hydration loads branch metadata; selected-branch tree reads and file reads reject canceled/stale completions. Existing in-memory GitHub tokens are reused during repository switching.
- The API client preserves structured categories and validates inspection/branch/tree response shape so malformed data becomes a safe failure rather than a render crash.
- Starting a new chat does not erase a repository analysis error.

## State Model

| Condition | State | Action / chat |
|---|---|---|
| No connected repository | DISCONNECTED | Connect repository; chat disabled |
| Resolving HEAD and existing analysis | CONNECTING | Loading; chat disabled |
| Known HEAD, no matching stored analysis | NOT_ANALYZED | Analyze branch; chat disabled |
| Explicit analysis request running | ANALYZING | Honest progress; chat disabled |
| Valid identity, analyzed commit equals HEAD | READY | Refresh analysis; chat enabled if AI is configured |
| Same repository/branch/folder, different commit | STALE | Re-analyze branch; chat disabled |
| Invalid identity/analysis response | SNAPSHOT_INVALID | Re-analyze branch; chat disabled |
| Analysis operation failed | ANALYSIS_FAILED | Retry analysis; chat disabled |
| Transport/backend failure | REQUEST_FAILED | Actionable request error |
| Authentication/permission failure | PERMISSION_DENIED | Check authorized access |
| GitHub request quota exceeded | RATE_LIMITED | Retry later or use an authorized token |
| Invalid URL or inaccessible repository/branch | INVALID_REPOSITORY | Correct URL, branch or access |
| No commits or an empty analyzed tree | EMPTY_REPOSITORY | Neutral empty state; chat disabled |
| AI server setup incomplete | CONFIGURATION_INCOMPLETE | Neutral configuration notice; valid context/artifacts remain available |

Role and ownership are configuration, not grounding errors. Project-wide is shown for project context; selected developers retain their actual configured role and folders. Tokens and snapshots are not persisted in browser storage.

## UX Improvements

One StatusPanel/ErrorStatus pattern is used for repository, analysis, context, prompt, integration, conflict and chat failures. It supports severity, sentence-case title, explanation, actions and optional collapsed technical details. Missing analysis and stale snapshots use amber; ordinary configuration/empty states are neutral; actual failures use restrained red; current analysis retains Baton green. Layout, navigation, fonts, dark theme and existing controls are preserved.

Working Context now reflects loading, missing, stale, invalid, failed and ready states. It shows the current branch/commit and the appropriate analysis action. Limited coverage and omitted files remain visible warnings, with the omission manifest available. Specification-only projects are identified from canonical classification without inventing implementation. The disabled composer explains what is needed. Empty chat content no longer scrolls/clips its own heading.

Visual verification artifacts (ignored local test output):

- baton-frontend/.test-output/analysis-required-desktop.png
- baton-frontend/.test-output/analysis-required-mobile.png
- baton-frontend/.test-output/workspace-desktop.png
- baton-frontend/.test-output/workspace-mobile.png

## Tests

- Backend full suite: 227 passed, one pre-existing Starlette/httpx deprecation warning.
- Frontend typecheck: passed.
- Frontend lint: passed, no errors or warnings.
- Frontend production build: passed; pre-existing Browserslist age warning.
- Repository-state browser checks: 24 passed.
- Existing workspace browser regression checks: passed on the final run.
- git diff --check: passed.

Browser tests exercise the actual React application against isolated responses exported through canonical Part 1/2/3 services. They cover missing/valid/stale snapshots, known HEAD, analysis start/success/failure, explicit refresh, Analysis-view notification, branch/repository isolation, late responses, GitHub 401/403/404/rate limit, transport/timeout, invalid identity, neutral role/ownership, empty/specification-only repositories, omitted coverage, provider configuration and mobile overflow. They also retain grounded answers, role boundaries, source navigation, artifact generation/download/Escape, branch comparison and credential persistence checks. They do not certify live GitHub/Gemini access.

Backend checks cover canonical creation -> inspection -> forced refresh -> changed HEAD -> re-analysis, cache identity, empty commits/trees, specification classification, bounded-store rejection, preservation of the last valid snapshot after failed refresh, and the request-to-analyzer force_refresh contract. Existing credential/authorization/context tests pass.

Commands:

- Backend: python -B -m pytest -q -p no:cacheprovider --basetemp=<unique task temp directory>
- Fixture export: python -B -m tests.export_workspace_fixtures
- Frontend: npm.cmd run typecheck; npm.cmd run lint; npm.cmd run build
- Browser: node tests/repository-states.e2e.cjs and node tests/workspace.e2e.cjs, with BATON_PLAYWRIGHT_PATH set to the bundled Playwright package, BATON_BROWSER_PATH set to the installed Chrome executable, and BATON_PREVIEW_URL=http://127.0.0.1:5174/

## Remaining Issues

- Production deployment has not been verified; Git publication status is reported in the chat.
- Deployed Render public-repository validation initially timed out; the retry returned HTTP 429 with github_rate_limit. Invalid URL validation returned HTTP 400 with invalid_repository_url. Live branch/analysis/refresh checks were blocked by that rate limit, not verified by the isolated tests.
- Authenticated public/private repository checks were not run because no valid authorized token was available. No credential/configuration values were changed or exposed.
- The existing canonical snapshot cache remains bounded and process-local. Restart/eviction can require explicit re-analysis; multiple backend instances do not share it. Durable storage would be a separate architectural change and was intentionally not added.
- Render logs/settings and the original repository’s analysis history were unavailable. The precise historical reason for its missing cache entry remains unverified.
