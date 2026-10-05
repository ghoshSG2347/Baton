"""
Project-type classification.

A repository may have MULTIPLE project types simultaneously.
Types are NEVER assumed — they are derived from concrete evidence:
  - Detected languages
  - Detected technologies
  - Directory classifications
  - File patterns
  - Documentation intent

Possible types (a project may hold several):
  Web Application, Frontend Application, Backend/API, Full-Stack,
  Machine Learning, Data Science, Data Pipeline, CLI, Library/SDK,
  Mobile, Desktop, Game, Embedded/IoT, Automation, DevOps/Infrastructure,
  Research, Specification Only, Monorepo, Mixed/Hybrid, Unknown

CRITICAL: Do NOT force a project into one category.
CRITICAL: Do NOT assume a web app unless frontend evidence exists.
CRITICAL: If only an ML project is detected, never add Frontend/Backend.
"""

from __future__ import annotations

from app.intelligence.models import (
    Confidence,
    DetectedLanguage,
    DetectedTechnology,
    ProjectType,
)


def classify(
    languages: list[DetectedLanguage],
    technologies: list[DetectedTechnology],
    files: list[dict],
    contents: dict[str, str],
    doc_sources: list,  # list[DocumentationSource]
) -> tuple[list[ProjectType], list[str]]:
    """
    Classify the project into one or more ProjectType values.

    Args:
        languages:    detected languages with evidence
        technologies: detected technologies with evidence
        files:        file tree
        contents:     file contents
        doc_sources:  documentation sources

    Returns:
        (project_types, evidence_strings)
        Only types with concrete evidence are included.
    """
    lang_names = {l.name.lower() for l in languages if l.file_count > 0}
    tech_names = {t.name.lower() for t in technologies}
    tech_cats = {t.category for t in technologies}
    paths = {f["path"].lower() for f in files if f.get("type") == "blob"}

    types: dict[ProjectType, list[str]] = {}
    evidence: list[str] = []

    def _add(pt: ProjectType, reason: str) -> None:
        types.setdefault(pt, []).append(reason)

    # ------------------------------------------------------------------
    # 1. Machine Learning / Data Science
    # ------------------------------------------------------------------
    ml_techs = [t for t in technologies if t.category == "ml-framework"]
    notebook_paths = [p for p in paths if p.endswith(".ipynb")]
    dataset_paths = [
        p for p in paths
        if p.endswith((".csv", ".parquet", ".tsv", ".h5", ".hdf5", ".npy", ".npz", ".pkl"))
    ]
    model_artifact_paths = [
        p for p in paths
        if p.endswith((".pt", ".pth", ".h5", ".pkl", ".onnx", ".pb", ".safetensors", ".ckpt"))
        or any(kw in p for kw in ("model/", "models/", "checkpoint", "weights", "artifacts/"))
    ]

    has_training = _content_matches(
        contents,
        [r"\.fit\(|model\.train\(|training_step|fit_transform|\.compile\(|trainer\.train"],
    )
    has_evaluation = _content_matches(
        contents,
        [r"accuracy|precision|recall|f1.score|confusion.matrix|classification.report|evaluate\("],
    )

    if ml_techs or notebook_paths or (dataset_paths and has_training):
        if has_training or model_artifact_paths:
            _add(ProjectType.MACHINE_LEARNING, f"ML frameworks: {[t.name for t in ml_techs[:3]]}")
        elif dataset_paths:
            _add(ProjectType.DATA_SCIENCE, f"Dataset files detected: {dataset_paths[:3]}")
        else:
            _add(ProjectType.DATA_SCIENCE, "Notebooks detected")

        if notebook_paths:
            evidence.append(f"Notebooks: {notebook_paths[:3]}")
        if dataset_paths:
            evidence.append(f"Dataset files: {dataset_paths[:3]}")
        if model_artifact_paths:
            evidence.append(f"Model artifacts: {model_artifact_paths[:3]}")

    # Data pipeline signals
    has_pipeline = _content_matches(
        contents,
        [r"pipeline\s*=|Pipeline\(|\.transform\(|dag\s*=|DAG\(|airflow|prefect|luigi"],
    )
    if has_pipeline and (has_training or "pandas" in lang_names or "python" in lang_names):
        _add(ProjectType.DATA_PIPELINE, "Data pipeline patterns detected")

    # ------------------------------------------------------------------
    # 2. Frontend
    # ------------------------------------------------------------------
    frontend_techs = [
        t for t in technologies
        if t.name.lower() in {
            "react", "vue", "angular", "svelte", "solidjs", "astro", "remix",
            "next.js",
        }
    ]
    has_jsx_tsx = any(p.endswith((".jsx", ".tsx")) for p in paths)
    has_browser_api = _content_matches(
        contents, [r"document\.|window\.|localStorage|sessionStorage|navigator\.|DOM"]
    )
    has_frontend_router = _content_matches(
        contents,
        [r"<Route|<Router|BrowserRouter|createBrowserRouter|useNavigate|useParams"],
    )
    has_ui_components = any(
        "/" + kw in p
        for p in paths
        for kw in ("components/", "pages/", "views/", "screens/")
    )

    if frontend_techs or has_jsx_tsx or has_browser_api or has_frontend_router:
        _add(ProjectType.FRONTEND, f"Frontend frameworks: {[t.name for t in frontend_techs[:3]]}")
        if has_jsx_tsx:
            evidence.append("JSX/TSX files detected")

    # ------------------------------------------------------------------
    # 3. Backend / API
    # ------------------------------------------------------------------
    backend_techs = [
        t for t in technologies
        if t.name.lower() in {
            "fastapi", "flask", "django", "express", "fastify", "nestjs", "hono",
            "starlette", "litestar",
        }
    ]
    has_route_decl = _content_matches(
        contents,
        [
            r"@(?:app|router)\.(?:get|post|put|patch|delete)\s*\(",
            r"(?:app|router)\.(?:get|post|put|patch|delete)\s*\(",
            r"@(?:Get|Post|Put|Patch|Delete)\s*\(",   # NestJS/Java style
        ],
    )
    has_server_startup = _content_matches(
        contents,
        [r"uvicorn\.run|app\.listen\(|server\.listen|gunicorn|listen\(PORT"],
    )
    has_db_access = any(t.category in {"database", "orm"} for t in technologies)

    if backend_techs or has_route_decl or has_server_startup:
        _add(ProjectType.BACKEND_API, f"Backend frameworks: {[t.name for t in backend_techs[:3]]}")
        if has_route_decl:
            evidence.append("Route declarations detected")

    # ------------------------------------------------------------------
    # 4. Full-Stack
    # ------------------------------------------------------------------
    if ProjectType.FRONTEND in types and ProjectType.BACKEND_API in types:
        _add(ProjectType.FULL_STACK, "Both frontend and backend components detected")

    # ------------------------------------------------------------------
    # 5. CLI
    # ------------------------------------------------------------------
    cli_techs = [t for t in technologies if t.category == "cli-framework"]
    has_argparse = _content_matches(contents, [r"ArgumentParser\(\)|add_argument\("])
    has_main_entry = _content_matches(
        contents, [r"if __name__\s*==\s*['\"]__main__['\"]"]
    )
    has_cli_commands = _content_matches(
        contents, [r"@click\.command|@app\.command|typer\.run"]
    )

    if cli_techs or has_cli_commands or (has_argparse and "python" in lang_names):
        _add(ProjectType.CLI, f"CLI frameworks/patterns detected: {[t.name for t in cli_techs]}")

    # ------------------------------------------------------------------
    # 6. Library / SDK
    # ------------------------------------------------------------------
    has_init_py = "__init__.py" in {p.rsplit("/", 1)[-1] for p in paths}
    has_setup_py = any(p.endswith("setup.py") or p.endswith("pyproject.toml") for p in paths)
    has_no_main = not has_server_startup and not has_cli_commands and not frontend_techs

    cargo_lib = _content_matches(contents, [r'\[lib\]'])
    go_pkg = _content_matches(contents, [r"^package\s+\w+"])
    has_npm_lib = _content_matches(contents, [r'"main"\s*:'])

    if (has_init_py and has_setup_py and has_no_main) or cargo_lib or has_npm_lib:
        _add(ProjectType.LIBRARY_SDK, "Package/library indicators detected")

    # ------------------------------------------------------------------
    # 7. Mobile
    # ------------------------------------------------------------------
    has_mobile = (
        "swift" in lang_names
        or "kotlin" in lang_names
        or "dart" in lang_names
        or any(t.name == "React Native" for t in technologies)
        or any("android" in p or "ios" in p or "flutter" in p for p in paths)
    )
    if has_mobile:
        _add(ProjectType.MOBILE, "Mobile platform indicators detected")

    # ------------------------------------------------------------------
    # 8. Desktop
    # ------------------------------------------------------------------
    has_desktop = _content_matches(
        contents,
        [r"Electron|electron|tkinter|PyQt|wx\.App|gtk\+|NSApplication|WinForms|WPF"],
    )
    if has_desktop:
        _add(ProjectType.DESKTOP, "Desktop application indicators detected")

    # ------------------------------------------------------------------
    # 9. Embedded / IoT
    # ------------------------------------------------------------------
    has_embedded = (
        "platformio.ini" in {p.rsplit("/", 1)[-1] for p in paths}
        or any(p.endswith(".ino") for p in paths)
        or "arduino" in lang_names
        or _content_matches(
            contents, [r"#include <Arduino|#include <esp_|#include <stm32"]
        )
    )
    if has_embedded:
        _add(ProjectType.EMBEDDED_IOT, "Embedded/IoT indicators detected")

    # ------------------------------------------------------------------
    # 10. DevOps / Infrastructure
    # ------------------------------------------------------------------
    infra_techs = [
        t for t in technologies
        if t.category in {"infrastructure", "containerization"}
        and t.name.lower() not in {"docker"}
    ]
    has_iac = any(p.endswith(".tf") for p in paths)
    has_ci_cd = any(".github/workflows" in p for p in paths)
    has_k8s = any(
        kw in p
        for p in paths
        for kw in ("k8s/", "kubernetes/", "helm/", "charts/")
    )

    if infra_techs or has_iac or has_k8s:
        _add(ProjectType.DEVOPS_INFRASTRUCTURE, "Infrastructure/IaC files detected")

    # ------------------------------------------------------------------
    # 11. Research
    # ------------------------------------------------------------------
    has_research = _content_matches(
        contents, [r"abstract|hypothesis|methodology|experiment|evaluation|baseline"]
    )
    has_research_files = any(p.endswith((".bib", ".tex")) for p in paths)
    if (has_research and notebook_paths) or has_research_files:
        _add(ProjectType.RESEARCH, "Research indicators detected (LaTeX, notebooks, academic vocabulary)")

    # ------------------------------------------------------------------
    # 12. Monorepo
    # ------------------------------------------------------------------
    root_dirs = set()
    for p in paths:
        parts = p.split("/")
        if len(parts) > 1:
            root_dirs.add(parts[0])
    has_monorepo_config = any(
        p.rsplit("/", 1)[-1] in {"turbo.json", "nx.json", "lerna.json", "pnpm-workspace.yaml"}
        for p in paths
    )
    # Monorepo: has workspace config or many top-level subdirs with their own package files
    pkg_subdirs = {
        p.split("/")[0]
        for p in paths
        if "package.json" in p and p.count("/") == 1
    }
    if has_monorepo_config or len(pkg_subdirs) >= 3:
        _add(ProjectType.MONOREPO, "Monorepo structure indicators detected")

    # ------------------------------------------------------------------
    # 13. Specification / Documentation only
    # ------------------------------------------------------------------
    has_implementation = bool(
        frontend_techs or backend_techs or has_route_decl or has_server_startup
        or ml_techs or cli_techs or has_embedded or infra_techs
    )
    has_only_docs = not has_implementation and bool(
        any(ds.role in {"PRD", "README", "SPECIFICATION", "ARCHITECTURE"} for ds in doc_sources)
    )
    if has_only_docs:
        _add(ProjectType.SPECIFICATION_ONLY, "No implementation detected; only documentation files found")

    # ------------------------------------------------------------------
    # 14. Automation
    # ------------------------------------------------------------------
    has_automation = (
        has_ci_cd
        or _content_matches(contents, [r"cron|schedule|trigger|webhook|automation"])
    )
    all_are_scripts = all(
        p.endswith((".sh", ".bash", ".ps1", ".py"))
        for p in list(paths)[:10]
        if "." in p
    )
    if has_automation and all_are_scripts and not types:
        _add(ProjectType.AUTOMATION, "Automation scripts and scheduling detected")

    # ------------------------------------------------------------------
    # Resolve / finalize
    # ------------------------------------------------------------------
    if not types:
        result_types = [ProjectType.UNKNOWN]
        evidence.append("No strong project-type signals detected")
    else:
        result_types = list(types.keys())
        for pt, reasons in types.items():
            for r in reasons:
                evidence.append(f"{pt.value}: {r}")

    # Remove UNKNOWN if we have other types
    if len(result_types) > 1 and ProjectType.UNKNOWN in result_types:
        result_types.remove(ProjectType.UNKNOWN)

    # If Mixed/Hybrid (many unrelated types, no clear dominant)
    if len(result_types) >= 4:
        result_types.append(ProjectType.MIXED_HYBRID)

    return result_types, evidence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _content_matches(contents: dict[str, str], patterns: list[str]) -> bool:
    import re
    for text in contents.values():
        for pattern in patterns:
            if re.search(pattern, text, re.I | re.MULTILINE):
                return True
    return False
