# Baton — Product Completion and Verification Audit

## Scope and baseline

Updated 2026-10-07 in the Windows PowerShell workspace. Repository: https://github.com/ghoshSG2347/Baton. Branch: main. Starting commit: `96f1e37a3ca252b1b9684c3d4a57ac7eaf27ac65`. Initial working tree clean; origin fetch/push matched the requested repository. The user authorized implementation, verification, documentation, commit and ordinary push. No force push, reset, destructive cleanup, framework replacement, new database or new intelligence/provider architecture was used.

[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) is the canonical subsystem reference. This report replaces obsolete completion findings in place. OBSERVED denotes inspected implementation; VERIFIED denotes an executed check with a stated scope; UNKNOWN denotes unavailable evidence. Local fixtures are not live Gemini or production deployment certification.

## Root causes and disposition

| Finding | Root cause | Result |
|---|---|---|
| Context controls disconnected | Frontend submitted only repository/branch/folder/include_markdown | FIXED: task, member boundaries, context type, constraints and UTF-8 byte limit use the existing ContextRequest/API |
| Misleading context metadata | Commit extracted from Markdown regex; timestamp fabricated from browser time | FIXED: structured context identity supplies branch, commit and generation timestamp |
| Initial context state race | Folder synchronization always created a new configuration object, including an unchanged initial folder | FIXED: unchanged folder retains its configuration object; scoped epochs ignore obsolete results |
| Prompt surface not grounded | Standalone manual endpoint used default Baton label and ignored teammate scope | FIXED: canonical mode uses existing prompt artifact; explicit manual mode passes actual label and marks USER_PROVIDED text |
| No member edit | Team exposed add/delete only | FIXED: edit uses existing persisted state, retains ID and ownership/protection fields; reload tested |
| Demo contamination | Loading a demo team could switch a connected workspace into demo mode | FIXED: demo-team loading is unavailable on connected live repositories |
| Live Overview fabricated readiness/activity | FRESH, 84 files, 3.2K tokens and demo events were unconditional | FIXED: existing inspection supplies measured coverage/identity and actual snapshot event; unavailable data is Unknown |
| New Chat retained draft | Handler cleared turns/ID but not composer text | FIXED: draft clears, pending chat aborts, snapshot/scopes remain, no analysis/inspection request |
| Expired conversation retry loop | All HTTP 409 responses treated as snapshot errors, stale conversation ID retained | FIXED: typed conversation errors; unusable IDs clear; error remains actionable without snapshot rebuild |
| False cross-branch signal | Repeated path within one branch counted twice; message asserted changed files | FIXED: per-branch path deduplication and inventory-presence wording |
| Empty integration falsely compatible | `not unmatched_calls` was true with no consumers/routes | FIXED: compatible=null and insufficient evidence; UI cannot report ready |
| Legacy method mismatch | Method stripped before route comparison | FIXED: explicitly different methods do not match; unqualified legacy paths remain unknown-method matches |
| Unvalidated response identity/integrity | Several frontend workspace calls only cast JSON | FIXED: chat/artifact/source/comparison identity guards; chat structure and artifact type/filename/SHA-256 checks |
| Generic source policy weaker than workspace source | Arbitrary paths and owner/repository values accepted | FIXED: existing URL grammar validates all service repository entry points; generic source rejects traversal/credential paths before network |
| Provider failures lacked codes | Configuration/provider failures exposed status/text only | FIXED: safe AI configuration/provider/session/path codes reach existing error UI |

All changes preserve the visual design, React/FastAPI structure, canonical analyzer, snapshot store, context generator, retrieval and Gemini adapter. No new GitHub implementation exists.

## Workflow verification matrix

| Workflow | Status and evidence |
|---|---|
| Landing/connect | VERIFIED WORKING: browser connection and actual GitHub validation; original No-Way-Home3 validation returns 200 in production |
| Repository/branches | VERIFIED WORKING within existing first-100-branches boundary; safe distinct auth/quota/network/not-found states |
| HEAD versus snapshot | VERIFIED WORKING: fixture tests preserve current HEAD, block stale/mismatched identity and retain pinned commits |
| Explicit analysis | VERIFIED WORKING: no implicit context/chat collection, double-click dedup, same-state reuse, force refresh and failed/late analysis tests |
| Snapshots | VERIFIED WORKING locally; PARTIALLY WORKING operationally because stores remain process-local and eviction/restart can lose state |
| Working Context | VERIFIED WORKING: missing/running/ready/stale/invalid/empty/partial/spec/provider-unconfigured states; omissions remain explicit |
| AI Workspace | VERIFIED WORKING for context/artifacts/source/compare; live Gemini is BLOCKED by operator configuration |
| New Chat | FIXED and fixture-verified: clears draft/history/ID, preserves snapshot, does not rescan; first submitted question creates backend ID, follow-up sends it |
| Chat/citations/actions | VERIFIED WORKING in service/browser fixtures, including binding, revision, ownership/evidence validation and session expiry; live provider quality UNKNOWN |
| Artifacts | VERIFIED WORKING: all nine types preview/download in browser; real local-backend/snapshot HTTP checks return 200 with matching commit/hash |
| Source | VERIFIED WORKING: pinned README HTTP read; fixture navigation preserves chat; traversal/credential paths rejected before network |
| Compare | VERIFIED WORKING in service/browser fixtures; diff-of-retained-inventory semantics, no Git merge; live two-branch production certification not performed |
| Team | FIXED: add/edit/delete, ID preservation and persistence/reload tested; no server team database or verified GitHub ownership |
| Context Builder | FIXED: controls reach existing API; real context HTTP 200 renders; missing exact-folder snapshot still requires explicit analysis |
| Prompt Builder | FIXED: grounded artifact versus explicit manual provenance; target teammate/boundaries/constraints forwarded |
| Conflict Radar | FIXED and PARTIALLY WORKING: honest inventory overlap, not changed-line or merge conflict detection |
| Integration | FIXED and PARTIALLY WORKING: detected method/path matching, branch/commit/omission metadata and insufficient evidence; no payload/runtime proof |
| Overview | FIXED: measured snapshot state/coverage/identity; demo values restricted to demo mode; no durable activity history |
| Change Repository | VERIFIED WORKING: clears repository/team/active evidence; preserves memory GitHub token as existing behavior |
| Reset/settings | VERIFIED WORKING: memory-only access key; reset clears connection/team/artifact state and credentials |
| Reload/token reentry | VERIFIED WORKING with actual frontend/backend/GitHub: token cleared on reload; reentry restores authorized snapshot without rescan |

## Backend and frontend checks

- Backend full suite: `python -B -m pytest -q -p no:cacheprovider --basetemp=<unique temporary directory>`: **266 passed**, 11.99 seconds on final backend run. One existing Starlette/httpx deprecation warning.
- Frontend typecheck: PASS.
- Frontend lint: PASS, no warnings after request-epoch cleanup correction.
- Frontend build: PASS, 2178 modules. Existing Browserslist database-age warning; no dependency migration performed.
- Repository-state browser suite: **29 checks passed** covering lifecycle/error/quota/late-result/mobile/repository-switch states.
- Workspace browser suite: PASS, expanded to assert New Chat draft/ID clearing, ID reuse on follow-up and conversation expiry without reinspection, alongside citations/source/artifacts/comparison/mobile.
- Product-completion browser suite: **8 checks passed**, covering builder payloads, team add/edit/delete/reload, measured Overview, insufficient integration evidence, all nine artifact hashes/previews/downloads and settings/reset.
- Live GitHub browser suite: **9 checks passed** on final run. Anonymous access correctly reported an exhausted quota; that run did not perform anonymous collection. Authenticated analysis/reuse/context/reload succeeded.

A first live browser attempt timed out waiting for the generated context header despite HTTP 200. The test now explicitly awaits the context response, and unchanged initial-folder synchronization avoids invalidating an in-flight request. Final live rendering passed. Failures during implementation were corrected and checks rerun; they are not represented as passed runs.

## Live GitHub and request accounting

Actual React → local FastAPI → GitHub REST tests used the existing Git credential in memory only. Neither tests nor reports retain the token. The original configured local fallback remains invalid; tests cleared that fallback only inside the test server process.

- Anonymous access observed remaining 4/60, then collection reached zero and correctly returned Baton 429 for GitHub 403. A failed quota-limited attempt did not become usable intelligence.
- Request token accepted in the authenticated 5000-request bucket; invalid token returned authentication failure, not rate-limit failure.
- Successful public ML collection retained commit `3a7a550985975a73805974c0e80f7c720b6dc8f0`, 42 analyzed files and 26 omissions. With an already observed authorized HEAD, collector metrics were **1 tree + 42 files = 43 GitHub requests**. HEAD resolution is separate and can add one request when its observation expires.
- Immediate ordinary same-state analysis: **0 collection requests**, no tree/files. Double click issued one analysis POST.
- Context generation and reopening chat issued no analysis POST. New Chat issued zero inspection/analysis requests in the fixture regression; first/follow-up service tests reuse retained evidence. Live provider first/follow-up request counts could not be measured because AI configuration is incomplete.
- Nine real artifact HTTP calls returned matching hashes/identity without tree/file collection; a pinned README source read used one file request. HEAD observations may refresh after 60 seconds.

No automatic retry, whole-repository scan on every message, or rate-limit error suppression was introduced.

## Production/deployment verification

Current remote Render `/api/health`: **200**. Vercel page: **200**. Production validation of `https://github.com/ghoshSG2347/No-Way-Home3` with the existing authorized request token: **200**, allowed Vercel CORS origin and credential absent from response.

These checks apply to the deployment available during the audit, not the new commit before rollout. Public health does not prove deployed Git SHA, environment values, multi-worker behavior, new UI delivery or live Gemini availability. VITE_BATON_API_URL remains build-time public configuration; changing it requires rebuilding the frontend. Render secret configuration belongs outside Git. No dashboard secrets were changed.

## AI/Gemini verification and limitation

Local safe presence check: GEMINI_API_KEY present; GEMINI_MODEL absent; BATON_ACCESS_KEY absent. Live inspection reported provider configured=false. No billable Gemini request was attempted with guessed configuration. The existing server-only REST provider, bounded lexical retrieval, ownership/evidence/action validation and process-local conversation store remain intact.

Backend/service/browser fixtures verify first message, follow-up ID/revision, scope isolation, citation/source identity, exports and safe failure states. This does **not** verify relevance/quality/latency/quota of real Gemini output or production New Chat. The operator must configure GEMINI_MODEL and BATON_ACCESS_KEY alongside a valid server-side GEMINI_API_KEY, then repeat live chat/quality acceptance tests.

## Security re-audit

No credential logging or persistence was introduced. GitHub/Google hosts remain fixed; repository source is statically parsed, not executed. Generic file display and workspace source guards reject traversal and credential files, including environment templates. Analysis can still collect allowed environment templates through the existing service policy and sanitize every assignment value; regression tests protect this distinction. owner/repository grammar is reused rather than adding an HTTP integration. Provider errors never echo upstream bodies. Frontend errors redact known/signature credentials. Snapshot/context sanitization and the safe JSON response boundary remain active. Artifacts verify content hashes before download. Raw HTML, remote images and active links remain suppressed in AI Markdown.

Repository instructions remain untrusted data under the existing provider system policy. Returned actions are guidance and must cite supplied editable evidence; no repository writes execute. Prompt injection resistance and redaction are not a mathematical guarantee. Ordinary APIs remain unauthenticated when BATON_ACCESS_KEY is unset; CORS is not authentication. Unknown secret formats, global inbound request-size limits, shared-key tenancy, process-local state and the 60-second permission/HEAD window remain limitations.

**VERIFIED:** Actual configured secrets and the existing Git credential were absent from staged content and every tracked file. No credential signature appeared in the staged diff; staged whitespace review passed. Environment files, keys, dependencies, build outputs, screenshots and generated fixtures remain ignored and unstaged.

## Remaining limitations and technical debt

Static extraction still has shallow wrapper/alias/dynamic API handling. The prior full static Baton self-analysis included test/detector strings and produced false project-family/routes; runtime/source cross-checks remain necessary. No new scanner or semantic engine was built. Integration cannot prove payload/auth/runtime compatibility; Conflict Radar cannot prove changed hunks/merge conflicts. Branch pagination remains first 100; collection omissions are real. Snapshot/conversation/cache state remains bounded and process-local, without durability or worker sharing. No accounts, server team persistence, live provider certification or production-revision endpoint exists.

Existing 51 tracked Python bytecode files, two TS build-info files, unused Supabase/legacy schema, unpinned Python/runtime dependencies, no tracked CI/Docker workflow and broader inbound schema bounds remain separate debt. No unrelated cleanup was performed.

## Documentation and delivery rule

PROJECT_CONTEXT.md was revised in place to remove obsolete disconnected-control/placeholder claims and document current request/identity/error/security behavior. This audit records executed evidence and limits. Root AGENTS.md enforces the user-requested rule: each future engineering task must read both documents and update them before final commit, preserving truthful local/live distinctions.

Implementation delivered in commit `ed870ea8a5b294f332cfb20b476a7bb46a2b1198` (`fix: connect Baton product workflows to canonical snapshots`), pushed normally to origin/main. Local HEAD and remote refs/heads/main matched, with a clean working tree after delivery. Deployment rollout is independently verifiable and is not inferred from Git push.

**Documentation refresh, 2026-10-07:** Starting tree clean at the delivered implementation commit; remote SHA equality rechecked. PROJECT_CONTEXT.md was reconciled with GitHub service/route validation, environment-template analysis versus display protection, canonical/manual prompt flows, team editing, recorded verification counts and the root engineering rule. Obsolete recommendations were removed in place. This pass changes documentation only; prior test/live results are retained as dated evidence, not claimed as rerun. Markdown sections, whitespace and changes are checked before the documentation commit.
