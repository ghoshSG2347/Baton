"""
Repository Intelligence Pipeline.

This is the orchestrator that:
  1. Takes raw file metadata and contents from GitHub
  2. Runs all analyzers in sequence
  3. Produces ONE canonical RepositoryIntelligence model
  4. Stores it in the snapshot cache

Pipeline sequence:
  1. Language detection
  2. Technology detection
  3. Documentation / intent analysis
  4. Project-type classification
  5. Directory / component classification
  6. API route + call analysis
  7. Dependency / import analysis
  8. Data-source classification
  9. Requirement extraction
  10. Intent vs reality reconciliation
  11. Architecture component modeling
  12. Completeness assessment

IMPORTANT:
  - Each analyzer is called ONCE
  - File contents are passed through, not re-fetched
  - The snapshot is populated from the result of this pipeline only
  - No AI calls are made in this pipeline (deterministic only)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.intelligence.models import (
    ArchitectureComponent,
    EvidenceSource,
    EvidenceStatus,
    Confidence,
    ContextCompleteness,
    DirectoryRole,
    EnvVariable,
    ImplementationStatus,
    IntelligenceConflict,
    ProjectType,
    RepositoryIntelligence,
    SnapshotStatus,
)

# Analyzers
from app.analyzers import language_analyzer, technology_analyzer
from app.analyzers import documentation_analyzer
from app.analyzers import project_type_analyzer
from app.analyzers import component_classifier
from app.analyzers import dependency_analyzer
from app.analyzers import data_source_analyzer
from app.analyzers import requirement_extractor
from app.analyzers import feature_reconciler, code_structure_analyzer
from app.intelligence.safety import sanitize_file, sensitive_path
from app.utils.file_filters import IGNORED_DIRS, IGNORED_NAMES


def run(
    files: list[dict],
    contents: dict[str, str],
    metadata: dict,
    skipped_paths: list[str],
) -> RepositoryIntelligence:
    """
    Execute the full intelligence pipeline.

    Args:
        files:         all file metadata dicts (path, type, size)
        contents:      decoded text content for analyzable files
        metadata:      repository metadata (owner, repo, branch, commit, etc.)
        skipped_paths: paths that were skipped due to size/count limits

    Returns:
        RepositoryIntelligence — the canonical project model
    """
    owner = metadata.get("owner", "")
    repo = metadata.get("repo", "")
    branch = metadata.get("branch", "")
    commit = metadata.get("commit")
    generated = metadata.get("generated") or datetime.now(timezone.utc).isoformat()
    folder = metadata.get("folder", "")
    inventory = files
    files = [f for f in files if not any(p in IGNORED_DIRS for p in f['path'].split('/')) and f['path'].rsplit('/', 1)[-1] not in IGNORED_NAMES and not sensitive_path(f['path'])]

    # Sanitize even callers that bypass GitHub collection (tests/import clients).
    eligible_paths = {f['path'] for f in files if f.get('type') == 'blob'}
    contents = {p: sanitize_file(p, t) for p, t in contents.items() if p in eligible_paths}
    doc_sources = documentation_analyzer.analyze_documentation(files, contents)
    blob_shas = {f['path']: f.get('sha') for f in files}
    for document in doc_sources:
        document.commit = commit
        document.blob_sha = blob_shas.get(document.path)
    repository_rules = documentation_analyzer.analyze_rules(files, contents)
    implementation = code_structure_analyzer.implementation_contents(contents)
    observed_contents = {p: implementation.get(p, t) for p, t in contents.items() if documentation_analyzer._classify_doc_path(p) is None}
    parsed_files = code_structure_analyzer.analyze(observed_contents)
    package_dependencies, package_scripts = code_structure_analyzer.manifests(observed_contents)

    # -----------------------------------------------------------------------
    # STEP 1 — Language detection
    # -----------------------------------------------------------------------
    languages = language_analyzer.analyze(files, implementation)
    stack_languages = language_analyzer.to_stack_languages(languages)

    # -----------------------------------------------------------------------
    # STEP 2 — Technology detection
    # -----------------------------------------------------------------------
    technologies = technology_analyzer.analyze(files, observed_contents)

    # Produce legacy stack.detected list
    stack_detected: list[str] = []
    _legacy_techs = {"react", "vue", "angular", "typescript", "python", "node.js", "next.js",
                     "fastapi", "django", "flask", "express"}
    for t in technologies:
        if t.name.lower() in _legacy_techs:
            stack_detected.append(t.name)
    # Supplement from languages (legacy compat)
    if any(l.name == "TypeScript" for l in languages):
        if "TypeScript" not in stack_detected:
            stack_detected.append("TypeScript")
    if any(l.name == "Python" for l in languages):
        if "Python" not in stack_detected:
            stack_detected.append("Python")
    if any(l.name in {"JavaScript", "TypeScript"} for l in languages):
        # Check for Node.js
        if any(f["path"].endswith("package.json") for f in files):
            if "Node.js" not in stack_detected:
                stack_detected.append("Node.js")

    # -----------------------------------------------------------------------
    # STEP 3 — Documentation / intent analysis
    # -----------------------------------------------------------------------
    important_files = documentation_analyzer.find_important_files(files)

    # -----------------------------------------------------------------------
    # STEP 4 — Project-type classification
    # -----------------------------------------------------------------------
    project_types, type_evidence = project_type_analyzer.classify(
        languages, technologies, files, observed_contents, doc_sources
    )

    # -----------------------------------------------------------------------
    # STEP 5 — Directory / component classification
    # -----------------------------------------------------------------------
    directory_classifications = component_classifier.classify_directories(files, implementation)
    stray_files = component_classifier.classify_root_files(files)

    # -----------------------------------------------------------------------
    # STEP 6 — API route + call analysis
    # -----------------------------------------------------------------------
    api_routes = dependency_analyzer.analyze_routes(implementation)
    api_calls_found = dependency_analyzer.analyze_api_calls(implementation)
    api_routes = dependency_analyzer.match_routes_to_calls(api_routes, api_calls_found)

    # Legacy formats
    legacy_routes = dependency_analyzer.to_legacy_routes(api_routes)
    legacy_api_calls = dependency_analyzer.to_legacy_api_calls(api_calls_found)

    # -----------------------------------------------------------------------
    # STEP 7 — Environment variables + types + handoffs
    # -----------------------------------------------------------------------
    env_variables = []
    import re
    for path, text in contents.items():
        names = dependency_analyzer.analyze_env_variables({path: text})
        if path.rsplit('/', 1)[-1].startswith('.env'):
            names += re.findall(r'(?m)^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=', text)
        for name in sorted(set(names)):
            existing = next((ev for ev in env_variables if ev.name == name), None)
            if existing:
                existing.source_files.append(path)
            else:
                env_variables.append(EnvVariable(name=name, source_files=[path]))
    env_var_names = sorted(ev.name for ev in env_variables)

    important_types = dependency_analyzer.analyze_important_types(implementation)
    handoffs = dependency_analyzer.analyze_handoffs(code_structure_analyzer.code_contents(contents))

    # -----------------------------------------------------------------------
    # STEP 8 — Data-source classification
    # -----------------------------------------------------------------------
    data_sources = data_source_analyzer.analyze(files, implementation)

    # -----------------------------------------------------------------------
    # STEP 9 — Requirement extraction
    # -----------------------------------------------------------------------
    requirements = requirement_extractor.extract(doc_sources, contents)

    # -----------------------------------------------------------------------
    # STEP 10 — Intent vs reality reconciliation
    # -----------------------------------------------------------------------
    requirements, conflicts, observed_features, missing_work = feature_reconciler.reconcile(
        requirements=requirements,
        contents=implementation,
        api_endpoints=api_routes,
        api_calls=api_calls_found,
        directory_classifications=directory_classifications,
        parsed_files=parsed_files,
    )

    # Detect documentation vs code conflicts
    doc_conflicts = feature_reconciler.detect_doc_vs_code_conflicts(
        doc_sources=doc_sources,
        contents=contents,
        api_endpoints=api_routes,
        directory_classifications=directory_classifications,
    )
    conflicts.extend(doc_conflicts)
    conflicts.extend(dependency_analyzer.detect_api_conflicts(api_routes, api_calls_found))
    for requirement in requirements:
        matching = [c for c in doc_conflicts if c.source_a == requirement.source_document and c.claim_a in requirement.intent]
        if matching:
            requirement.status = ImplementationStatus.CONFLICTING
            requirement.conflicts.extend(c.description for c in matching)

    # -----------------------------------------------------------------------
    # STEP 11 — Architecture component modeling
    # -----------------------------------------------------------------------
    dependencies = dependency_analyzer.analyze_imports(implementation)
    resolved_dependencies = dependency_analyzer.resolve_imports(implementation)
    component_classifier.classify_shared(directory_classifications, resolved_dependencies)
    components = _build_components(
        directory_classifications,
        api_routes,
        project_types,
        technologies,
        languages,
    )

    data_flows = [f"{ep.source_file} <- {caller} via {ep.method} {ep.route}" for ep in api_routes for caller in ep.callers]
    data_flows += [f"{ds.path} -> {consumer}" for ds in data_sources for consumer in ds.consumers]

    # -----------------------------------------------------------------------
    # STEP 12 — Deployment detection
    # -----------------------------------------------------------------------
    observed_deployment, planned_deployment = _analyze_deployment(
        technologies, doc_sources, contents, files
    )

    # -----------------------------------------------------------------------
    # STEP 13 — Test detection
    # -----------------------------------------------------------------------
    tests_detected, test_notes = _analyze_tests(files, contents, directory_classifications)

    # -----------------------------------------------------------------------
    # STEP 14 — Risks and unknowns
    # -----------------------------------------------------------------------
    risks = _identify_risks(conflicts, missing_work, requirements, technologies)
    unknowns = _identify_unknowns(
        project_types, directory_classifications, requirements, api_routes
    )
    analysis_warnings: list[str] = list(metadata.get("analysis_warnings", []))
    if skipped_paths:
        analysis_warnings.append(
            f"{len(skipped_paths)} relevant files were omitted by analysis limits or could not be read."
        )

    # -----------------------------------------------------------------------
    # STEP 15 — Context completeness
    # -----------------------------------------------------------------------
    files_discovered = len([f for f in inventory if f.get("type") == "blob"])
    files_analyzed = len(contents)
    skipped_paths = sorted(set(skipped_paths) | {f['path'] for f in inventory if f.get('type') == 'blob' and f['path'] not in contents})
    files_omitted = len(skipped_paths)
    files_summarized = files_discovered - files_analyzed - files_omitted

    completeness_status = "COMPLETE"
    if metadata.get("tree_truncated") or files_omitted > 0 or files_analyzed < files_discovered:
        completeness_status = "PARTIAL"
    if files_analyzed < files_discovered * 0.5:
        completeness_status = "MINIMAL"

    completeness = ContextCompleteness(
        files_discovered=files_discovered,
        files_fully_analyzed=files_analyzed,
        files_summarized=max(0, files_summarized),
        files_omitted=files_omitted,
        critical_files_omitted=len(set(skipped_paths) & set(important_files)),
        omitted_paths=skipped_paths,
        impact="Low" if files_omitted == 0 else "Medium" if files_omitted < 10 else "High",
        status=completeness_status,
        omission_reasons={p: metadata.get('omission_reasons', {}).get(p, 'not_collected') for p in skipped_paths},
        tree_truncated=bool(metadata.get('tree_truncated')),
    )

    # -----------------------------------------------------------------------
    # Build project summary (evidence-based, not invented)
    # -----------------------------------------------------------------------
    project_summary = _build_project_summary(
        project_types, languages, technologies, doc_sources, api_routes, data_sources
    )

    # -----------------------------------------------------------------------
    # Build mock_data list (backward compat)
    # -----------------------------------------------------------------------
    mock_data_paths = [
        ds.path for ds in data_sources
        if ds.classification in {"mock", "fixture", "test-data"}
    ]

    # -----------------------------------------------------------------------
    # Config files
    # -----------------------------------------------------------------------
    config_files = [
        ds.path for ds in data_sources if ds.classification == "config"
    ] + [f["path"] for f in files if f.get("path", "").rsplit("/", 1)[-1] in {
        ".env.example", ".env.sample", "docker-compose.yml", "render.yaml",
        "vercel.json", "fly.toml", "netlify.toml",
    }]

    return RepositoryIntelligence(
        # Identity
        owner=owner,
        repo=repo,
        branch=branch,
        commit=commit,
        generated=generated,
        snapshot_status=SnapshotStatus.PARTIAL if completeness.status != 'COMPLETE' or not commit else SnapshotStatus.CURRENT,
        repository_metadata={k: metadata.get(k) for k in ('owner', 'repo', 'branch', 'commit', 'folder', 'generated')},
        parsed_files=parsed_files,
        documentation_content={d.path: contents[d.path] for d in doc_sources if d.path in contents},
        dependencies=dependencies,
        resolved_dependencies=resolved_dependencies,
        data_models=[{'source_file': p.path, **s} for p in parsed_files for s in p.symbols if s['kind'] in {'ClassDef', 'class', 'interface', 'type', 'struct', 'enum', 'table'}],
        package_dependencies=package_dependencies,
        package_scripts=package_scripts,
        api_consumers=api_calls_found,
        evidence=[EvidenceSource(file=p.path, symbol=s['name'], line=s['line'], category=EvidenceStatus.OBSERVED) for p in parsed_files for s in p.symbols],
        # Project
        project_types=project_types,
        project_type_evidence=type_evidence,
        project_summary=project_summary,
        project_identity={'repository': f'{owner}/{repo}', 'documented_titles': [{'source_document': d.path, 'title': d.headings[0].lstrip('# ').strip(), 'category': EvidenceStatus.DOCUMENTED.value} for d in doc_sources if d.role in {'README', 'PRD'} and d.headings]},
        project_root=folder,
        # Documentation
        documentation_sources=doc_sources,
        repository_rules=repository_rules,
        # Languages / Technologies
        languages=languages,
        technologies=technologies,
        # Structure
        file_tree=[{"path": f["path"], "type": f.get("type"), "size": f.get("size"), "sha": f.get("sha"), "mode": f.get("mode")} for f in inventory],
        directory_classifications=directory_classifications,
        # Architecture
        components=components,
        data_flows=data_flows,
        # APIs
        api_endpoints=api_routes,
        # Requirements
        requirements=requirements,
        observed_features=observed_features,
        planned_features=[r.intent for r in requirements if r.status in {ImplementationStatus.NOT_DETECTED, ImplementationStatus.UNKNOWN}],
        # Data
        data_sources=data_sources,
        # Config
        env_variables=env_variables,
        config_files=sorted(set(config_files)),
        # Deployment
        observed_deployment=observed_deployment,
        planned_deployment=planned_deployment,
        # Tests
        tests_detected=tests_detected,
        test_coverage_notes=test_notes,
        # Problems
        conflicts=conflicts,
        unknowns=unknowns,
        risks=risks,
        missing_work=missing_work,
        analysis_warnings=analysis_warnings,
        # Completeness
        completeness=completeness,
        # --- Legacy backward-compatible fields ---
        stack_detected=stack_detected,
        stack_languages=stack_languages,
        important_files=important_files,
        routes=legacy_routes,
        api_calls=legacy_api_calls,
        environment_variables=env_var_names,
        types=important_types,
        mock_data=mock_data_paths,
        handoffs=handoffs,
        shared_files=[],
        stray_files=stray_files,
    )


# ---------------------------------------------------------------------------
# Architecture component modeling
# ---------------------------------------------------------------------------

def _build_components(
    directory_classifications,
    api_endpoints,
    project_types,
    technologies,
    languages,
) -> list[ArchitectureComponent]:
    """Build architecture components from classified directories."""
    components: list[ArchitectureComponent] = []
    role_to_paths: dict[DirectoryRole, list[str]] = {}

    for dc in directory_classifications:
        role_to_paths.setdefault(dc.role, []).append(dc.path)

    role_descriptions = {
        DirectoryRole.FRONTEND: "User interface and client-side application",
        DirectoryRole.BACKEND: "Server-side API, route handlers, and business logic",
        DirectoryRole.ML_PIPELINE: "Machine learning code; detected stages are recorded per file",
        DirectoryRole.DATA_PROCESSING: "Data ingestion, transformation, and preprocessing",
        DirectoryRole.CLI: "Command-line interface and script entrypoints",
        DirectoryRole.SHARED: "Shared domain logic, types, and utilities",
        DirectoryRole.TESTS: "Test suite",
        DirectoryRole.INFRASTRUCTURE: "Infrastructure, CI/CD, and deployment configuration",
        DirectoryRole.CONFIGURATION: "Application configuration",
    }

    for role, paths in role_to_paths.items():
        if role in {DirectoryRole.UNKNOWN, DirectoryRole.AMBIGUOUS, DirectoryRole.ASSETS,
                    DirectoryRole.GENERATED, DirectoryRole.DOCUMENTATION}:
            continue

        responsibilities: list[str] = []
        if role == DirectoryRole.BACKEND and api_endpoints:
            routes = [f"{e.method} {e.route}" for e in api_endpoints[:5]]
            if routes:
                responsibilities.append(f"Exposes API endpoints: {', '.join(routes)}")
        if role == DirectoryRole.FRONTEND:
            fe_techs = [t.name for t in technologies if t.name in {"React", "Vue", "Angular", "Next.js", "Svelte"}]
            if fe_techs:
                responsibilities.append(f"Built with: {', '.join(fe_techs)}")
        if role == DirectoryRole.ML_PIPELINE:
            ml_techs = [t.name for t in technologies if t.category == "ml-framework"]
            if ml_techs:
                responsibilities.append(f"ML stack: {', '.join(ml_techs[:3])}")

        components.append(ArchitectureComponent(
            name=role.value,
            role=role_descriptions.get(role, role.value),
            paths=paths,
            responsibilities=responsibilities,
            dependencies=[],
            confidence=Confidence.MEDIUM,
            evidence=[e for dc in directory_classifications if dc.role == role for e in dc.evidence],
        ))

    return components


# ---------------------------------------------------------------------------
# Deployment analysis
# ---------------------------------------------------------------------------

def _analyze_deployment(technologies, doc_sources, contents, files) -> tuple[list[str], list[str]]:
    """Configuration presence and explicit deployment intent remain distinct."""
    import re
    platforms = {'dockerfile': 'Docker', 'docker-compose.yml': 'Docker',
                 'docker-compose.yaml': 'Docker', 'render.yaml': 'Render',
                 'vercel.json': 'Vercel', 'netlify.toml': 'Netlify',
                 'fly.toml': 'Fly.io', 'railway.json': 'Railway'}
    observed = []
    for file in files:
        path = file['path']
        name = path.rsplit('/', 1)[-1].lower()
        if file.get('type') == 'blob' and name in platforms:
            observed.append(f"{platforms[name]} configuration present: {path} (deployment not verified)")
        if '.github/workflows/' in path and path.endswith(('.yml', '.yaml')):
            observed.append(f"GitHub Actions workflow present: {path} (execution not verified)")
    planned = []
    for doc in doc_sources:
        for number, line in enumerate(contents.get(doc.path, '').splitlines(), 1):
            if not re.search(r'\b(?:deploy|deployment|host|hosting)\b', line, re.I):
                continue
            if re.search(r'\b(?:not|never|no)\b', line, re.I):
                continue
            for platform in sorted(set(platforms.values()) | {'AWS', 'GCP', 'Azure', 'Kubernetes'}):
                if re.search(re.escape(platform), line, re.I):
                    planned.append(f"{platform}: documented deployment statement in {doc.path}:{number}")
    return sorted(set(observed)), sorted(set(planned))


# ---------------------------------------------------------------------------
# Test analysis
# ---------------------------------------------------------------------------

def _analyze_tests(files, contents, directory_classifications) -> tuple[list[str], list[str]]:
    """Detect test files and report coverage notes."""
    test_files: list[str] = []
    import re

    for f in files:
        path = f.get("path", "")
        if re.search(r"test_.*\.(py|ts|js)$|.*\.(spec|test)\.(ts|js|tsx|jsx)$|^tests?/", path, re.I):
            test_files.append(path)

    notes: list[str] = []
    test_dirs = [dc for dc in directory_classifications if dc.role == DirectoryRole.TESTS]
    if test_files:
        notes.append(f"{len(test_files)} test file(s) detected")
    else:
        notes.append("No test files detected")

    if test_dirs:
        notes.append(f"Test directories: {', '.join(d.path for d in test_dirs[:3])}")

    return test_files, notes


# ---------------------------------------------------------------------------
# Risk and unknown identification
# ---------------------------------------------------------------------------

def _identify_risks(conflicts, missing_work, requirements, technologies) -> list[str]:
    """Identify meaningful risks."""
    risks: list[str] = []

    if conflicts:
        risks.append(f"{len(conflicts)} conflict(s) detected between documentation and code")

    partially = [r for r in requirements if r.status == ImplementationStatus.PARTIALLY_IMPLEMENTED]
    if partially:
        risks.append(f"{len(partially)} requirement(s) partially implemented")

    if missing_work:
        risks.append(f"{len(missing_work)} documented requirement(s) have no observed implementation")

    return risks


def _identify_unknowns(project_types, directory_classifications, requirements, api_routes) -> list[str]:
    """Identify areas Baton cannot determine."""
    unknowns: list[str] = []

    ambiguous = [dc for dc in directory_classifications if dc.role == DirectoryRole.AMBIGUOUS]
    if ambiguous:
        unknowns.append(f"Ambiguous directories: {', '.join(d.path for d in ambiguous[:3])}")

    not_detectable = [r for r in requirements if r.status == ImplementationStatus.NOT_DETECTABLE]
    if not_detectable:
        unknowns.append(f"{len(not_detectable)} requirements could not be verified from code patterns")

    if ProjectType.UNKNOWN in project_types:
        unknowns.append("Project type could not be determined from available evidence")

    return unknowns


# ---------------------------------------------------------------------------
# Project summary builder
# ---------------------------------------------------------------------------

def _build_project_summary(
    project_types,
    languages,
    technologies,
    doc_sources,
    api_routes,
    data_sources,
) -> str:
    """
    Build a concise, evidence-based project summary.
    Does NOT invent features — only reports what is observed.
    """
    parts: list[str] = []

    if project_types and project_types != [ProjectType.UNKNOWN]:
        type_names = ", ".join(pt.value for pt in project_types if pt != ProjectType.UNKNOWN)
        parts.append(f"{type_names} project.")

    primary_langs = [l.name for l in languages[:3] if l.file_count > 0 and l.name not in {"JSON", "YAML", "Markdown"}]
    if primary_langs:
        parts.append(f"Primary language(s): {', '.join(primary_langs)}.")

    notable_techs = [
        t.name for t in technologies
        if t.category in {"framework", "ml-framework"} and t.confidence != Confidence.LOW
    ][:4]
    if notable_techs:
        parts.append(f"Key technologies: {', '.join(notable_techs)}.")

    if api_routes:
        parts.append(f"{len(api_routes)} API endpoint(s) detected.")

    dataset_count = sum(1 for ds in data_sources if ds.classification == "dataset")
    if dataset_count:
        parts.append(f"{dataset_count} dataset file(s) detected.")

    prd = next((d for d in doc_sources if d.role == "PRD"), None)
    if prd and prd.headings:
        parts.append(f"PRD documented in `{prd.path}`.")

    if not parts:
        return "Repository could not be characterized with high confidence from available files."

    return " ".join(parts)
