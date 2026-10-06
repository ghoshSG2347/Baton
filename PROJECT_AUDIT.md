# Baton — Complete Project Audit

## Audit scope and evidence

**OBSERVED:** Audit performed 2026-10-06, repository `https://github.com/ghoshSG2347/Baton`, Windows PowerShell workspace. Initial branch `main`; initial HEAD `68fa524c406faf58cb0229dfc9f4b0bafb661407`; working tree clean and no untracked personal work. Origin fetch/push both point to the requested repository. User authorized audit, necessary small corrections, documentation, commit and ordinary push to main. No force/reset/clean/branch deletion occurred.

This is the forensic report; [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) is the stable subsystem reference. Evidence categories have the same meanings there: OBSERVED source/config; VERIFIED executed checks; DOCUMENTED intent; DERIVED mechanical relationship; INFERRED uncertain interpretation; UNKNOWN unavailable evidence; CONFLICTING incompatible claims; RECOMMENDATION future work; USER_PROVIDED operator input. Passing tests are not a production completeness certificate.

## Complete repository inventory

**OBSERVED:** Initial tracked inventory: 220 files: 152 backend, 64 frontend, four root files. Root contained .gitignore, master solution blueprint, repository-state report and GitHub-rate audit. No root README. No shared runtime package, database migration, Docker config, CI workflow or application AGENTS.md was tracked/found. Backend and frontend have separate dependency/build/deployment roots.

| Group | Contents inspected | Treatment |
|---|---|---|
| Backend application | FastAPI entry/routes/deps/core/schemas; all service, canonical intelligence, analyzer and generator families; utilities | Architectural source; route/schema/runtime cross-checks |
| Backend tests/scripts | 14 test modules, conftest, repository JSON fixtures, fixture exporter, manual public acceptance helper | Tests inspected and full suite executed; opt-in helper not blindly treated as current results |
| Frontend application | React entry/App, shared state/hooks/API/types/redaction/status, nine workspace sections, landing/UI/CSS | Architectural source; browser tests exercise existing UI |
| Frontend harnesses | workspace.e2e.cjs, repository-states.e2e.cjs, github-live.e2e.cjs | Executed sequentially; fixture vs live evidence separated |
| Build/config | package.json/package-lock, Vite/TS/eslint/Tailwind/PostCSS, requirements, Render/Vercel, env templates, index.html | Inspected; npm/pip tooling and local versions checked |
| Static assets | public/baton.svg | Presentation asset, not intelligence source |
| Documentation | Root blueprint/prior audits, backend/frontend context, Part 1–3 validation reports, backend GitHub validation audit, example context | Historical statements checked against current code; contradictions recorded |
| Generated tracked files | 51 Python .pyc, two TypeScript .tsbuildinfo | Existing repository debt; inspected as inventory/credential scan only; not edited/staged |
| Ignored local material | backend .env, frontend .env.local, node_modules, dist, .test-output, __pycache__, .pytest_cache | Contents of installations/build/screenshots/cache excluded from architecture; no secrets dumped |

**OBSERVED:** .gitignore excludes environment files/dependencies/build/Python caches/logs/IDE output; tracked legacy generated files remain tracked despite those ignore rules. Environment templates already tracked remain available despite broad `.env.*` ignore. No Python lock/runtime pin or Node engine/runtime pin is present. Python requirements are unpinned and include pytest in production installs. Playwright is externally supplied for optional browser harnesses, not a package.json test dependency/script.

## Git history

**OBSERVED:** 24 commits existed at audit start. Meaningful milestones:

| Commit/milestone | Evidence/interpretation |
|---|---|
| `1d1408e` initial blueprint; backend commits through `fe0c92a` | Backend/design preceded frontend |
| `4e3002b` frontend added; `df0aeac` frontend context | Separate packaged frontend introduced into same repo |
| `859834d` deployment; `ccdee4f` CORS canonical URL correction | Deployment configuration evolved |
| `56ccdec` repository switch | Clear repository-specific UI state while preserving memory token |
| `aa4c1e0`, `62463fa`, `135e3c3` recent larger work | Canonical intelligence/context/workspace present in current source; vague titles alone do not prove each feature's origin |
| `7729759` | Safe differentiated GitHub validation error propagation |
| `f9e540e` | Explicit repository analysis lifecycle/status corrections |
| `68fa524` | Auth/quota diagnostics, short-lived observations, coalescing and analysis reuse |

No framework/database migration was observed. Current code, not commit messages or previous reports, established implementation facts. Final commit is the subsequent audit commit; identify it via `git log -1` or path history, avoiding a self-referential hash inside committed Markdown.

## Architecture findings

**OBSERVED:** React 18/TypeScript/Vite 5/Tailwind 3 client communicates JSON HTTP with FastAPI. GitHubService accesses fixed GitHub REST; AnalysisService performs bounded commit-pinned reads and passes sanitized evidence to one canonical pipeline. MemorySnapshotStore retains RepositoryIntelligence 1.1; ContextService projects Context Model 2.0. WorkspaceService reuses it for lexical retrieval, deterministic artifacts, source and branch comparison; Gemini selects evidence IDs and labeled reasoning. No database, autonomous repository editing, merge engine, embeddings or server user account system exists.

**OBSERVED:** Older standalone Prompt Builder is a pasted-context formatter; Conflict Radar uses inventory paths; Integration explicitly analyzes whole frontend/backend branches and compares detected methods/routes. These paths cannot be described as the same grounded artifact workflow.

**VERIFIED:** Runtime OpenAPI listed the 17 schema-visible application operations; `/api/health` is an additional hidden compatibility alias. Framework docs/OpenAPI utility routes remain enabled. Frontend request headers and route inputs were cross-checked. PROJECT_CONTEXT.md contains the complete API table including request/response/error/auth/use and aliases; it was checked against router source, Pydantic models and runtime schema.

## Findings and disposition

| ID | Evidence/severity | Exact finding | Disposition |
|---|---|---|---|
| A01 | VERIFIED, high correctness risk | ConflictRadar caught failed branch tree reads and substituted empty arrays, allowing a false “NO CONFLICTS DETECTED” result | Fixed by letting the existing outer error handler receive the real safe API error; regression browser check added |
| A02 | OBSERVED, high interpretation risk | Static analysis treats test fixture strings/detector patterns as implementation signals; self-audit produces spurious project families/routes | Documented; semantic/scoping overhaul outside minimal correction scope |
| A03 | VERIFIED/OBSERVED, medium | Standalone context purpose/member/budget controls are not sent; token budget only affects visual ratio | Documented; existing schema supports richer requests; no generator rewrite |
| A04 | OBSERVED, medium | Standalone prompts have hardcoded Baton repository label, manually pasted context, and unused live target-member field | Documented; grounded workspace prompt artifacts remain separate |
| A05 | OBSERVED, medium | Live Overview hardcodes FRESH/84 files/3.2K tokens and DEMO_ACTIVITIES | Documented; not treated as live metrics |
| A06 | VERIFIED, configuration | Local GITHUB_TOKEN fallback rejected by GitHub /user with 401 | Do not change/commit credentials; replace outside Git when operator configures environment |
| A07 | VERIFIED, configuration | Local Gemini key present, GEMINI_MODEL absent, BATON_ACCESS_KEY absent | Local chat cannot run; no live billable provider call attempted |
| A08 | VERIFIED, production quota | Render anonymous access produced GitHub 403 remaining=0 in 60-request bucket, mapped to Baton 429 | Real quota failure preserved; valid token accepted in 5000-request bucket |
| A09 | OBSERVED, security | Generic GitHub file endpoint lacks workspace source's sensitive-path/inventory policy; direct owner/repo fields less validated than repo_url | Documented; redaction is not a complete policy substitute |
| A10 | OBSERVED, availability/security | Legacy schemas/inbound body lack comprehensive byte/length bounds; API accessible if shared key unset | Documented; CORS is not API authentication or quota control |
| A11 | OBSERVED, deployment | Snapshots/conversations/observations are process-local; multiple workers can disagree and restart evicts state | Documented; no persistence layer introduced |
| A12 | OBSERVED, freshness | Authorized HEAD observations last 60s; changes/revocations can lag until expiry or explicit refresh | Documented as real freshness window |
| A13 | OBSERVED, shallow conflict detection | All shared blob paths count; no actual diff, merge base or hunk analysis; reason says changed without proof | Documented; no merge engine claim |
| A14 | OBSERVED, shallow integration | Only detected method/path calls compared; empty evidence can say compatible; payload types/auth not compared | Documented |
| A15 | OBSERVED, discovery debt | Branch list only first 100; truncated trees and omitted files limit completeness | Documented, tested omissions maintained |
| A16 | OBSERVED, build debt | 51 tracked bytecode + two TS build-info, unpinned Python/runtime, unused Supabase/legacy schema | Reported; no unrelated cleanup/dependency migration |

### Targeted correction

**OBSERVED:** Removed only the nested catch in `baton-frontend/src/components/workspace/sections/ConflictRadar.tsx`. A failed `getTree` now aborts comparison and reaches the component's existing ErrorStatus. It does not send `/conflicts` with fabricated empty inventories. Existing design, API/service, context generator and chatbot remain unchanged.

**VERIFIED:** Added one regression to `tests/repository-states.e2e.cjs`: fail tree with 404/github_not_found, assert safe repository/branch error and technical HTTP/code details, assert no conflict POST and no false success. Test setup initially needed a visible textarea selector because hidden AI remains mounted; a second adjustment checks the visible friendly title before opening collapsed technical details. Those harness corrections are reflected in the final passing suite.

## GitHub authentication, quotas and request counts

**VERIFIED:** Browser → batonApi → local FastAPI → shared GitHubService → actual GitHub exercised against public `ghoshSG2347/Alzheimer-Disease-Prediction-Model`, main, HEAD `3a7a550985975a73805974c0e80f7c720b6dc8f0`. Request observers retained token presence/equality booleans only, never credential content. Existing Git login was resolved in memory for the authorized audit, not saved to an environment file.

| Check | Actual result |
|---|---|
| Local anonymous validation/access | 200; access showed 56/60 remaining at that observation |
| Local anonymous analysis | Successful partial analysis, 42 text files with 26 omitted paths; anonymous availability differs from Render's shared quota |
| Invalid request token | Authentication failure, not rate limit; 401 with dedicated safe message |
| Authenticated access | GitHub accepted token, 4996/5000 remaining at browser observation |
| Explicit authenticated collection | Safe backend metrics: 1 commit + 1 tree + 42 file requests = 44 actual GitHub requests; no double analysis POST from same-render double click |
| Ordinary same-commit repeat | Backend metrics counts empty/total 0, no file/tree rescan |
| Context Builder + reopening Ask Baton | No additional analysis POST; backend logs show projection/inspect 200 without tree/file collection |
| Reload | Token cleared from browser request; reentry restores authenticated snapshot without analysis POST |
| Branch changes | Fixture/wire/service tests establish exact key isolation; real public HEAD remains identified, no live branch mutation |

**OBSERVED:** Connection browsing can add metadata, branches and branch-ref tree independently of analysis; cached branch-ref tree and commit-pinned tree are different keys. A recent valid HEAD can reduce fresh collection to one tree + N files; force refresh resolves HEAD. Numeric remaining values are historical observations, not current promises. Rate cooldown is credential scoped; changing credentials need not wait for anonymous quota. Repeated reads coalesce, but unrelated scopes/users are not globally throttled.

**VERIFIED:** Prior rate-fix implementation is present and working for the observed authenticated/anonymous paths. It does not abolish GitHub's real limits, fix invalid tokens, or establish live provider readiness. Wire tests cover environment fallback precedence, Authorization on each request, primary/secondary errors, Retry-After, backoff, timeout, deduplication and cache TTL/fresh bypass. Quota header presence does not prove authentication; /user 200 does.

## Production deployment observations

**VERIFIED:** Public endpoint checks during this audit:

| URL/check | HTTP/body result | What it proves |
|---|---|---|
| Vercel `https://baton-sigma-six.vercel.app` | 200 HTML | Frontend deployment responds; not proof of deployed Git SHA |
| Vercel served JavaScript | 200; Render API base and `/api/v1/github/access` present | Compiled frontend points to expected backend; dashboard value/SHA not disclosed |
| Render `/api/health` | 200, status ok/service baton-backend | Correct liveness alias exists |
| Render `/api/v1/github/access`, no token | 429; upstream403; primary; limit60/remaining0/used60; token_source none | New quota endpoint/error metadata deployed; server supplied no fallback for that request |
| Render `/github/access`, accepted request token | 200; authenticated true/source request; limit5000/remaining4998/used2 at observation | Actual accepted authenticated GitHub path |
| Render `/github/access`, invalid token | 401 github_authentication_failure | Invalid credentials distinguished safely |
| Render original `No-Way-Home3` validation with accepted token | 200; owner/repository correct; default main; visibility private; accessible true | Original repository is accessible with this credential, not anonymously guaranteed public |
| Production-origin OPTIONS with content-type/x-github-token | 200; allow-origin exactly Vercel URL | Relevant CORS preflight succeeds |

**OBSERVED:** Source Render health path/start/build commands and CORS align with these responses. Local ignored frontend env selects Render; the browser audit deliberately overrides VITE_BATON_API_URL to local backend in its process only. **VERIFIED:** Served Vercel JavaScript independently contains the expected Render API base. **UNKNOWN:** Dashboard env/root directories, deployed commit SHA, worker topology, provider configuration and production AI answers. No deployment dashboard/log connector was available. Local Uvicorn logs were inspected; remote quota metadata was observed, not invented from inaccessible Render logs. Full private repository content analysis was not performed.

## Snapshot, branch and failure verification

**OBSERVED/VERIFIED:** Exact owner/repo/branch/commit/folder/version matching; deep-copy isolation; eviction limits; default branch; partial coverage; auth checks before reads; changing commits; stale/invalid/missing/empty statuses; browser late-result guards and repository reset are covered by executed tests. Current canonical freshness rule resolves authorized HEAD then looks up exact key; HEAD cache adds up to 60s lag. Different credentials do not share permission observations.

Failures in auth/quota/network collection abort, preserving prior retained snapshots without silently presenting them as current. Explicit historical continuation has STALE warnings and current_head; normal UI continuation is false. Folder context cannot substitute a full-project snapshot. Browser refresh clears credentials/history but preserves nonsecret connection/team configuration and depends on backend process retention. No opening-chat/context implicit rescan was observed. Conflict Radar scan collects trees; Integration check can collect both branches; neither should be described as a snapshot-only consumer.

## Canonical context A–F verification

**VERIFIED:** Direct canonical pipeline/generator calls and existing executed tests exercised these cases. Fixed generated_at was used for deterministic equality. These are fixture tests, not six claims of production repository maturity.

| Case | Inputs/result | Accuracy limits |
|---|---|---|
| A rich README/architecture/rules | bookos fixture, 4 docs, candidate feature PARTIALLY_IMPLEMENTED, usable 25,727-byte context | Rich docs are retained intent, not completed runtime behavior |
| B docs-poor | frontend fixture, zero docs/requirements, usable 12,039-byte context | Documentation/requirements unknown; no invented product specification |
| C ML/data science | ml fixture, stage/dataset/model metadata, usable 19,637-byte context | Notebook cells static; no training/evaluation executed; binary artifact fixture collection differs from live filters |
| D frontend/backend monorepo | bookos fixture, real POST /api/ask-book/type/import/data relationships | Regex/literal extraction only; arbitrary wrappers remain unsupported |
| E specification-only | PRD fixture, both requirements NOT_DETECTED, usable 12,728-byte context | No runtime implementation inferred from spec |
| F limited coverage | Explicit synthetic omitted server/ai.ts reason file_count_limit; PARTIAL and snapshot_collection manifest | Synthetic omission flag check plus actual service limit/truncation tests and 26 omissions in real ML collection |

All five complete fixture calls with identical timestamp/options were byte-for-byte deterministic, commit anchored and usable. Existing tests additionally exercise role/ownership closure, protected contracts, narrow budgets, whole-record omissions, unusable budgets, secret/Markdown sanitization and no context I/O/rescan. “COMPLETE” describes supplied collection coverage, not feature quality or semantic accuracy.

## Static self-audit accuracy experiment

**VERIFIED:** Ran current pipeline against 166 eligible tracked text files from the whole Baton tree, excluding generated bytecode/build-info/known filtered assets. This is a local static experiment, bypassing GitHub's 100-file collection budget. It included application, tests, detector definitions and historical documentation.

Result: collection COMPLETE, 27 detected route declarations, seven API consumers (all from `tests/test_intelligence.py`), 120 data models, ten recognized documents, one resolved-import source, zero extracted formal requirements and 41 reported conflicts. Project types included ML/data pipeline/frontend/backend/full-stack/CLI/mobile/desktop/game/embedded/mixed. Baton is not actually all those products.

**DERIVED:** Fixture and detector string literals contaminate classification/route signals. The real `batonApi` wrappers are missed; absolute backend imports and `@/` frontend aliases are not resolved by the relative-import resolver. Historical docs amplify conflict noise. This is a concrete intelligence accuracy gap, not a complete feature verifier. The canonical context in this task was independently authored from source/runtime/tests, not blindly exported from this result. **RECOMMENDATION:** Establish source-vs-test/pattern provenance and wrapper/alias fixtures before making stronger semantic claims; avoid an unreviewed pipeline rewrite during a documentation audit.

## AI and security audit

**OBSERVED:** Gemini is implemented, with server-only key header, fixed endpoint, JSON evidence schema, provider concurrency/time/output caps, no hidden retry, and safe provider failures. Workspace does not accept unrestricted model-written project facts: selected evidence must exist and actions must satisfy evidence/ownership. Labeled reasoning can still contain semantic errors; ID validation alone does not prove relevance or truth.

Repository rules/docs are untrusted data in system prompt and quoted context records. Source/notebook/model execution was not found; no eval/exec/subprocess application path was found. Fixed dynamic imports in route auth load trusted app modules. Provider actions do not execute changes. Workspace source prevents traversal/out-of-inventory and secret-file reads; generic GitHub file reads have weaker policy. Raw HTML/images/links are disabled/suppressed in AI Markdown. Prompt exports to external agents still need source-content boundaries.

**VERIFIED:** Safe scan of all tracked files, including generated binaries, found no exact configured/request/Git-credential values. Credential values were never printed. Tests cover credential patterns/configured secrets, snapshots/projections/API redaction, malicious Markdown/source content, unknown evidence IDs, forbidden actions and conversation binding. Browser localStorage/sessionStorage contained no accepted token. These checks do not prove every unknown credential pattern is absent.

**OBSERVED:** Shared optional BATON_ACCESS_KEY is not per-user authentication; ordinary APIs are public when unset, while chat refuses missing backend key. Inbound request/global rate limits are incomplete; memory/cache/AI concurrency bounds are per process. Snapshots are not credential keyed, so the authorized HEAD read is essential and permission observations can lag 60s. No arbitrary user-specified external-host fetch feature exists, but direct owner/repo path validation should be consistent. No account/profile body is exposed by GitHub access diagnostics.

**UNKNOWN:** Live Gemini acceptance/quality, novel prompt injection robustness, load/penetration testing, provider spend, production dashboard secrets and actual worker isolation. No billable live Gemini call was made because local model/operator configuration is absent. This audit did not claim a security certification.

## Documentation contradictions and legacy/dead-code findings

| Source claim | Current source/verified result | Action |
|---|---|---|
| FRONTEND_CONTEXT: changed-file conflicts | Whole branch inventories, no diffs | Canonical context clarifies; historical document marked with current reference |
| FRONTEND_CONTEXT: token-budgeted/member standalone context | UI fields not forwarded by generateContext | Recorded as incomplete; no generator changes |
| Blueprint: external AI handoff model | Current Gemini WorkspaceService already exists | Preserve intent/history; do not present blueprint as implementation inventory |
| Older backend stateless descriptions | Bounded process-local snapshots/conversations/observations | Canonical storage model documented |
| documentation_analyzer comment “NEVER full file” | Excerpt object bounded, but pipeline also retains full sanitized collected docs | Record exact distinction |
| pipeline docstring stores snapshot | AnalysisService saves; pipeline returns model | Responsibility map corrects attribution |
| Error propagation is globally generic | Current GitHub codes distinguish auth/quota/permission/not-found/network/timeout | Executed wire/live checks support current behavior |

**OBSERVED:** Supabase dependency is unused in src. `schemas/team.py` does not represent current MemberContext and has no route. Compatibility analyzer wrappers/legacy dictionary context generator exist and may still support tests/external consumers; no blind deletion. Legacy `shared_files` remains empty. Direct string-format prompt code is used, not dead. Overview placeholders are reachable, not dead. Most response dictionaries are not FastAPI response_model validated. No duplicate frontend HTTP client was found in application source.

## Exact checks executed

| Check | Result | Scope |
|---|---|---|
| Backend `python -B -m pytest -q -p no:cacheprovider --basetemp=<unique temp>` | **250 passed**, one warning, 32.94s | Existing full suite; no backend code changed afterward |
| Frontend `npm.cmd run typecheck` | **PASS** | tsc app configuration |
| Frontend `npm.cmd run lint` | **PASS** | ESLint source/harness checks |
| Frontend `npm.cmd run build` | **PASS**, 2178 transformed modules, 11.50s | Vite production build; existing outdated Browserslist warning |
| Fixture exporter | **PASS** | Actual canonical context/workspace responses exported to ignored .test-output |
| Repository-state browser suite | **29 checks passed** | Includes new Conflict Radar error regression, lifecycle/quota/late results/mobile |
| Workspace browser suite | **PASS** | Grounded evidence, protected role, pinned commit, artifact preview/download/Escape, comparison/branch isolation, memory credentials/mobile/refresh |
| GitHub live browser suite | **10 checks passed** | Real React/local FastAPI/GitHub, anonymous/auth/invalid token/analysis/reuse/reload |
| Direct A–F context checks | **PASS** | Five deterministic full fixtures and explicit limited omission, plus existing suite's limits |
| Full static self-analysis | Executed; **accuracy gaps found** | Do not count false classifications as verified capabilities |
| Production health/auth/CORS/original repo | **PASS with real anonymous quota failure** | Read-only public API probes; private repo validation only |
| Additional local HTTP smoke checks | **PASS** | Both health aliases 200; missing operator-key chat 503; legacy prompt hardcoded label; invalid URL 400; same-branch integration/compare 200 |
| Credential scan | **No exact known secret values in tracked content** | Does not guarantee unknown formats absent |

Local tool versions: Python 3.14.6; Node 24.18.0; FastAPI 0.141.1; Starlette 1.6.0; Pydantic 2.13.5; pydantic-settings 2.15.0; httpx 0.28.1; pytest 9.1.1; anyio 4.14.2; Uvicorn 0.52.4; Vite 5.4.8. These are observed local installations, not pinned production requirements. Starlette warns that TestClient/httpx usage is deprecated. No coverage percentage, live provider output, multi-worker/load certification or automatic deployed-revision validation was measured.

**VERIFIED:** The same-branch live ML integration returned empty frontend/backend route sets with compatible=true, confirming that compatibility without detected contracts is not proof of interoperability. Same-branch snapshot comparison returned zero changed paths. These are smoke checks, not a live two-branch API compatibility certification.

## Performance findings

**VERIFIED:** Same-commit analysis reuses stored intelligence with zero actual GitHub requests within the recent authorized observation. Explicit refresh collected 44 requests for the public ML case. No duplicate POST on double click; content reads unique. Projection and chat opening do not recollect tree/files. **OBSERVED:** Sequential file HTTP clients and synchronous parser/regex work create latency under broad limits; two-branch Integration may double collection; anonymous quotas are shared externally. Fixed cache/AI bounds are process-local and do not provide per-tenant resource isolation.

## Second verification pass and delivery

**OBSERVED:** Canonical document checked against actual service relationships, router/OpenAPI paths, Pydantic inputs, settings names/defaults, frontend forwarded fields, quota logs and final check outcomes. Unsupported live provider/deployed SHA claims explicitly labeled UNKNOWN. File references point to real modules; contextual paths use their stated frontend/backend roots. No architecture/design/provider/context rewrite occurred.

Intended changes: root PROJECT_CONTEXT.md and PROJECT_AUDIT.md; minimal ConflictRadar.tsx correction; one repository-state browser regression; small precedence notices in existing backend/frontend context docs. Generated files, ignored environment/dependency/build/test outputs and historical reports are not staged. Before commit: review git diff/status, check whitespace, scan staged content against known values/credential signatures. Commit/push to verified origin/main without force; verify remote HEAD equals local HEAD and working tree clean. The terminal/final response carries actual final commit/push result rather than a fabricated pre-commit hash here.

## Remaining priorities

**RECOMMENDATION:** Correct operator credentials/provider configuration outside Git; align legacy UI controls and Overview metrics with existing real APIs; improve source-vs-fixture extraction and wrapper/alias evidence; consistently protect sensitive file paths and bound inbound requests; pin runtime/dependencies and add CI; make process-local deployment/freshness limitations explicit to users. Consider durability/tenancy only through a separately authorized design. Preserve the existing architecture and uncertainty until those changes are tested. Current tests passing does not remove these gaps.
