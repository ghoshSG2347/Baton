"""
Directory / component classification.

Classifies repository directories by EVIDENCE, not by name.

A directory named 'engine/' that contains FastAPI route handlers
is classified as Backend/API.

A directory named 'backend/' that contains only React components
is classified as Frontend.

Evidence categories per role:

FRONTEND
  - JSX/TSX files
  - React/Vue/Angular imports
  - Browser API usage (document, window, localStorage)
  - UI component patterns
  - Frontend routing (react-router, next.js pages)
  - CSS/SCSS/styled-components

BACKEND / API
  - HTTP framework imports (FastAPI, Flask, Express, Django, etc.)
  - Route declarations (@app.get, router.post, etc.)
  - Database access (ORM imports, SQL queries)
  - Server startup (uvicorn, gunicorn, listen())
  - Middleware patterns

ML PIPELINE
  - Model training (fit(), train(), training_step)
  - Datasets (pd.read_csv, np.load, torch.utils.data)
  - ML framework imports (torch, tensorflow, sklearn)
  - Evaluation metrics
  - Notebook files

DATA PROCESSING
  - ETL patterns (extract, transform, load)
  - pandas/polars data manipulation
  - Data cleaning
  - Pipeline/DAG definitions

CLI
  - argparse/click/typer usage
  - __main__ entrypoints
  - sys.argv access

SHARED / DOMAIN LOGIC
  - Imported by multiple other components
  - API schemas / shared types
  - Common domain models
  - No standalone entrypoint

TESTS
  - Test file naming (test_*.py, *.spec.ts, *.test.ts)
  - Testing imports (pytest, jest, vitest, etc.)

CONFIGURATION
  - Only config files (.env, *.config.js, *.toml, etc.)

DOCUMENTATION
  - Only markdown/text/rst documentation

INFRASTRUCTURE
  - Dockerfile, CI/CD, Terraform, k8s
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import PurePosixPath
from typing import Optional

from app.intelligence.models import Confidence, DirectoryClassification, DirectoryRole


# ---------------------------------------------------------------------------
# Evidence scoring: role → (pattern, weight)
# Weight >= 2 = strong signal; Weight == 1 = weak signal
# ---------------------------------------------------------------------------

_CONTENT_SIGNALS: list[tuple[str, DirectoryRole, int]] = [
    # --- Frontend ---
    (r"from ['\"]react['\"]|import React", DirectoryRole.FRONTEND, 3),
    (r"from ['\"]vue['\"]", DirectoryRole.FRONTEND, 3),
    (r"@angular/core|@NgModule|@Component", DirectoryRole.FRONTEND, 3),
    (r"document\.|window\.|localStorage|sessionStorage", DirectoryRole.FRONTEND, 2),
    (r"<Route|BrowserRouter|useNavigate|Link to=", DirectoryRole.FRONTEND, 2),
    (r"styled\.div|css`|createGlobalStyle", DirectoryRole.FRONTEND, 1),
    (r"@svelte|createEventDispatcher", DirectoryRole.FRONTEND, 2),

    # --- Backend ---
    (r"from fastapi import|import fastapi", DirectoryRole.BACKEND, 3),
    (r"from flask import|import flask", DirectoryRole.BACKEND, 3),
    (r"from django\.|import django", DirectoryRole.BACKEND, 3),
    (r"require\(['\"]express['\"]|from ['\"]express['\"]", DirectoryRole.BACKEND, 3),
    (r"@nestjs/core|@Module|@Controller", DirectoryRole.BACKEND, 3),
    (r"@(?:app|router)\.(?:get|post|put|patch|delete)\s*\(", DirectoryRole.BACKEND, 3),
    (r"(?:app|router)\.(?:get|post|put|patch|delete)\s*\(", DirectoryRole.BACKEND, 2),
    (r"uvicorn\.run|gunicorn|app\.listen\(|server\.listen", DirectoryRole.BACKEND, 2),
    (r"from sqlalchemy|import sqlalchemy|mongoose\.|prisma\.", DirectoryRole.BACKEND, 2),
    (r"SELECT\s+\*|INSERT INTO|UPDATE\s+\w+\s+SET|DELETE FROM", DirectoryRole.BACKEND, 1),

    # --- ML Pipeline ---
    (r"import torch|from torch", DirectoryRole.ML_PIPELINE, 3),
    (r"import tensorflow|from tensorflow", DirectoryRole.ML_PIPELINE, 3),
    (r"from sklearn|import sklearn", DirectoryRole.ML_PIPELINE, 3),
    (r"import keras|from keras", DirectoryRole.ML_PIPELINE, 3),
    (r"model\.fit\(|model\.train\(|trainer\.train\(|training_step", DirectoryRole.ML_PIPELINE, 3),
    (r"\.predict\(|model\.eval\(|model\.inference", DirectoryRole.ML_PIPELINE, 2),
    (r"pd\.read_csv|np\.load|torch\.load|DataLoader", DirectoryRole.ML_PIPELINE, 2),
    (r"accuracy|precision|recall|f1_score|confusion_matrix", DirectoryRole.ML_PIPELINE, 2),
    (r"import mlflow|import wandb|wandb\.init", DirectoryRole.ML_PIPELINE, 2),

    # --- Data Processing ---
    (r"import pandas|from pandas", DirectoryRole.DATA_PROCESSING, 2),
    (r"import polars|from polars", DirectoryRole.DATA_PROCESSING, 2),
    (r"\.dropna\(|\.fillna\(|\.merge\(|\.groupby\(", DirectoryRole.DATA_PROCESSING, 2),
    (r"DAG\(|airflow|prefect|luigi|Pipeline\(", DirectoryRole.DATA_PROCESSING, 2),

    # --- CLI ---
    (r"@click\.command|@app\.command|typer\.run", DirectoryRole.CLI, 3),
    (r"import argparse|ArgumentParser\(\)", DirectoryRole.CLI, 2),
    (r"if __name__\s*==\s*['\"]__main__['\"]", DirectoryRole.CLI, 1),
    (r"sys\.argv\[", DirectoryRole.CLI, 2),

    # --- Tests ---
    (r"import pytest|from pytest import", DirectoryRole.TESTS, 3),
    (r"describe\(|it\(|expect\(|test\(", DirectoryRole.TESTS, 2),
    (r"@pytest\.fixture|@pytest\.mark", DirectoryRole.TESTS, 3),

    # --- Infrastructure ---
    (r"FROM\s+\w+|RUN\s+\w+|EXPOSE\s+\d+|ENTRYPOINT", DirectoryRole.INFRASTRUCTURE, 3),
    (r"resource\s+\"aws_|provider\s+\"", DirectoryRole.INFRASTRUCTURE, 3),
    (r"on:\s+push:|jobs:\s*\n", DirectoryRole.INFRASTRUCTURE, 2),
]

_PATH_SIGNALS: list[tuple[str, DirectoryRole, int]] = [
    # Frontend
    (r"\.(tsx|jsx)$", DirectoryRole.FRONTEND, 3),
    (r"\.css$|\.scss$|\.sass$|\.less$", DirectoryRole.FRONTEND, 1),
    # Backend


    # Tests
    (r"test_.*\.(py|ts|js)$|.*\.(spec|test)\.(ts|js|tsx|jsx)$", DirectoryRole.TESTS, 3),
    (r"^tests?/|/__tests__/|/spec/", DirectoryRole.TESTS, 3),
    # Config
    (r"\.(env|toml|ini|cfg)$|config\.\w+$", DirectoryRole.CONFIGURATION, 1),
    # Infrastructure
    (r"\.tf$|dockerfile$|\.ya?ml$", DirectoryRole.INFRASTRUCTURE, 1),
    # Documentation
    (r"\.(md|rst|txt)$", DirectoryRole.DOCUMENTATION, 1),
    # Notebooks (ML)
    (r"\.ipynb$", DirectoryRole.ML_PIPELINE, 2),
    # Data files (ML/data)
    (r"\.(csv|parquet|tsv|npy|npz|pkl|h5|hdf5)$", DirectoryRole.DATA_PROCESSING, 1),
]


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def classify_directories(
    files: list[dict],
    contents: dict[str, str],
) -> list[DirectoryClassification]:
    """
    Classify meaningful repository directories by evidence.

    Returns DirectoryClassification for each directory with >= 2 files,
    ordered by path.
    """
    # Group files by their top-level directory
    dir_files: dict[str, list[str]] = {}
    for f in files:
        path = f.get("path", "")
        if not path or f.get("type") != "blob":
            continue
        parts = path.split("/")
        if len(parts) == 1:
            dir_key = "."    # root level
        else:
            dir_key = parts[0]
        dir_files.setdefault(dir_key, []).append(path)

    # For each directory, also include subdirectory files under it
    # We want to score top-level dirs first, then meaningful subdirs
    classifications: list[DirectoryClassification] = []
    seen_dirs: set[str] = set()

    # Score all unique directory paths (not just top-level)
    all_dirs: dict[str, list[str]] = {}
    for f in files:
        path = f.get("path", "")
        if not path or f.get("type") != "blob":
            continue
        parts = path.split("/")
        if len(parts) == 1:
            all_dirs.setdefault('.', []).append(path)
        # Consider up to 3 levels of nesting
        for depth in range(1, min(len(parts), 4)):
            dir_path = "/".join(parts[:depth])
            all_dirs.setdefault(dir_path, []).append(path)

    for dir_path, file_paths in sorted(all_dirs.items()):
        if not file_paths:
            continue
        if dir_path in seen_dirs:
            continue

        # Skip obviously non-meaningful dirs
        last_segment = dir_path.rsplit("/", 1)[-1].lower()
        if last_segment in {
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "dist", "build", "coverage", ".next", ".nuxt",
        }:
            continue

        scores: Counter[DirectoryRole] = Counter()
        evidence: list[str] = []

        # Score by file paths
        for file_path in file_paths:
            for pattern, role, weight in _PATH_SIGNALS:
                if re.search(pattern, file_path, re.I):
                    scores[role] += weight

        # Score by content
        dir_contents = {p: contents[p] for p in file_paths if p in contents}
        for file_path, text in dir_contents.items():
            for pattern, role, weight in _CONTENT_SIGNALS:
                if role == DirectoryRole.INFRASTRUCTURE and not (PurePosixPath(file_path).name.lower() == 'dockerfile' or file_path.endswith(('.tf', '.yml', '.yaml'))):
                    continue
                if re.search(pattern, text, re.I | re.MULTILINE):
                    scores[role] += weight

        if not scores:
            classifications.append(DirectoryClassification(path=dir_path, role=DirectoryRole.UNKNOWN, observed_role=DirectoryRole.UNKNOWN.value, confidence=Confidence.UNKNOWN, evidence=file_paths))
            continue

        # Determine winner and confidence
        top_role, top_score = scores.most_common(1)[0]
        total_score = sum(scores.values())
        dominant_ratio = top_score / total_score if total_score > 0 else 0

        competing = scores.most_common(2)
        if len(competing) == 2 and competing[1][1] / top_score >= 0.6:
            confidence = Confidence.LOW
            role = DirectoryRole.AMBIGUOUS
        elif dominant_ratio >= 0.6:
            confidence = Confidence.HIGH if top_score >= 5 else Confidence.MEDIUM
            role = top_role
        elif dominant_ratio >= 0.4:
            confidence = Confidence.MEDIUM
            role = top_role
        else:
            # Two competing roles of similar strength → AMBIGUOUS
            top_two = scores.most_common(2)
            if len(top_two) >= 2 and top_two[1][1] / top_score >= 0.6:
                confidence = Confidence.LOW
                role = DirectoryRole.AMBIGUOUS
            else:
                confidence = Confidence.LOW
                role = top_role

        # Build evidence strings
        winning_patterns = _collect_evidence(dir_path, file_paths, dir_contents, role)
        if not winning_patterns and role != DirectoryRole.AMBIGUOUS:
            # Still produce an entry but mark LOW
            confidence = Confidence.LOW

        classifications.append(DirectoryClassification(
            path=dir_path,
            role=role,
            confidence=confidence,
            evidence=winning_patterns,
            observed_role=role.value,
        ))
        seen_dirs.add(dir_path)

    return classifications


def classify_shared(classifications, resolved_dependencies):
    """Mark a domain directory shared only when both UI and server import it."""
    role_by_path = {d.path: d.role for d in classifications}
    consumers = {}
    for source, targets in resolved_dependencies.items():
        source_dirs = sorted((p for p in role_by_path if source.startswith(p + '/')), key=len)
        source_role = role_by_path[source_dirs[-1]] if source_dirs else DirectoryRole.UNKNOWN
        for target in targets:
            for directory in classifications:
                if target.startswith(directory.path + '/') and not source.startswith(directory.path + '/'):
                    consumers.setdefault(directory.path, []).append((source, source_role))
    for directory in classifications:
        matches = consumers.get(directory.path, [])
        if {DirectoryRole.FRONTEND, DirectoryRole.BACKEND} <= {role for _, role in matches} and directory.role in {DirectoryRole.UNKNOWN, DirectoryRole.AMBIGUOUS, DirectoryRole.SHARED}:
            directory.role = DirectoryRole.SHARED
            directory.observed_role = DirectoryRole.SHARED.value
            directory.confidence = Confidence.HIGH
            directory.evidence.extend(f'Imported by {source}' for source, _ in matches)


def classify_root_files(files: list[dict]) -> list[str]:
    """
    Identify stray / unclassified root-level files.
    """
    root_files = [
        f["path"] for f in files
        if "/" not in f.get("path", "")
        and f.get("type") == "blob"
    ]
    return root_files


# ---------------------------------------------------------------------------
# Evidence collection helpers
# ---------------------------------------------------------------------------

def _collect_evidence(
    dir_path: str,
    file_paths: list[str],
    contents: dict[str, str],
    role: DirectoryRole,
) -> list[str]:
    evidence: list[str] = []
    count = len(file_paths)
    evidence.append(f"{count} file(s) in `{dir_path}/`")

    # Role-specific evidence
    ext_counts: Counter[str] = Counter()
    for p in file_paths:
        ext = PurePosixPath(p).suffix.lower()
        if ext:
            ext_counts[ext] += 1

    top_exts = [ext for ext, _ in ext_counts.most_common(3)]
    if top_exts:
        evidence.append(f"File types: {', '.join(f'`{e}`' for e in top_exts)}")

    # Sample matching content patterns for the winning role
    matched_patterns: list[str] = []
    for source_path, text in contents.items():
        for pattern, prole, _ in _CONTENT_SIGNALS:
            if prole == role and re.search(pattern, text, re.I | re.MULTILINE):
                short_pat = source_path + ": " + pattern[:50].rstrip("|")
                if short_pat not in matched_patterns:
                    matched_patterns.append(short_pat)
                if len(matched_patterns) >= 3:
                    break
        if len(matched_patterns) >= 3:
            break

    for p in matched_patterns:
        evidence.append(f"Pattern: `{p}`")

    return evidence
