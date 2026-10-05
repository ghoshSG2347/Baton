"""
Evidence-based language detection.

Detects programming languages from:
  1. File extension counts (primary signal)
  2. Package / manifest files (strong corroborating evidence)
  3. Build system files (additional evidence)
  4. Import statements in content (high-confidence secondary signal)

Does NOT assume a language simply because it is common for the project type.
Every language in the result must have concrete evidence.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from app.intelligence.models import Confidence, DetectedLanguage

# ---------------------------------------------------------------------------
# Extension → canonical language name
# ---------------------------------------------------------------------------

EXT_TO_LANGUAGE: dict[str, str] = {
    "gd": "GDScript",
    "py": "Python",
    "pyx": "Python",
    "pyi": "Python",
    "ipynb": "Jupyter Notebook",
    "js": "JavaScript",
    "jsx": "JavaScript",
    "ts": "TypeScript",
    "tsx": "TypeScript",
    "mjs": "JavaScript",
    "cjs": "JavaScript",
    "java": "Java",
    "kt": "Kotlin",
    "kts": "Kotlin",
    "swift": "Swift",
    "m": "Objective-C",
    "c": "C",
    "h": "C",
    "cpp": "C++",
    "cc": "C++",
    "cxx": "C++",
    "hpp": "C++",
    "hxx": "C++",
    "cs": "C#",
    "go": "Go",
    "rs": "Rust",
    "rb": "Ruby",
    "php": "PHP",
    "dart": "Dart",
    "scala": "Scala",
    "r": "R",
    "rmd": "R",
    "matlab": "MATLAB",
    "jl": "Julia",
    "lua": "Lua",
    "ex": "Elixir",
    "exs": "Elixir",
    "erl": "Erlang",
    "hrl": "Erlang",
    "hs": "Haskell",
    "lhs": "Haskell",
    "sh": "Shell",
    "bash": "Shell",
    "zsh": "Shell",
    "fish": "Shell",
    "ps1": "PowerShell",
    "sql": "SQL",
    "tf": "Terraform",
    "hcl": "HCL",
    "proto": "Protobuf",
    "graphql": "GraphQL",
    "gql": "GraphQL",
    "ino": "Arduino",
    "html": "HTML",
    "css": "CSS",
    "scss": "SCSS",
    "sass": "SASS",
    "less": "Less",
    "vue": "Vue",
    "svelte": "Svelte",
    "json": "JSON",
    "yaml": "YAML",
    "yml": "YAML",
    "toml": "TOML",
    "xml": "XML",
    "md": "Markdown",
    "rst": "reStructuredText",
    "tex": "LaTeX",
    "dockerfile": "Dockerfile",
    "makefile": "Makefile",
}

# Filenames (not extensions) that indicate a language
FILENAME_TO_LANGUAGE: dict[str, str] = {
    "dockerfile": "Dockerfile",
    "makefile": "Makefile",
    "gemfile": "Ruby",
    "rakefile": "Ruby",
    "podfile": "Ruby",
    "gruntfile.js": "JavaScript",
    "gulpfile.js": "JavaScript",
}

# Package/manifest files → language evidence
MANIFEST_EVIDENCE: dict[str, tuple[str, str]] = {
    # filename → (language, evidence description)
    "package.json": ("JavaScript", "Node.js package manifest"),
    "package-lock.json": ("JavaScript", "npm lock file"),
    "yarn.lock": ("JavaScript", "Yarn lock file"),
    "pnpm-lock.yaml": ("JavaScript", "pnpm lock file"),
    "requirements.txt": ("Python", "pip requirements file"),
    "pyproject.toml": ("Python", "Python project manifest"),
    "setup.py": ("Python", "Python setup script"),
    "setup.cfg": ("Python", "Python setup configuration"),
    "Pipfile": ("Python", "Pipenv dependencies"),
    "Pipfile.lock": ("Python", "Pipenv lock file"),
    "poetry.lock": ("Python", "Poetry lock file"),
    "Cargo.toml": ("Rust", "Cargo package manifest"),
    "Cargo.lock": ("Rust", "Cargo lock file"),
    "go.mod": ("Go", "Go module manifest"),
    "go.sum": ("Go", "Go module checksums"),
    "build.gradle": ("Java", "Gradle build script"),
    "build.gradle.kts": ("Kotlin", "Gradle build script (Kotlin DSL)"),
    "pom.xml": ("Java", "Maven project object model"),
    "Gemfile": ("Ruby", "Bundler gem manifest"),
    "Gemfile.lock": ("Ruby", "Bundler lock file"),
    "composer.json": ("PHP", "Composer package manifest"),
    "pubspec.yaml": ("Dart", "Dart/Flutter package manifest"),
    "mix.exs": ("Elixir", "Mix project manifest"),
    "CMakeLists.txt": ("C++", "CMake build configuration"),
    "platformio.ini": ("C/C++", "PlatformIO embedded build config"),
    "DESCRIPTION": ("R", "R package description"),
    "Project.toml": ("Julia", "Julia project manifest"),
}

# Import patterns per language (for content-level detection)
IMPORT_PATTERNS: dict[str, list[str]] = {
    "Python": [r"^\s*import\s+\w", r"^\s*from\s+\w+\s+import"],
    "JavaScript": [r"^\s*(?:const|let|var)\s+.+\s*=\s*require\(", r"^\s*import\s+.+\s+from\s+['\"]"],
    "TypeScript": [r"^\s*import\s+.+\s+from\s+['\"]", r"^\s*export\s+(?:type|interface|class|const)"],
    "Go": [r"^\s*import\s+\(", r"^\s*import\s+\""],
    "Rust": [r"^\s*use\s+\w+::", r"^\s*extern\s+crate\s+"],
    "Java": [r"^\s*import\s+[\w.]+;", r"^\s*package\s+[\w.]+;"],
    "Ruby": [r"^\s*require\s+['\"]", r"^\s*require_relative\s+['\"]"],
    "R": [r"^\s*library\(", r"^\s*require\("],
}


# ---------------------------------------------------------------------------
# Main analyzer function
# ---------------------------------------------------------------------------

def analyze(files: list[dict], contents: dict[str, str]) -> list[DetectedLanguage]:
    """
    Detect programming languages from repository files and contents.

    Args:
        files: list of file metadata dicts (with "path" key)
        contents: dict mapping path → decoded text content

    Returns:
        list of DetectedLanguage, ordered by file_count descending.
        Only languages with concrete evidence are included.
    """
    paths = [f["path"] for f in files if f.get("type") == "blob"]

    # --- Pass 1: count files by extension ---
    ext_counts: Counter[str] = Counter()
    ext_files: dict[str, list[str]] = {}

    for path in paths:
        ext = _ext(path)
        filename = path.rsplit("/", 1)[-1].lower()
        lang = EXT_TO_LANGUAGE.get(ext) or FILENAME_TO_LANGUAGE.get(filename)
        if lang:
            ext_counts[lang] += 1
            ext_files.setdefault(lang, []).append(ext)

    # --- Pass 2: manifest evidence ---
    manifest_evidence: dict[str, list[str]] = {}
    for path in paths:
        filename = path.rsplit("/", 1)[-1]
        if filename in MANIFEST_EVIDENCE:
            lang, desc = MANIFEST_EVIDENCE[filename]
            manifest_evidence.setdefault(lang, []).append(f"`{filename}` ({desc})")

    # --- Pass 3: import-level detection from contents ---
    import_evidence: dict[str, list[str]] = {}
    for path, text in contents.items():
        for lang, patterns in IMPORT_PATTERNS.items():
            if EXT_TO_LANGUAGE.get(_ext(path)) != lang:
                continue
            if any(re.search(p, text, re.MULTILINE) for p in patterns):
                import_evidence.setdefault(lang, []).append(path)

    # --- Merge into DetectedLanguage entries ---
    all_langs: set[str] = (
        set(ext_counts.keys())
        | set(manifest_evidence.keys())
        | set(import_evidence.keys())
    )

    results: list[DetectedLanguage] = []
    for lang in all_langs:
        fc = ext_counts.get(lang, 0)
        exts = sorted(set(ext_files.get(lang, [])))
        evidence: list[str] = []

        if fc > 0:
            evidence.append(f"{fc} `{'`, `'.join(exts)}` file(s) detected")

        for m in manifest_evidence.get(lang, []):
            evidence.append(m)

        imp_files = import_evidence.get(lang, [])
        if imp_files:
            sample = imp_files[:3]
            evidence.append(f"Imports detected in: {', '.join(f'`{p}`' for p in sample)}")

        confidence = _confidence(fc, manifest_evidence.get(lang, []), imp_files)
        results.append(DetectedLanguage(
            name=lang,
            file_count=fc,
            extensions=exts,
            evidence=evidence,
            confidence=confidence,
        ))

    # Sort: by file_count desc, then alphabetically
    results.sort(key=lambda d: (-d.file_count, d.name))
    return results


def to_stack_languages(languages: list[DetectedLanguage]) -> list[str]:
    """
    Produce the legacy-compatible sorted language name list.
    Excludes documentation-only formats (JSON, YAML, Markdown, etc.).
    """
    exclude = {"JSON", "YAML", "TOML", "XML", "Markdown", "reStructuredText", "LaTeX"}
    return sorted(l.name for l in languages if l.name not in exclude and l.file_count > 0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ext(path: str) -> str:
    filename = path.rsplit("/", 1)[-1]
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return filename.lower()


def _confidence(
    file_count: int,
    manifests: list[str],
    imports: list[str],
) -> Confidence:
    signals = 0
    if file_count >= 3:
        signals += 2
    elif file_count >= 1:
        signals += 1
    if manifests:
        signals += 2
    if imports:
        signals += 1

    if signals >= 4:
        return Confidence.HIGH
    if signals >= 2:
        return Confidence.MEDIUM
    return Confidence.LOW
