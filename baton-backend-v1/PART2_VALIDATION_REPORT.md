# BATON Part 2 — Context System Validation

Implemented on 2026-10-05 in the existing backend worktree, preserving Part 1 changes. Part 3 remains outside this change.

## Delivered

The context endpoint now produces detailed project, role, task and AI handoff views from the same canonical intelligence snapshot. Markdown is a projection, never the stored source of truth. It contains the requested first ten sections plus contracts, data/ML stages, dependencies, configuration, deployment, ownership/rules, developer guidance, conflicts, omissions and AI handoff guidance: twenty sections total.

Context requests authorize current branch state, then load the matching snapshot. They perform no repository scan, file collection, independent feature reconciliation or LLM calls. Missing/stale/wrong-version/mismatched snapshots return an explicit 409 refresh instruction. Explicit analysis remains the refresh operation.

Role selection uses canonical classifications and relationships. Protected backend code and shared contracts remain available for understanding; modification targets require supplied ownership and exclude protection scopes. USER duties, task, scopes and corrections are kept distinct from repository evidence. Unknown relevance falls back openly to project context. No ownership is inferred from role or commit history.

The UTF-8 budget removes whole supporting records and reports their identifiers in Markdown. Structured omissions distinguish source collection, view relevance and byte-budget exclusions. Identity, boundaries, contracts, rules, conflicts and uncertainty are retained; an impossible Markdown budget returns 413. The direct builder instead returns an explicitly unusable INCOMPLETE result within its byte limit.

## Changed areas

| File | Responsibility |
|---|---|
| `app/schemas/context.py` | Optional view/member/task/constraints/commit/budget request fields |
| `app/services/context_snapshot.py` | Authorized snapshot-only loading and refresh errors |
| `app/services/context_service.py` | Shared view dispatch, server budget cap, redaction and compatibility response |
| `app/generators/context_relevance.py` | Canonical relationship closure and USER modification boundaries |
| `app/generators/context_builder.py` | Detailed evidence-based Markdown, completeness and omission metadata |
| `app/generators/context_generator.py` | One canonical builder plus legacy direct-library compatibility |
| `app/analyzers/code_structure_analyzer.py` | Small canonical extension for flat TypeScript contract property declarations |
| `tests/test_context_system.py` | 52 additional parameterized regression cases |
| `tests/test_intelligence_service.py` | Existing route test now explicitly supplies a snapshot for context |
| `BACKEND_CONTEXT.md` | Current endpoint contract, architecture, budgets and limitations |

The old canonical formatter was replaced by the shared builder. The legacy dictionary formatter remains only for older direct library callers; it is never used by the context API. No frontend source, chat feature, provider integration, deployment configuration or infrastructure dependency was added.

## Validation result

Command, executed from `baton-backend-v1`:

```powershell
python -B -m pytest -q -p no:cacheprovider
```

**132 passed.** This includes the existing 80 regressions and 52 Part 2 cases. The environment reports one existing Starlette/httpx deprecation warning. `git diff --check` passes.

The new tests cover:

- All twenty briefing sections, detailed contracts, source evidence and conservative implementation status.
- Four context types with stable shared snapshot identity and no canonical mutation.
- Frontend boundary closure across API routes, request types, retrieval, AI adapter and data consumers.
- Protection precedence, missing ownership, team scope, arbitrary roles, unmatched scopes and visible USER overrides.
- Task selection without invented product requirements; empty, specification-only, README-only, ML, mixed-language, scripts, frontend and backend repositories.
- Whole-record budget omissions, protected mandatory contracts/rules, strict UTF-8 limits and unusable-budget errors.
- Distinct source/view/budget omissions, escaping, USER secret redaction and token redaction across older cached response projections.
- Repeated requests that authorize each time while tree/file/analysis calls are prohibited by test doubles.
- Missing/stale/changed/mismatched snapshots, folder/version isolation, incorrect adapter identity, default branch resolution, partial snapshots and GitHub authorization failures.
- Existing response keys, structured-only output, invalid view rejection, configured server limits and actionable 409/413 responses.
- Canonical flat TypeScript properties and explicitly unknown nested shapes.

Tests use deterministic local fixtures and mocked GitHub authorization/state responses. No live private GitHub repository, production deployment, runtime product behavior or compiler-level contract accuracy was verified.

## Reviewable example

`examples/context/bookos-frontend.context.md` is an actual builder output from the synthetic BookOS fixture in `tests/fixtures/repositories.json`. Its owner/repository/commit are fixture identifiers, not a live analysis. It demonstrates a frontend member who owns `client/` while `server/` and `shared/` are protected. The API, shared request fields, retrieval, AI adapter and data relationships remain in the briefing.

## Operating implications and limits

Run an explicit repository/folder analysis before requesting context. Branch, commit, folder and analysis version must match; the optional request commit is an assertion of current state, not historical checkout support. Context intentionally returns a refresh error after eviction, worker restart or requests reaching a worker without the snapshot. Storage remains bounded and process-local; no durable member or context history is introduced.

Complete collection does not establish completed functionality. Static classifications and task relevance remain evidence-labeled; unrecorded signatures, business responsibilities, shapes, dynamic routes, runtime behavior and test success remain UNKNOWN. Canonical status is retained alongside conservative display labels. NOT_DETECTED never becomes NOT_IMPLEMENTED.

TypeScript property extraction covers only simple flat declarations; nested/generic/computed/method shapes are not resolved. Earlier snapshots lacking these optional fields remain truthful UNKNOWN views until explicitly refreshed. Bidirectional dependency closure may yield broad role slices in tightly connected projects. Ownership metadata guides external agents; it is not a write permission system. Repository instructions remain source data and are never executed by the server.

Markdown and structured context redact supplied tokens and recognizable secrets, but heuristic redaction is not a general secret-scanning guarantee. Token estimates remain approximate. Small budgets can require increasing both request `max_bytes` and server `MAX_TOTAL_CONTEXT_BYTES`.
