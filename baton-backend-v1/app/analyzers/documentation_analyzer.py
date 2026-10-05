"""
Documentation and intent analysis.

Discovers and extracts project-level documentation sources:
  - PRD / Product Requirements Documents
  - README files
  - Architecture documents
  - AGENTS.md / CLAUDE.md / Copilot instructions
  - Repository rules in .builder/, .cursor/, .github/
  - CONTRIBUTING.md, CHANGELOG.md, etc.

For each source:
  - Identifies its role (PRD, README, ARCHITECTURE, RULES, etc.)
  - Extracts headings for structural understanding
  - Captures a safe excerpt (first 2000 chars) — NEVER the full file
  - Does NOT execute any content

For rule files:
  - Extracts stated rules, restrictions, and architectural constraints
  - Preserves scope (repository-wide vs directory-specific vs agent-specific)
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Optional

from app.intelligence.models import DocumentationSource, RepositoryRule

# ---------------------------------------------------------------------------
# Classification: known documentation file patterns
# ---------------------------------------------------------------------------

# Exact filename → role
_EXACT_ROLE: dict[str, str] = {
    "readme.md": "README",
    "readme.txt": "README",
    "readme.rst": "README",
    "readme": "README",
    "prd.md": "PRD",
    "product.md": "PRD",
    "requirements.md": "REQUIREMENTS",
    "spec.md": "SPECIFICATION",
    "specification.md": "SPECIFICATION",
    "design.md": "DESIGN",
    "architecture.md": "ARCHITECTURE",
    "arch.md": "ARCHITECTURE",
    "system-design.md": "ARCHITECTURE",
    "agents.md": "AGENTS",
    "claude.md": "AGENTS",
    "copilot-instructions.md": "AGENTS",
    "gemini.md": "AGENTS",
    "cursor-rules.md": "RULES",
    "contributing.md": "CONTRIBUTING",
    "changelog.md": "CHANGELOG",
    "history.md": "CHANGELOG",
    "roadmap.md": "ROADMAP",
    "todo.md": "ROADMAP",
    "security.md": "SECURITY",
    "license": "LICENSE",
    "license.md": "LICENSE",
    "license.txt": "LICENSE",
}

# Path-prefix → role (highest priority first)
_PREFIX_ROLE: list[tuple[str, str]] = [
    (".github/COPILOT_INSTRUCTIONS", "AGENTS"),
    (".github/copilot-instructions", "AGENTS"),
    (".builder/rules", "RULES"),
    (".builder/", "RULES"),
    (".cursor/rules", "RULES"),
    (".cursor/", "RULES"),
    (".mdc", "RULES"),
    ("docs/prd", "PRD"),
    ("docs/requirements", "REQUIREMENTS"),
    ("docs/architecture", "ARCHITECTURE"),
    ("docs/design", "DESIGN"),
    ("docs/api", "API_DOCS"),
    ("docs/", "DOCUMENTATION"),
    ("doc/", "DOCUMENTATION"),
    ("wiki/", "DOCUMENTATION"),
]

# Semantic filename patterns → role
_SEMANTIC_PATTERNS: list[tuple[str, str]] = [
    (r"prd", "PRD"),
    (r"product.?req", "PRD"),
    (r"product.?(description|spec|brief)", "PRD"),
    (r"requirem", "REQUIREMENTS"),
    (r"architec", "ARCHITECTURE"),
    (r"design", "DESIGN"),
    (r"spec(ification)?", "SPECIFICATION"),
    (r"agent", "AGENTS"),
    (r"instruct", "AGENTS"),
    (r"rules?", "RULES"),
    (r"contrib", "CONTRIBUTING"),
    (r"guideline", "CONTRIBUTING"),
    (r"changelog|release.note", "CHANGELOG"),
    (r"roadmap", "ROADMAP"),
    (r"security", "SECURITY"),
]

# Rule instruction file patterns
_RULE_PATH_PATTERNS: list[str] = [
    r"(?:^|/)agents\.md$",
    r"(?:^|/)claude\.md$",
    r"^gemini\.md$",
    r"^copilot.instructions\.md$",
    r"^\.builder/",
    r"^\.cursor/",
    r"^\.github/COPILOT_INSTRUCTIONS",
    r"^\.mdc",
    r"\.mdc$",
]

# Important structure files (not docs but worth noting)
_IMPORTANT_FILENAMES: frozenset[str] = frozenset({
    "package.json", "pyproject.toml", "requirements.txt", "setup.py",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "main.py", "app.py", "index.ts", "index.js", "App.tsx", "App.jsx",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "render.yaml", "vercel.json", "fly.toml", "netlify.toml",
    ".env.example", ".env.sample",
})


# ---------------------------------------------------------------------------
# Main analysis functions
# ---------------------------------------------------------------------------

def analyze_documentation(
    files: list[dict],
    contents: dict[str, str],
) -> list[DocumentationSource]:
    """
    Find and classify documentation sources.

    Returns list of DocumentationSource, ordered by priority
    (PRD first, README second, etc.)
    """
    sources: list[DocumentationSource] = []
    seen: set[str] = set()

    for f in files:
        path = f.get("path", "")
        if not path or path in seen:
            continue
        role = _classify_doc_path(path)
        if role is None:
            continue
        seen.add(path)
        text = contents.get(path, "")
        headings = _extract_headings(text)
        excerpt = _safe_excerpt(text)
        sources.append(DocumentationSource(
            path=path,
            role=role,
            headings=headings,
            raw_excerpt=excerpt,
        ))

    # Sort by priority: PRD > REQUIREMENTS > SPECIFICATION > ARCHITECTURE >
    #                   AGENTS > RULES > README > CONTRIBUTING > DOCUMENTATION > others
    priority = {
        "PRD": 0, "REQUIREMENTS": 1, "SPECIFICATION": 2, "ARCHITECTURE": 3,
        "DESIGN": 4, "AGENTS": 5, "RULES": 6, "README": 7, "API_DOCS": 8,
        "CONTRIBUTING": 9, "DOCUMENTATION": 10, "ROADMAP": 11,
        "CHANGELOG": 12, "SECURITY": 13, "LICENSE": 99,
    }
    sources.sort(key=lambda s: (priority.get(s.role, 50), s.path))
    return sources


def analyze_rules(
    files: list[dict],
    contents: dict[str, str],
) -> list[RepositoryRule]:
    """
    Extract explicit instruction and rule sources.
    """
    rules: list[RepositoryRule] = []
    seen: set[str] = set()

    for f in files:
        path = f.get("path", "")
        if not path or path in seen:
            continue
        if not _is_rule_file(path):
            continue
        seen.add(path)
        text = contents.get(path, "")
        if not text:
            continue
        scope = _classify_scope(path)
        extracted_rules, restrictions, notes = _extract_rules(text)
        if extracted_rules or restrictions or notes:
            rules.append(RepositoryRule(
                source_path=path,
                scope=scope,
                rules=extracted_rules,
                restrictions=restrictions,
                notes=notes,
            ))

    return rules


def find_important_files(files: list[dict]) -> list[str]:
    """
    Return paths of architecturally important files.
    Based on filename matching, not directory convention.
    """
    result: list[str] = []
    for f in files:
        path = f.get("path", "")
        filename = PurePosixPath(path).name
        if filename in _IMPORTANT_FILENAMES or _classify_doc_path(path) in {"PRD", "README", "ARCHITECTURE"}:
            result.append(path)
    return sorted(result)


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def _classify_doc_path(path: str) -> Optional[str]:
    """Return the documentation role for a path, or None if not a doc file."""
    lower_path = path.lower()
    filename = PurePosixPath(lower_path).name
    if re.fullmatch(r'requirements(?:[-_.]\w+)?\.txt', filename):
        return None  # dependency manifests are not product requirements

    # 1. Exact filename match
    if filename in _EXACT_ROLE:
        return _EXACT_ROLE[filename]

    # 2. Path prefix match
    for prefix, role in _PREFIX_ROLE:
        if lower_path.startswith(prefix.lower()):
            # Must be a text file
            if _is_text_doc(path):
                return role

    # 3. Semantic filename pattern (only .md, .rst, .txt files)
    if _is_text_doc(path):
        for pattern, role in _SEMANTIC_PATTERNS:
            if re.search(pattern, filename, re.I):
                return role

    if PurePosixPath(path).suffix.lower() in {".md", ".mdc", ".rst", ".mdx"}:
        return "DOCUMENTATION"
    return None


def _is_text_doc(path: str) -> bool:
    ext = PurePosixPath(path).suffix.lower()
    return ext in {".md", ".rst", ".txt", ".mdx", ".mdc", ""}


def _is_rule_file(path: str) -> bool:
    lower = path.lower()
    for pattern in _RULE_PATH_PATTERNS:
        if re.search(pattern, lower, re.I):
            return True
    return False


def _classify_scope(path: str) -> str:
    lower = path.lower()
    if any(lower.startswith(p) for p in [".builder/", ".cursor/", ".github/"]):
        return f"agent-configuration: {path}"
    if "/" not in path.strip("/"):
        return "repository-wide"
    dirname = path.rsplit("/", 1)[0]
    return f"directory: {dirname}"


# ---------------------------------------------------------------------------
# Content extraction helpers
# ---------------------------------------------------------------------------

def _extract_headings(text: str) -> list[str]:
    """Extract markdown headings from document text."""
    headings: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^(#{1,3})\s+(.+)", line.strip())
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            prefix = "#" * level + " "
            headings.append(f"{prefix}{title}")
        if len(headings) >= 30:
            break
    return headings


def _safe_excerpt(text: str, max_chars: int = 2000) -> Optional[str]:
    """Return a safe excerpt of at most max_chars characters."""
    if not text:
        return None
    return text[:max_chars] if len(text) > max_chars else text


def _extract_rules(text: str) -> tuple[list[str], list[str], list[str]]:
    """
    Extract rules, restrictions, and notes from an instruction file.
    Uses markdown heading and bullet list structure.
    """
    rules: list[str] = []
    restrictions: list[str] = []
    notes: list[str] = []

    current_section = "notes"
    for line in text.splitlines():
        stripped = line.strip()

        # Detect section headings
        if re.match(r"^#{1,3}\s+", stripped):
            heading = re.sub(r"^#+\s+", "", stripped).lower()
            if re.search(r"rule|standard|convention|practice|guideline", heading):
                current_section = "rules"
            elif re.search(r"restrict|not.allow|prohibit|must.not|do.not|never", heading):
                current_section = "restrictions"
            elif re.search(r"note|important|warning|caution", heading):
                current_section = "notes"
            else:
                current_section = "notes"
            continue

        # Extract bullet points
        bullet_match = re.match(r"^[-*+]\s+(.+)", stripped)
        if bullet_match:
            content = bullet_match.group(1).strip()
            if re.search(r"must.not|do.not|never|prohibit|restrict|avoid", content, re.I):
                restrictions.append(content)
            elif current_section == "rules":
                rules.append(content)
            elif current_section == "restrictions":
                restrictions.append(content)
            else:
                notes.append(content)
            continue

        # Number list items
        num_match = re.match(r"^\d+\.\s+(.+)", stripped)
        if num_match:
            content = num_match.group(1).strip()
            if current_section == "rules":
                rules.append(content)
            elif current_section == "restrictions":
                restrictions.append(content)
            else:
                notes.append(content)

    # Cap to avoid overwhelming output
    return rules[:20], restrictions[:20], notes[:20]
