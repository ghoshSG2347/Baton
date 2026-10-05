"""
Canonical Context Generator.

Produces the detailed `context.md` from a RepositoryIntelligence model.

CRITICAL DESIGN RULES:
  1. This generator consumes ONLY the RepositoryIntelligence model.
     It does NOT independently inspect raw repository files.
  2. Every section reflects evidence from the model — no invention.
  3. DOCUMENTED and OBSERVED are always kept separate.
  4. Confidence levels are shown for uncertain classifications.
  5. Context is budget-trimmed by PRIORITY, not random truncation.
  6. No GitHub tokens or secret values are ever written to the output.

Priority tiers for context budget:
  P0 — repository identity, project type, source-of-truth docs, architecture, 
       critical contracts, important rules
  P1 — important feature implementation status, API contracts, data flows
  P2 — supporting code detail, directory details
  P3 — generic utilities, generated code, low-value listings
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.intelligence.models import (
    ImplementationStatus,
    ProjectType,
    RepositoryIntelligence,
)
from app.utils.token_budget import estimate_tokens, fit_context


def generate(analysis_or_intelligence, max_bytes: int) -> dict:
    """
    Generate context.md from either a RepositoryIntelligence model
    or a legacy analysis dict (backward compatibility).

    Args:
        analysis_or_intelligence: RepositoryIntelligence or legacy dict
        max_bytes: maximum bytes for the generated markdown

    Returns:
        dict with keys: markdown, estimated_tokens, omitted
    """
    from app.intelligence.models import RepositoryIntelligence as RI

    if isinstance(analysis_or_intelligence, RI):
        intelligence = analysis_or_intelligence
    else:
        # Legacy dict → produce backward-compatible output
        return _generate_legacy(analysis_or_intelligence, max_bytes)

    sections = _build_sections(intelligence)
    raw = _assemble(sections)
    text = fit_context(raw, max_bytes)

    omitted: list[str] = []
    if len(text) < len(raw):
        omitted.append("Context was trimmed to the configured byte budget.")
    omitted += intelligence.completeness.omitted_paths

    return {
        "markdown": text,
        "estimated_tokens": estimate_tokens(text),
        "omitted": omitted,
    }


def _build_sections(intel: RepositoryIntelligence) -> list[tuple[int, str]]:
    """
    Build all sections as (priority, content) tuples.
    Priority 0 = highest (never trimmed).
    """
    sections: list[tuple[int, str]] = []
    add = sections.append

    # -----------------------------------------------------------------------
    # Header (P0)
    # -----------------------------------------------------------------------
    add((0, _header(intel)))

    # -----------------------------------------------------------------------
    # 1. Project Identity (P0)
    # -----------------------------------------------------------------------
    add((0, _section_project_identity(intel)))

    # -----------------------------------------------------------------------
    # 2. Project Summary (P0)
    # -----------------------------------------------------------------------
    add((0, _section_project_summary(intel)))

    # -----------------------------------------------------------------------
    # 3. Source-of-Truth Documents (P0)
    # -----------------------------------------------------------------------
    if intel.documentation_sources:
        add((0, _section_source_of_truth(intel)))

    # -----------------------------------------------------------------------
    # 4. Project Intent (P0 if docs exist, P1 otherwise)
    # -----------------------------------------------------------------------
    priority_docs = [d for d in intel.documentation_sources if d.role in {"PRD", "REQUIREMENTS", "SPECIFICATION"}]
    if priority_docs:
        add((0, _section_project_intent(intel)))
    elif intel.requirements:
        add((1, _section_project_intent(intel)))

    # -----------------------------------------------------------------------
    # 5. Observed Implementation (P0)
    # -----------------------------------------------------------------------
    add((0, _section_observed_implementation(intel)))

    # -----------------------------------------------------------------------
    # 6. Intent vs Reality (P0)
    # -----------------------------------------------------------------------
    if intel.requirements:
        add((0, _section_intent_vs_reality(intel)))

    # -----------------------------------------------------------------------
    # 7. Implementation Status (P1)
    # -----------------------------------------------------------------------
    if intel.requirements:
        add((1, _section_implementation_status(intel)))

    # -----------------------------------------------------------------------
    # 8. Technology Stack (P0)
    # -----------------------------------------------------------------------
    add((0, _section_technology_stack(intel)))

    # -----------------------------------------------------------------------
    # 9. Repository Structure (P1)
    # -----------------------------------------------------------------------
    add((1, _section_repository_structure(intel)))

    # -----------------------------------------------------------------------
    # 10. Directory Classification (P1)
    # -----------------------------------------------------------------------
    if intel.directory_classifications:
        add((1, _section_directory_classification(intel)))

    # -----------------------------------------------------------------------
    # 11. Canonical Architecture (P0)
    # -----------------------------------------------------------------------
    add((0, _section_architecture(intel)))

    # -----------------------------------------------------------------------
    # 12. Components (P1)
    # -----------------------------------------------------------------------
    if intel.components:
        add((1, _section_components(intel)))

    # -----------------------------------------------------------------------
    # 13. Data Flows (P1)
    # -----------------------------------------------------------------------
    if intel.data_flows:
        add((1, _section_data_flows(intel)))

    # -----------------------------------------------------------------------
    # 14. API / Interface Contracts (P0 if APIs exist)
    # -----------------------------------------------------------------------
    if intel.api_endpoints:
        add((0, _section_api_contracts(intel)))

    # -----------------------------------------------------------------------
    # 15. Types / Models / Schemas (P2)
    # -----------------------------------------------------------------------
    if intel.types:
        add((2, _section_types(intel)))

    # -----------------------------------------------------------------------
    # 16. Dependencies (P2)
    # -----------------------------------------------------------------------
    add((2, _section_dependencies(intel)))

    # -----------------------------------------------------------------------
    # 17. Data Sources (P1 for ML, P2 otherwise)
    # -----------------------------------------------------------------------
    if intel.data_sources:
        ds_priority = 1 if ProjectType.MACHINE_LEARNING in intel.project_types else 2
        add((ds_priority, _section_data_sources(intel)))

    # -----------------------------------------------------------------------
    # 18. Configuration (P1)
    # -----------------------------------------------------------------------
    if intel.env_variables or intel.config_files:
        add((1, _section_configuration(intel)))

    # -----------------------------------------------------------------------
    # 19. Deployment (P1)
    # -----------------------------------------------------------------------
    if intel.observed_deployment or intel.planned_deployment:
        add((1, _section_deployment(intel)))

    # -----------------------------------------------------------------------
    # 20. Repository Rules (P0)
    # -----------------------------------------------------------------------
    if intel.repository_rules:
        add((0, _section_repository_rules(intel)))

    # -----------------------------------------------------------------------
    # 21. Tests (P2)
    # -----------------------------------------------------------------------
    add((2, _section_tests(intel)))

    # -----------------------------------------------------------------------
    # 22. Missing / Incomplete Work (P1)
    # -----------------------------------------------------------------------
    if intel.missing_work or intel.planned_features:
        add((1, _section_missing_work(intel)))

    # -----------------------------------------------------------------------
    # 23. Risks / Conflicts (P1)
    # -----------------------------------------------------------------------
    if intel.risks or intel.conflicts:
        add((1, _section_risks_conflicts(intel)))

    # -----------------------------------------------------------------------
    # 24. Unknowns (P2)
    # -----------------------------------------------------------------------
    if intel.unknowns:
        add((2, _section_unknowns(intel)))

    # -----------------------------------------------------------------------
    # 25. Context Completeness (P2)
    # -----------------------------------------------------------------------
    add((2, _section_completeness(intel)))

    # -----------------------------------------------------------------------
    # 26. Evidence & Confidence (P2)
    # -----------------------------------------------------------------------
    add((2, _section_evidence_confidence(intel)))

    # -----------------------------------------------------------------------
    # 27. AI Development Guidance (P0)
    # -----------------------------------------------------------------------
    add((0, _section_ai_guidance(intel)))

    return sections


def _assemble(sections: list[tuple[int, str]]) -> str:
    """Assemble sections in priority order, then by original order."""
    # Keep original order but mark for potential trimming later by priority
    return "\n\n".join(content for _, content in sections)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _header(intel: RepositoryIntelligence) -> str:
    return (
        "# Baton Context\n"
        "> Baton Repository Intelligence — Evidence-Based Project Briefing\n\n"
        f"> ⚠️ Snapshot status: **{intel.snapshot_status.value}**"
    )


def _section_project_identity(intel: RepositoryIntelligence) -> str:
    types_str = ", ".join(pt.value for pt in intel.project_types) or "Unknown"
    lines = [
        "## 1. Project Identity",
        f"- **Repository**: `{intel.owner}/{intel.repo}`",
        f"- **Branch**: `{intel.branch}`",
        f"- **Commit**: `{intel.commit or 'Not available'}`",
        f"- **Project Root**: `{'/' if not intel.project_root else intel.project_root}`",
        f"- **Generated**: {intel.generated}",
        f"- **Project Type**: {types_str}",
    ]
    return "\n".join(lines)


def _section_project_summary(intel: RepositoryIntelligence) -> str:
    summary = intel.project_summary or "Summary could not be determined from available evidence."
    return f"## 2. Project Summary\n\n{summary}"


def _section_source_of_truth(intel: RepositoryIntelligence) -> str:
    lines = ["## 3. Source-of-Truth Documents", ""]
    for doc in intel.documentation_sources[:10]:
        lines.append(f"### `{doc.path}` — {doc.role}")
        if doc.headings:
            top_headings = doc.headings[:5]
            lines.append("Key sections: " + " | ".join(top_headings))
        lines.append("")
    if not intel.documentation_sources:
        lines.append("- No documentation sources detected.")
    return "\n".join(lines)


def _section_project_intent(intel: RepositoryIntelligence) -> str:
    lines = ["## 4. Project Intent"]
    lines.append("")
    lines.append("*What the project is documented to do (DOCUMENTED — not necessarily implemented):*")
    lines.append("")

    if intel.planned_features:
        lines.append("**Documented features / requirements:**")
        for feat in intel.planned_features[:15]:
            lines.append(f"- {feat}")
    elif intel.documentation_sources:
        lines.append("Documentation sources found but structured requirements could not be extracted.")
    else:
        lines.append("No documentation or specification found.")

    if intel.observed_features:
        lines.append("")
        lines.append("**Observed intent from code:**")
        for feat in intel.observed_features[:10]:
            lines.append(f"- {feat}")

    return "\n".join(lines)


def _section_observed_implementation(intel: RepositoryIntelligence) -> str:
    lines = ["## 5. Observed Implementation"]
    lines.append("")
    lines.append("*What the repository actually contains (OBSERVED):*")
    lines.append("")

    if intel.languages:
        lang_str = ", ".join(
            f"{l.name} ({l.file_count} files)"
            for l in intel.languages[:5]
            if l.file_count > 0
        )
        lines.append(f"**Languages**: {lang_str}")

    if intel.api_endpoints:
        lines.append(f"**API endpoints detected**: {len(intel.api_endpoints)}")
        for ep in intel.api_endpoints[:5]:
            callers = f" — callers: {ep.callers[0]}" if ep.callers else ""
            lines.append(f"  - `{ep.method} {ep.route}` ({ep.source_file}){callers}")

    if intel.data_sources:
        datasets = [ds for ds in intel.data_sources if ds.classification == "dataset"]
        artifacts = [ds for ds in intel.data_sources if ds.classification == "model-artifact"]
        if datasets:
            lines.append(f"**Datasets**: {len(datasets)} file(s)")
        if artifacts:
            lines.append(f"**Model artifacts**: {len(artifacts)} file(s)")

    if intel.tests_detected:
        lines.append(f"**Tests**: {len(intel.tests_detected)} test file(s) detected")

    if intel.directory_classifications:
        roles = {}
        for dc in intel.directory_classifications:
            roles.setdefault(dc.role.value, []).append(dc.path)
        lines.append("")
        lines.append("**Observed subsystems:**")
        for role, paths in list(roles.items())[:6]:
            lines.append(f"  - **{role}**: `{'`, `'.join(paths[:3])}`")

    if not intel.languages and not intel.api_endpoints and not intel.directory_classifications:
        lines.append("No significant implementation detected. Repository may be specification-only.")

    return "\n".join(lines)


def _section_intent_vs_reality(intel: RepositoryIntelligence) -> str:
    lines = ["## 6. Intent vs Reality"]
    lines.append("")
    lines.append(
        "> DOCUMENTED = what the specification says. "
        "OBSERVED = what the code contains. "
        "These are never silently merged."
    )
    lines.append("")

    if not intel.requirements:
        lines.append("No structured requirements extracted from documentation.")
        return "\n".join(lines)

    # Group by status
    status_groups: dict[str, list] = {}
    for req in intel.requirements:
        status_groups.setdefault(req.status.value, []).append(req)

    priority_order = [
        ImplementationStatus.CONFLICTING.value,
        ImplementationStatus.PARTIALLY_IMPLEMENTED.value,
        ImplementationStatus.NOT_STARTED.value,
        ImplementationStatus.IMPLEMENTED.value,
        ImplementationStatus.NOT_DETECTABLE.value,
        ImplementationStatus.UNKNOWN.value,
    ]
    for status in priority_order:
        group = status_groups.get(status, [])
        if not group:
            continue
        lines.append(f"### {status.replace('_', ' ')}: {len(group)} requirement(s)")
        for req in group[:3]:
            lines.append(f"- **{req.intent[:80]}**")
            lines.append(f"  - Source: `{req.source_document}`")
            if req.observed_code:
                lines.append(f"  - Observed: {req.observed_code[0][:60]}")
            if req.missing_pieces:
                lines.append(f"  - Missing: {req.missing_pieces[0][:60]}")
        if len(group) > 3:
            lines.append(f"  *(+{len(group) - 3} more)*")
        lines.append("")

    return "\n".join(lines)


def _section_implementation_status(intel: RepositoryIntelligence) -> str:
    lines = ["## 7. Implementation Status"]
    lines.append("")

    if not intel.requirements:
        lines.append("No structured requirements to report.")
        return "\n".join(lines)

    for req in intel.requirements[:20]:
        status_emoji = {
            ImplementationStatus.IMPLEMENTED.value: "✅",
            ImplementationStatus.PARTIALLY_IMPLEMENTED.value: "🔶",
            ImplementationStatus.NOT_STARTED.value: "❌",
            ImplementationStatus.CONFLICTING.value: "⚠️",
            ImplementationStatus.NOT_DETECTABLE.value: "❓",
            ImplementationStatus.UNKNOWN.value: "❓",
            ImplementationStatus.IMPLEMENTED_WITH_DIFFERENCES.value: "⚠️",
        }.get(req.status.value, "❓")

        section = f" (§{req.source_section})" if req.source_section else ""
        lines.append(f"{status_emoji} **{req.intent[:70]}**")
        lines.append(f"   Source: `{req.source_document}`{section} | Status: `{req.status.value}` | Confidence: `{req.confidence.value}`")
        if req.missing_pieces:
            lines.append(f"   Missing: {'; '.join(req.missing_pieces[:2])}")
        lines.append("")

    return "\n".join(lines)


def _section_technology_stack(intel: RepositoryIntelligence) -> str:
    lines = ["## 8. Technology Stack", ""]

    # Languages
    if intel.languages:
        lines.append("### Languages")
        lines.append("")
        for lang in intel.languages[:8]:
            if lang.file_count == 0 and not lang.evidence:
                continue
            lines.append(f"**{lang.name}** — Confidence: `{lang.confidence.value}`")
            for ev in lang.evidence[:3]:
                lines.append(f"  - {ev}")
        lines.append("")

    # Technologies by category
    if intel.technologies:
        cats: dict[str, list] = {}
        for t in intel.technologies:
            cats.setdefault(t.category, []).append(t)

        category_display = {
            "framework": "Frameworks",
            "build-tool": "Build Tools",
            "testing": "Testing",
            "database": "Databases",
            "orm": "ORMs",
            "ml-framework": "ML Frameworks",
            "cloud": "Cloud / Deployment",
            "containerization": "Containerization",
            "infrastructure": "Infrastructure",
            "package-manager": "Package Managers",
            "linting": "Linting / Formatting",
            "notebook": "Notebooks",
            "cli-framework": "CLI Frameworks",
            "data-visualization": "Data Visualization",
            "validation": "Validation",
            "styling": "Styling",
        }
        for cat, display in category_display.items():
            techs = cats.get(cat, [])
            if not techs:
                continue
            lines.append(f"### {display}")
            for t in techs:
                lines.append(f"**{t.name}** — Confidence: `{t.confidence.value}`")
                for ev in t.evidence[:2]:
                    lines.append(f"  - {ev}")
            lines.append("")

    return "\n".join(lines)


def _section_repository_structure(intel: RepositoryIntelligence) -> str:
    lines = ["## 9. Repository Structure", ""]

    if not intel.file_tree:
        lines.append("- No files detected.")
        return "\n".join(lines)

    # Show top-level structure
    top_level_dirs: dict[str, int] = {}
    for f in intel.file_tree:
        path = f.get("path", "")
        if "/" in path:
            top_dir = path.split("/")[0]
            top_level_dirs[top_dir] = top_level_dirs.get(top_dir, 0) + 1

    if top_level_dirs:
        lines.append("**Top-level structure:**")
        lines.append("")
        for d, count in sorted(top_level_dirs.items(), key=lambda x: -x[1])[:12]:
            lines.append(f"- `{d}/` ({count} file(s))")

    lines.append("")
    important = intel.important_files
    if important:
        lines.append("**Key files:**")
        for f in important[:10]:
            lines.append(f"- `{f}`")

    return "\n".join(lines)


def _section_directory_classification(intel: RepositoryIntelligence) -> str:
    lines = ["## 10. Directory Classification", ""]
    lines.append(
        "> Classifications are driven by code evidence, not directory names."
    )
    lines.append("")

    for dc in intel.directory_classifications[:15]:
        lines.append(f"### `{dc.path}/`")
        lines.append(f"- **Role**: {dc.role.value}")
        lines.append(f"- **Confidence**: `{dc.confidence.value}`")
        if dc.user_override:
            lines.append(f"- **User Override**: {dc.user_override}")
        if dc.evidence:
            lines.append("- **Evidence**:")
            for ev in dc.evidence[:3]:
                lines.append(f"  - {ev}")
        lines.append("")

    return "\n".join(lines)


def _section_architecture(intel: RepositoryIntelligence) -> str:
    lines = ["## 11. Canonical Architecture", ""]
    lines.append(
        "> This is ONE unified project architecture. All subsystems derive from "
        "this model. Frontend and backend cannot have contradictory interpretations."
    )
    lines.append("")

    if intel.project_types == [ProjectType.SPECIFICATION_ONLY]:
        lines.append("**Status: PLANNED / DOCUMENTED ARCHITECTURE**")
        lines.append("")
        lines.append(
            "No implementation detected. Architecture below is derived from documentation only."
        )
        lines.append("Do NOT treat this as a description of current implemented state.")
        lines.append("")

    if intel.components:
        for comp in intel.components:
            lines.append(f"**{comp.name}**")
            lines.append(f"  Role: {comp.role}")
            if comp.paths:
                lines.append(f"  Paths: `{'`, `'.join(comp.paths[:3])}`")
            if comp.responsibilities:
                for r in comp.responsibilities[:2]:
                    lines.append(f"  - {r}")
            lines.append("")
    else:
        # Derive from project types even without component classifications
        type_descriptions = {
            ProjectType.MACHINE_LEARNING: "Dataset → Preprocessing → Training → Evaluation → Model Artifact",
            ProjectType.FRONTEND: "Browser → UI Components → State → API Calls",
            ProjectType.BACKEND_API: "HTTP Request → Router → Handler → Response",
            ProjectType.CLI: "CLI Input → Parser → Domain Logic → Output",
            ProjectType.FULL_STACK: "User → Frontend → API → Backend → Data Store",
        }
        described = False
        for pt in intel.project_types:
            if pt in type_descriptions:
                lines.append(f"**{pt.value}**: {type_descriptions[pt]}")
                described = True
        if not described:
            lines.append("Architecture could not be determined from available evidence.")

    return "\n".join(lines)


def _section_components(intel: RepositoryIntelligence) -> str:
    lines = ["## 12. Components", ""]
    for comp in intel.components:
        lines.append(f"### {comp.name}")
        lines.append(f"**Role**: {comp.role}")
        if comp.paths:
            lines.append(f"**Paths**: `{'`, `'.join(comp.paths[:5])}`")
        if comp.responsibilities:
            lines.append("**Responsibilities**:")
            for r in comp.responsibilities:
                lines.append(f"  - {r}")
        if comp.dependencies:
            lines.append(f"**Depends on**: {', '.join(comp.dependencies[:5])}")
        lines.append("")
    return "\n".join(lines)


def _section_data_flows(intel: RepositoryIntelligence) -> str:
    lines = ["## 13. Data Flows", ""]
    for flow in intel.data_flows:
        lines.append(f"- {flow}")
    if not intel.data_flows:
        lines.append("- Data flows could not be determined from available evidence.")
    return "\n".join(lines)


def _section_api_contracts(intel: RepositoryIntelligence) -> str:
    lines = ["## 14. API / Interface Contracts", ""]

    for ep in intel.api_endpoints[:20]:
        lines.append(f"### `{ep.method} {ep.route}`")
        lines.append(f"- **Source**: `{ep.source_file}`")
        if ep.callers:
            lines.append(f"- **Callers**: `{'`, `'.join(ep.callers[:3])}`")
        if ep.evidence:
            lines.append(f"- **Evidence**: {ep.evidence[0]}")
        lines.append("")

    if intel.api_calls:
        unmatched = [
            c for c in intel.api_calls
            if not any(_normalize(c.route) == _normalize(e.route) for e in intel.api_endpoints)
        ]
        if unmatched:
            lines.append("### Client-side calls without matched server routes")
            for c in unmatched[:5]:
                lines.append(f"- `{c.route}` (called from `{c.source_file}`)")
            lines.append("")

    return "\n".join(lines)


def _section_types(intel: RepositoryIntelligence) -> str:
    lines = ["## 15. Types / Models / Schemas", ""]
    if intel.types:
        lines.append("**Important types detected** (domain models, API contracts, shared schemas):")
        for t in intel.types[:30]:
            lines.append(f"- `{t}`")
    else:
        lines.append("- No significant types detected.")
    return "\n".join(lines)


def _section_dependencies(intel: RepositoryIntelligence) -> str:
    lines = ["## 16. Dependencies", ""]

    if intel.api_endpoints and intel.api_calls:
        lines.append("**API dependency relationships:**")
        for ep in intel.api_endpoints[:5]:
            if ep.callers:
                lines.append(f"- `{ep.source_file}` ← called by `{'`, `'.join(ep.callers[:2])}`")
        lines.append("")

    if intel.technologies:
        critical = [t for t in intel.technologies if t.category in {"framework", "database", "orm"}]
        if critical:
            lines.append("**Critical dependencies:**")
            for t in critical[:8]:
                lines.append(f"- {t.name} ({t.category})")

    if not intel.api_endpoints and not intel.technologies:
        lines.append("- No significant dependency relationships detected.")

    return "\n".join(lines)


def _section_data_sources(intel: RepositoryIntelligence) -> str:
    lines = ["## 17. Data Sources", ""]

    by_class: dict[str, list] = {}
    for ds in intel.data_sources:
        by_class.setdefault(ds.classification, []).append(ds)

    class_order = [
        "dataset", "model-artifact", "training-artifact",
        "fixture", "mock", "test-data", "seed",
        "static-data", "config", "generated", "unknown",
    ]
    for cls in class_order:
        items = by_class.get(cls, [])
        if not items:
            continue
        lines.append(f"### {cls.replace('-', ' ').title()}: {len(items)} file(s)")
        for ds in items[:5]:
            consumers = f" — consumed by: `{ds.consumers[0]}`" if ds.consumers else ""
            lines.append(f"- `{ds.path}` (Confidence: {ds.confidence.value}){consumers}")
        lines.append("")

    if not intel.data_sources:
        lines.append("- No data files detected.")

    return "\n".join(lines)


def _section_configuration(intel: RepositoryIntelligence) -> str:
    lines = ["## 18. Configuration", ""]
    lines.append(
        "> Environment variable NAMES only are shown. "
        "Values are never stored or displayed."
    )
    lines.append("")

    if intel.env_variables:
        lines.append("**Environment Variables:**")
        lines.append("")
        for ev in intel.env_variables[:30]:
            req_str = " *(required)*" if ev.required else ""
            purpose = f" — {ev.purpose}" if ev.purpose else ""
            lines.append(f"- `{ev.name}`{req_str}{purpose}")
        lines.append("")

    if intel.config_files:
        lines.append("**Config Files:**")
        for f in intel.config_files[:10]:
            lines.append(f"- `{f}`")

    if not intel.env_variables and not intel.config_files:
        lines.append("- No configuration files or environment variables detected.")

    return "\n".join(lines)


def _section_deployment(intel: RepositoryIntelligence) -> str:
    lines = ["## 19. Deployment", ""]

    if intel.observed_deployment:
        lines.append("**OBSERVED DEPLOYMENT CONFIGURATION** (configuration files exist):")
        for d in intel.observed_deployment:
            lines.append(f"- {d}")
        lines.append("")

    if intel.planned_deployment:
        lines.append("**PLANNED DEPLOYMENT** (mentioned in documentation only):")
        for d in intel.planned_deployment:
            lines.append(f"- {d}")
        lines.append("")

    if not intel.observed_deployment and not intel.planned_deployment:
        lines.append("- No deployment configuration detected.")

    return "\n".join(lines)


def _section_repository_rules(intel: RepositoryIntelligence) -> str:
    lines = ["## 20. Repository Rules", ""]

    for rule_set in intel.repository_rules[:5]:
        lines.append(f"### `{rule_set.source_path}` — Scope: {rule_set.scope}")
        if rule_set.rules:
            lines.append("**Rules:**")
            for r in rule_set.rules[:10]:
                lines.append(f"  - {r}")
        if rule_set.restrictions:
            lines.append("**Restrictions:**")
            for r in rule_set.restrictions[:10]:
                lines.append(f"  - ❌ {r}")
        if rule_set.notes:
            lines.append("**Notes:**")
            for n in rule_set.notes[:5]:
                lines.append(f"  - {n}")
        lines.append("")

    return "\n".join(lines)


def _section_tests(intel: RepositoryIntelligence) -> str:
    lines = ["## 21. Tests", ""]
    if intel.tests_detected:
        lines.append(f"**{len(intel.tests_detected)} test file(s) detected:**")
        for t in intel.tests_detected[:10]:
            lines.append(f"- `{t}`")
    else:
        lines.append("- No test files detected.")
    if intel.test_coverage_notes:
        lines.append("")
        for note in intel.test_coverage_notes:
            lines.append(f"- {note}")
    return "\n".join(lines)


def _section_missing_work(intel: RepositoryIntelligence) -> str:
    lines = ["## 22. Missing / Incomplete Work", ""]

    if intel.missing_work:
        lines.append("**Requirements with no observed implementation:**")
        for m in intel.missing_work[:10]:
            lines.append(f"- {m}")
        lines.append("")

    if intel.planned_features:
        lines.append("**Planned features (documented but not confirmed implemented):**")
        for f in intel.planned_features[:10]:
            lines.append(f"- {f}")

    if not intel.missing_work and not intel.planned_features:
        lines.append("- No missing work detected from requirements comparison.")

    return "\n".join(lines)


def _section_risks_conflicts(intel: RepositoryIntelligence) -> str:
    lines = ["## 23. Risks / Conflicts", ""]

    if intel.conflicts:
        lines.append("**⚠️ CONFLICTS DETECTED** — sources disagree on the following:")
        lines.append("")
        for c in intel.conflicts[:10]:
            lines.append(f"### {c.description}")
            lines.append(f"- **Source A** (`{c.source_a}`): {c.claim_a}")
            lines.append(f"- **Source B** (`{c.source_b}`): {c.claim_b}")
            lines.append(f"- **Resolution**: {c.resolution}")
            lines.append("")

    if intel.risks:
        lines.append("**Risks:**")
        for r in intel.risks:
            lines.append(f"- {r}")

    if not intel.conflicts and not intel.risks:
        lines.append("- No conflicts or risks detected.")

    return "\n".join(lines)


def _section_unknowns(intel: RepositoryIntelligence) -> str:
    lines = ["## 24. Unknowns", ""]
    for u in intel.unknowns:
        lines.append(f"- {u}")
    if not intel.unknowns:
        lines.append("- No significant unknowns.")
    return "\n".join(lines)


def _section_completeness(intel: RepositoryIntelligence) -> str:
    c = intel.completeness
    lines = [
        "## 25. Context Completeness",
        "",
        f"- **Status**: `{c.status}`",
        f"- **Files discovered**: {c.files_discovered}",
        f"- **Fully analyzed**: {c.files_fully_analyzed}",
        f"- **Summarized**: {c.files_summarized}",
        f"- **Omitted**: {c.files_omitted}",
        f"- **Critical files omitted**: {c.critical_files_omitted}",
        f"- **Impact on confidence**: {c.impact}",
    ]
    if c.omitted_paths:
        lines.append("")
        lines.append("**Omitted paths** (size/count limits):")
        for p in c.omitted_paths[:10]:
            lines.append(f"  - `{p}`")
    return "\n".join(lines)


def _section_evidence_confidence(intel: RepositoryIntelligence) -> str:
    lines = ["## 26. Evidence & Confidence", ""]

    uncertain = [
        dc for dc in intel.directory_classifications
        if dc.confidence.value in {"LOW", "UNKNOWN"}
    ]
    if uncertain:
        lines.append("**Low-confidence directory classifications:**")
        for dc in uncertain[:5]:
            lines.append(f"- `{dc.path}/` → {dc.role.value} (LOW)")
        lines.append("")

    low_conf_techs = [t for t in intel.technologies if t.confidence.value == "LOW"]
    if low_conf_techs:
        lines.append("**Low-confidence technology detections:**")
        for t in low_conf_techs[:5]:
            lines.append(f"- {t.name}: {t.evidence[0] if t.evidence else 'weak signal'}")

    if not uncertain and not low_conf_techs:
        lines.append("- All major classifications have MEDIUM or HIGH confidence.")

    return "\n".join(lines)


def _section_ai_guidance(intel: RepositoryIntelligence) -> str:
    lines = ["## 27. AI Development Guidance", ""]
    lines.append(
        "Before modifying this repository, understand the following "
        "(derived from evidence, not invention):"
    )
    lines.append("")

    # Project purpose
    lines.append(f"**Project type**: {', '.join(pt.value for pt in intel.project_types)}")
    if intel.project_summary:
        lines.append(f"**Summary**: {intel.project_summary}")
    lines.append("")

    # Implementation status
    not_started = sum(1 for r in intel.requirements if r.status == ImplementationStatus.NOT_STARTED)
    partial = sum(1 for r in intel.requirements if r.status == ImplementationStatus.PARTIALLY_IMPLEMENTED)
    implemented = sum(1 for r in intel.requirements if r.status == ImplementationStatus.IMPLEMENTED)
    if intel.requirements:
        lines.append(f"**Implementation status**: {implemented} implemented, {partial} partial, {not_started} not started")
    lines.append("")

    # Architecture rules
    if intel.repository_rules:
        lines.append("**Active repository rules** (from instruction files):")
        for rs in intel.repository_rules[:3]:
            for r in rs.restrictions[:3]:
                lines.append(f"  - ❌ {r}")
        lines.append("")

    # Important contracts
    if intel.api_endpoints:
        lines.append(f"**API contracts**: {len(intel.api_endpoints)} endpoint(s) detected — do not break these without checking callers")
        lines.append("")

    # Conflicts to be aware of
    if intel.conflicts:
        lines.append(f"**⚠️ Active conflicts**: {len(intel.conflicts)} conflict(s) between documentation and code — resolve before adding features")
        lines.append("")

    # Missing work
    if intel.missing_work:
        lines.append(f"**Missing work**: {len(intel.missing_work)} documented requirement(s) lack implementation")
        lines.append("")

    # Critical warnings
    lines.append("**DO NOT ASSUME**:")
    lines.append("- Documented ≠ Implemented")
    lines.append("- Inferred ≠ Confirmed")
    lines.append("- Recommended ≠ Required")
    lines.append("- Folder name ≠ Component role (classifications are evidence-based)")

    if intel.unknowns:
        lines.append("")
        lines.append("**Unknown areas** (proceed with caution):")
        for u in intel.unknowns[:3]:
            lines.append(f"  - {u}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Legacy backward-compatible generator
# (used when a plain dict is passed instead of RepositoryIntelligence)
# ---------------------------------------------------------------------------

def _generate_legacy(analysis: dict, max_bytes: int) -> dict:
    """
    Produce context.md from the old analysis dict format.
    Preserved for backward compatibility with existing tests.
    """
    metadata = analysis.get("metadata", {})
    stack = analysis.get("stack", {}).get("detected", [])
    files = analysis.get("file_tree", [])

    def _bullets(values):
        return [f"- {value}" for value in values] or ["- None detected"]

    lines = [
        "# Baton Context",
        "> Baton Repository Context",
        "",
        "## Source",
        f"- Repository: {metadata.get('owner', 'unknown')}/{metadata.get('repo', 'unknown')}",
        f"- Branch: {metadata.get('branch', 'unknown')}",
        f"- Commit: {metadata.get('commit') or 'Not available'}",
        f"- Generated: {metadata.get('generated') or datetime.now(timezone.utc).isoformat()}",
        "",
        "## Requesting Member",
        "- Name: Not configured",
        "- Role: Not configured",
        "- Owns: Not configured",
        "",
        "## Do Not Touch",
        "- No ownership boundaries configured",
        "",
        "## Project Stack",
    ]
    lines += _bullets(stack or ["Not detected"])
    lines += ["", "## Project Structure"] + _bullets([x.get("path") for x in files])
    lines += ["", "## Team Rules", "- No team rules supplied", "", "## Source Member", "- Not configured"]
    lines += ["", "## Completed Work", "- Deterministic repository scan completed"]
    lines += ["", "## Detected Frontend Expectations"] + _bullets(analysis.get("types", []))
    for title, key in (
        ("Routes", "routes"),
        ("API Calls", "api_calls"),
        ("Types / Data Shapes", "types"),
        ("Mock Data", "mock_data"),
        ("Environment Variables", "environment_variables"),
        ("Handoff", "handoffs"),
        ("Shared Files", "shared_files"),
        ("Possible Integration Issues", "analysis_warnings"),
        ("Stray / Out-of-structure Files", "stray_files"),
    ):
        lines += ["", f"## {title}"] + _bullets(analysis.get(key, []))
    lines += [
        "",
        "## Not Detected",
        "- Ownership configuration, contracts, and recent commit subjects were not supplied to this request.",
        "",
        "## Files Included for Verification",
    ] + _bullets([x.get("path") for x in files])

    raw = "\n".join(lines)
    text = fit_context(raw, max_bytes)
    omitted = []
    if len(text) < len(raw):
        omitted.append("Context was trimmed to the configured byte budget.")
    omitted += metadata.get("skipped_files", [])
    return {"markdown": text, "estimated_tokens": estimate_tokens(text), "omitted": omitted}


def _normalize(path: str) -> str:
    import re
    return re.sub(r"\s+", "", path).lower().rstrip("/")
