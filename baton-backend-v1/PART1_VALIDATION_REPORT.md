# BATON Part 1 validation report

Completed: 5 October 2026. Scope: canonical repository intelligence foundation only.

## A. Architecture before changes

The repository already used FastAPI with request-scoped HTTPX GitHub access, optional operator access keys, header/server token precedence, deterministic analyzers, Markdown context/prompt generators, and conflict/integration routes. No database, LLM, job queue or repository execution was required.

A partial canonical dataclass model, pipeline and memory cache already existed. This implementation extends those modules rather than replacing the architecture. The legacy `RepositoryAnalyzer` still combined independent stack/API/frontend/handoff helpers, while `AnalysisService` used a different pipeline. The context service consumed legacy projections; cross-branch integration ignored method differences in those strings.

Existing collection retained paths, selected text, languages/frameworks, routes/calls, types, environment names, fixtures and TODO markers. Important losses included the filtered inventory, import relationships, parsed symbols, complete documentation beyond excerpts, dependency versions/scripts, omission reasons and exact source identity. Documentation and code were concatenated during feature reconciliation, allowing a PRD to match itself. Directory classification omitted one-file components. Generic ML/web flows and authentication assumptions could invent architecture. Cache keys omitted folder scope, exposed mutable objects and confused historical staleness. Tree SHA was incorrectly recorded as commit SHA, files were read from a moving branch, and the aggregate collection byte limit was not enforced.

## B. Files modified

Paths are relative to `baton-backend-v1`.

- `BACKEND_CONTEXT.md`: updated integration contract and canonical architecture documentation; removed contradictory no-cache/tree-SHA claims.
- `app/intelligence/models.py`: provenance, exact-state fields, parsed files, dependencies, API consumers, data structures, override model and additive canonical API projection.
- `app/intelligence/pipeline.py`: canonical orchestration, document-first discovery, safe observed-source separation, retained relationships, conservative components/flows, deployment separation and completeness.
- `app/intelligence/snapshot.py`: replaceable bounded memory store, copy isolation, scoped/versioned identity, metadata and targeted invalidation.
- `app/services/analysis_service.py`: authorized exact-commit resolution, pinned collection, cache reuse and all collection limits.
- `app/services/github_service.py`: commit resolution, encoded refs and generic safe errors.
- `app/services/integration_service.py`: method-aware canonical comparison with legacy fallback.
- `app/analyzers/repository_analyzer.py`: canonical compatibility adapter.
- `app/analyzers/api_analyzer.py`: canonical API compatibility adapter.
- `app/analyzers/frontend_analyzer.py`: canonical type/data compatibility projection.
- `app/analyzers/stack_analyzer.py`: canonical stack compatibility projection.
- `app/analyzers/handoff_analyzer.py`: canonical handoff compatibility projection.
- `app/analyzers/component_classifier.py`: root/single-file/ambiguous/shared classifications and source evidence; prevents Python imports becoming Docker evidence.
- `app/analyzers/dependency_analyzer.py`: method/path/caller matching, literal mounts, request/response references, import resolution and API conflicts.
- `app/analyzers/documentation_analyzer.py`: semantic discovery, nested instruction scope, generic Markdown roles and dependency-manifest distinction.
- `app/analyzers/feature_reconciler.py`: replaces documentation-contaminated keyword certification with conservative symbol/endpoint comparisons and explicit conflicts.
- `app/analyzers/requirement_extractor.py`: prose, continuation lines, identifiers, priorities, source lines and fenced-code exclusion.
- `app/analyzers/language_analyzer.py`: language-specific import evidence and GDScript extension support.
- `app/analyzers/project_type_analyzer.py`: scripting, ML/library/mobile/game evidence and avoidance of directory-name classification.
- `app/analyzers/technology_analyzer.py`: parsed Python dependencies and removal of generic route-to-Express guessing.
- `app/analyzers/data_source_analyzer.py`: consumed structured static data and unknown structured-file preservation.
- `app/generators/context_generator.py`: fixes a pre-existing canonical-mode bug that treated legacy API strings as endpoint objects; no presentation redesign.
- `app/utils/file_filters.py`: treats binary datasets/model artifacts as metadata-only input.
- `app/utils/token_budget.py`: strict UTF-8 output byte budget, including the truncation marker.

Frontend files, route request schemas, deployment files and dependencies were not changed. Test-generated tracked bytecode changes were restored.

## C. Files created

- `app/analyzers/code_structure_analyzer.py`
- `app/intelligence/safety.py`
- `tests/fixtures/repositories.json`
- `tests/test_intelligence.py`
- `tests/test_intelligence_service.py`
- `PART1_VALIDATION_REPORT.md`

## D. Canonical schema

`RepositoryIntelligence` remains the top-level dataclass. Its main groups are:

| Group | Content |
|---|---|
| Source state | Owner/repository, resolved branch, exact commit, UTC analysis timestamp, version, folder scope and status |
| Intent | Document roles, sanitized retained documentation, document commit/blob provenance, instruction scope and explicit requirements |
| Identity/technology | Documented titles, evidence-based summary, multiple project types, languages, technologies, dependency manifests and package scripts |
| Semantic structure | Returned file inventory with metadata, directory classifications, components, parsed symbols/imports/entrypoints and parse status |
| Relationships | Declared and resolved imports, API declarations/consumers/callers, request/response/type references and observed data consumers |
| Data/operations | Types/classes/interfaces/SQL tables, ML stage tags, datasets/artifacts/static data/configuration, variable names, tests and deployment evidence |
| Truth/coverage | Evidence category and sources, confidence, requirements/status, conflicts, risks, unknowns, omissions, completeness and user corrections |

Legacy fields remain projections for current clients. `canonical_api` is an additive analysis-response field used by integration comparisons. Full internal consumers use `AnalysisService.analyze_intelligence()`.

## E. Project classification

Multiple categories are supported without requiring frontend/backend/database. File extensions and manifests provide language evidence. Dependencies, imports, supported source patterns and actual configuration support technology and project classification. Documentation examples and source comments/Python docstrings are excluded from implementation signals. Unknown is retained when evidence is insufficient.

Fixtures verify documentation/specification, ML, web frontend/backend/full-stack, CLI, scripts, native mixed-language libraries, embedded, mobile, desktop and game cases. No BookOS-specific feature signal is hardcoded.

## F. Directory classification

Weighted file/content evidence classifies meaningful directories, including root and one-file directories. Folder names do not establish frontend/backend roles. Competing strong roles are AMBIGUOUS; no signal yields UNKNOWN. Confidence and concrete source references accompany classifications, which are labeled INFERRED. Domain paths can be labeled SHARED when resolved imports demonstrate consumers on both the UI and server sides. Components derive from this semantic map.

## G. Intent versus reality

Requirements retain documented text, source document/section/line, explicit IDs and explicit priorities. Implementation evidence is a separate field. Missing matching source yields NOT_DETECTED, including bounded-analysis uncertainty. Matching symbols yield PARTIALLY_IMPLEMENTED candidates, with an explicit warning that behavior/completeness are not verified.

The narrow requirement `Expose GET /health.` may be mechanically IMPLEMENTED by an observed matching endpoint declaration. This does not certify runtime functionality. Conflicting explicit documentation/API claims are marked CONFLICTING. No completion percentages are generated.

## H. Hallucination prevention

The core is deterministic and makes no LLM call. Documentation never supplies observed implementation evidence. Comments and Python docstrings are excluded from implementation-pattern scans. Generic keyword counts cannot certify behavior. Generic dataset-to-training or frontend-to-backend flow templates were removed; flows now require matched callers or actual data references. Authentication risks are not invented merely because a server exists. A framework mention does not create a framework implementation, and a vendor mention does not create a deployment plan.

DOCUMENTED, OBSERVED, DERIVED, INFERRED, UNKNOWN, CONFLICTING and RECOMMENDED are distinct provenance categories. The core generates no recommendations. Pattern extraction and confidence are disclosed rather than treated as compiler-level proof.

## I. Snapshot storage

The injectable `SnapshotStore` protocol supports save/load/exists/invalidate/metadata. The V1 adapter is bounded process-local memory, with defensive copies, locking, a maximum of 20 entries and approximately 40 MB of serialized snapshot data. Python object overhead is additional. The model/store interface permits a future persistent adapter without adding infrastructure now.

Snapshots are not durable, not shared between workers and not an authorization mechanism. Each serving process may need its own first analysis. Concurrent uncached requests are not coalesced; this version guarantees one fetch per selected file within a collection, not global request deduplication.

## J. Invalidation and staleness

Identity includes owner/repository, branch, exact commit, normalized folder and analysis version. GitHub commit resolution occurs on every service request before cache access and uses the requesting credentials. All tree/file reads are then pinned to that resolved commit.

A changed HEAD triggers a fresh analysis with a changed-state warning. A folder result cannot stand in for the whole repository. Old-version and unknown-commit snapshots cannot be reused. Explicit stale retrieval returns a copied STALE view, without mutating stored historical facts. Targeted invalidation can remove one commit/folder, one branch or the repository. Partial collection remains PARTIAL after reuse. Repositories without a commit return uncached PARTIAL intelligence.

## K. Security

GitHub remains read-only. Token precedence, access-key protection and deployment configuration are preserved. Cache hits first require GitHub access with current credentials; cached private data cannot bypass a failed repository access check. Authorization/rate-limit failures abort collection instead of caching misleading partial results.

Sensitive environment/private-key/credential files are omitted. Environment template values, supplied request/server tokens and recognizable credential patterns are removed before findings or snapshots are built. Snapshot schema contains no token field. GitHub errors do not echo remote messages or HTTP exception details. Binary datasets and model artifacts remain metadata-only. Notebook code cells are parsed as text, and outputs are not retained.

No repository modules are imported, no source subprocesses run, no notebooks or model files execute, and no `eval`/`exec` evaluates repository text. Sanitized documents and instructions remain untrusted data for future consumers. Heuristic redaction cannot identify every secret hidden under an innocuous name or in arbitrary prose; snapshots are not a comprehensive secret-scanning product.

## L. Tests added

58 additional collected cases cover the requested repository families and regressions, plus:

- Intent-only versus observed implementation, narrow verifiable endpoints and conservative partial candidates.
- Oddly named, root, single-file, ambiguous and shared directories.
- Nested AGENTS scope and `.builder` rules; mechanically opposing instructions.
- BookOS-style Ask Book callers, shared types, retrieval/AI imports, data and documented fallback.
- ML datasets, preprocessing, model, training, evaluation, notebook cells and artifacts without web invention.
- Dynamic/query/trailing-slash/case-sensitive API normalization, external calls, HTTP methods, FastAPI/Express mounts, Flask multi-method routes and request/response type references.
- Documentation conflicts, source commit/blob evidence, requirement IDs/priorities/lines and fenced-code exclusion.
- Snapshot save/load/copy isolation, folder/commit/version identity, bounded eviction, invalidation, unknown commits and stale views.
- Fresh authorization on cache hits, pinned reads, changed HEAD, default branch and empty repository behavior.
- All collection budgets, post-decode byte checks, failed-read omissions, sensitive/binary filtering and truncated tree reporting.
- Request/server token canaries, secret patterns, template values, safe GitHub errors and source/notebook nonexecution.
- Existing HTTP route compatibility, canonical integration comparison, deterministic output and strict Markdown byte budgets.

## M. Test results

Command: `python -B -m pytest -q -p no:cacheprovider` from `baton-backend-v1`.

Result: **80 passed**, including all **22 original regression tests**, on Python 3.14.6. One existing Starlette/FastAPI TestClient warning recommends a newer HTTP transport; no dependency migration was made for this task. `git diff --check` passed with no whitespace errors. Git emitted expected Windows LF/CRLF notices.

GitHub collection tests use deterministic mocks; no live repository credentials, production deployment or runtime execution of fixture source was required.

## N. Remaining limitations

- Memory snapshots disappear on restart and are not shared between instances; no durable-store guarantee is made.
- Static extraction cannot certify runtime behavior, feature completeness or actual test coverage.
- Non-Python structure extraction uses patterns; compiler type resolution, arbitrary aliases and dynamic/nested route mounts are incomplete.
- Directory analysis considers up to three nesting levels. Bounded collection and GitHub truncated trees may omit implementation evidence.
- Requirement extraction is structured/modal-text based. Semantic equivalence, general prose conflicts and sophisticated instruction-scope conflict resolution require future work.
- Local import/data relationships resolve supported literal references, not every language module system, working-directory convention or bundler alias.
- Binary data/model contents are not inspected, and secret redaction is heuristic beyond supplied token values and supported formats.
- The existing Markdown presentation and prompt API remain compatibility consumers; final context workspace, role views and chat are not part of this upgrade.

## O. What Part 2 can consume

Part 2 can call `analyze_intelligence()` and reuse the exact-state snapshot through the store abstraction. It receives documented intent, source paths/commit evidence, semantic components, parsed symbols/imports, API callers/contracts, dependencies, data/ML stage findings, requirements/status, conflicts, confidence and completeness. These records support selecting relevant files and explaining why a classification exists without downloading the entire repository again.

The override model preserves original observed classifications alongside USER-sourced corrections. It does not apply automatic UI edits or silently replace repository evidence. Chat, role-specific context generation, final context presentation and PRD/prompt redesign remain for later parts.
