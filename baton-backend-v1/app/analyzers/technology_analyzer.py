"""
Evidence-based technology stack detection.

For every reported technology:
  - At least one piece of concrete evidence must exist.
  - Generic stack guesses are not made.
  - Technologies detected only from language presence are NOT reported;
    they require package/config/import evidence.

Categories:
  framework        — React, FastAPI, Django, Flask, Express, Vue, Angular, Next.js, etc.
  build-tool       — Vite, Webpack, esbuild, Rollup, Parcel, Make, CMake, etc.
  testing          — pytest, Jest, Vitest, Mocha, Cypress, Playwright, etc.
  database         — PostgreSQL, MySQL, SQLite, MongoDB, Redis, etc.
  orm              — SQLAlchemy, Prisma, Mongoose, TypeORM, etc.
  ml-framework     — PyTorch, TensorFlow, scikit-learn, Keras, JAX, etc.
  cloud            — AWS, GCP, Azure, Vercel, Render, Railway, Fly.io, etc.
  containerization — Docker, Kubernetes, etc.
  infrastructure   — Terraform, Ansible, Pulumi, etc.
  package-manager  — npm, yarn, pnpm, pip, poetry, cargo, etc.
  linting          — ESLint, Prettier, Black, Ruff, Flake8, etc.
  notebook         — Jupyter, Colab references, etc.
  messaging        — Celery, RabbitMQ, Kafka, etc.
  monitoring       — Sentry, Datadog, OpenTelemetry, etc.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from app.intelligence.models import Confidence, DetectedTechnology


# ---------------------------------------------------------------------------
# Technology definitions
# Each entry: (name, category, patterns)
# patterns is a list of (source, pattern):
#   source "pkg_json_dep"  → check package.json dependencies/devDependencies
#   source "pkg_json_dev"  → devDependencies only
#   source "pypi"          → requirements.txt / pyproject.toml / setup.py
#   source "file_exists"   → a specific filename anywhere in the tree
#   source "file_content"  → regex match in any file content
#   source "path_pattern"  → path matches a glob-like pattern
# ---------------------------------------------------------------------------

_TECH_DEFINITIONS: list[tuple[str, str, list[tuple[str, str]]]] = [
    # --- JS/TS Frameworks ---
    ("React", "framework", [
        ("pkg_json_dep", "react"),
        ("file_content", r"from ['\"]react['\"]"),
        ("file_content", r"import React"),
    ]),
    ("Next.js", "framework", [
        ("pkg_json_dep", "next"),
        ("file_exists", "next.config.js"),
        ("file_exists", "next.config.ts"),
        ("file_exists", "next.config.mjs"),
    ]),
    ("Vue", "framework", [
        ("pkg_json_dep", "vue"),
        ("file_content", r"from ['\"]vue['\"]"),
        ("path_pattern", r"\.vue$"),
    ]),
    ("Angular", "framework", [
        ("pkg_json_dep", "@angular/core"),
        ("file_content", r"@NgModule|@Component|@Injectable"),
    ]),
    ("Svelte", "framework", [
        ("pkg_json_dep", "svelte"),
        ("path_pattern", r"\.svelte$"),
    ]),
    ("SolidJS", "framework", [
        ("pkg_json_dep", "solid-js"),
    ]),
    ("Remix", "framework", [
        ("pkg_json_dep", "@remix-run/react"),
    ]),
    ("Astro", "framework", [
        ("pkg_json_dep", "astro"),
        ("file_exists", "astro.config.mjs"),
        ("file_exists", "astro.config.ts"),
    ]),
    # --- Node.js Backend ---
    ("Express", "framework", [
        ("pkg_json_dep", "express"),
        ("file_content", r"require\(['\"]express['\"]|from ['\"]express['\"]"),
        ("file_content", r"(?:app|router)\.(?:get|post|put|patch|delete)\s*\("),
    ]),
    ("Fastify", "framework", [
        ("pkg_json_dep", "fastify"),
    ]),
    ("NestJS", "framework", [
        ("pkg_json_dep", "@nestjs/core"),
        ("file_content", r"@Module|@Controller|@Injectable"),
    ]),
    ("Hono", "framework", [
        ("pkg_json_dep", "hono"),
    ]),
    # --- Python Backend ---
    ("FastAPI", "framework", [
        ("pypi", "fastapi"),
        ("file_content", r"from fastapi import|import fastapi"),
        ("file_content", r"@(?:app|router)\.(?:get|post|put|patch|delete)\s*\("),
    ]),
    ("Flask", "framework", [
        ("pypi", "flask"),
        ("file_content", r"from flask import|import flask"),
        ("file_content", r"@app\.route\s*\("),
    ]),
    ("Django", "framework", [
        ("pypi", "django"),
        ("file_content", r"from django\.|import django"),
        ("file_exists", "manage.py"),
        ("file_exists", "wsgi.py"),
    ]),
    ("Starlette", "framework", [
        ("pypi", "starlette"),
    ]),
    ("Litestar", "framework", [
        ("pypi", "litestar"),
    ]),
    # --- Build Tools ---
    ("Vite", "build-tool", [
        ("pkg_json_dep", "vite"),
        ("file_exists", "vite.config.ts"),
        ("file_exists", "vite.config.js"),
        ("file_exists", "vite.config.mjs"),
    ]),
    ("Webpack", "build-tool", [
        ("pkg_json_dep", "webpack"),
        ("file_exists", "webpack.config.js"),
        ("file_exists", "webpack.config.ts"),
    ]),
    ("esbuild", "build-tool", [
        ("pkg_json_dep", "esbuild"),
    ]),
    ("Rollup", "build-tool", [
        ("pkg_json_dep", "rollup"),
        ("file_exists", "rollup.config.js"),
    ]),
    ("Turbo", "build-tool", [
        ("pkg_json_dep", "turbo"),
        ("file_exists", "turbo.json"),
    ]),
    ("CMake", "build-tool", [
        ("file_exists", "CMakeLists.txt"),
    ]),
    ("PlatformIO", "build-tool", [
        ("file_exists", "platformio.ini"),
    ]),
    ("Make", "build-tool", [
        ("file_exists", "Makefile"),
        ("file_exists", "makefile"),
    ]),
    # --- Testing ---
    ("pytest", "testing", [
        ("pypi", "pytest"),
        ("file_content", r"import pytest|from pytest import"),
        ("file_exists", "pytest.ini"),
        ("file_exists", "conftest.py"),
        ("path_pattern", r"test_.*\.py$|_test\.py$"),
    ]),
    ("Jest", "testing", [
        ("pkg_json_dep", "jest"),
        ("file_exists", "jest.config.js"),
        ("file_exists", "jest.config.ts"),
    ]),
    ("Vitest", "testing", [
        ("pkg_json_dep", "vitest"),
        ("file_exists", "vitest.config.ts"),
        ("file_exists", "vitest.config.js"),
    ]),
    ("Cypress", "testing", [
        ("pkg_json_dep", "cypress"),
        ("file_exists", "cypress.config.ts"),
        ("file_exists", "cypress.config.js"),
    ]),
    ("Playwright", "testing", [
        ("pkg_json_dep", "@playwright/test"),
        ("file_exists", "playwright.config.ts"),
        ("file_exists", "playwright.config.js"),
    ]),
    # --- Databases ---
    ("PostgreSQL", "database", [
        ("pypi", "psycopg2"),
        ("pypi", "asyncpg"),
        ("pypi", "psycopg"),
        ("pkg_json_dep", "pg"),
        ("pkg_json_dep", "@neondatabase/serverless"),
        ("file_content", r"postgresql://|postgres://|POSTGRES_URL|DATABASE_URL.*postgres"),
    ]),
    ("MySQL", "database", [
        ("pypi", "mysql-connector-python"),
        ("pypi", "pymysql"),
        ("pkg_json_dep", "mysql2"),
        ("file_content", r"mysql://|MYSQL_URL"),
    ]),
    ("SQLite", "database", [
        ("pypi", "sqlite3"),
        ("file_content", r"sqlite:///|sqlite3\.connect"),
        ("path_pattern", r"\.db$|\.sqlite$|\.sqlite3$"),
    ]),
    ("MongoDB", "database", [
        ("pypi", "pymongo"),
        ("pypi", "motor"),
        ("pkg_json_dep", "mongoose"),
        ("pkg_json_dep", "mongodb"),
        ("file_content", r"mongodb://|MONGO_URL|MongoClient"),
    ]),
    ("Redis", "database", [
        ("pypi", "redis"),
        ("pkg_json_dep", "ioredis"),
        ("pkg_json_dep", "redis"),
        ("file_content", r"redis://|REDIS_URL|RedisClient"),
    ]),
    # --- ORMs ---
    ("SQLAlchemy", "orm", [
        ("pypi", "sqlalchemy"),
        ("file_content", r"from sqlalchemy|import sqlalchemy"),
    ]),
    ("Prisma", "orm", [
        ("pkg_json_dep", "@prisma/client"),
        ("file_exists", "schema.prisma"),
    ]),
    ("Drizzle", "orm", [
        ("pkg_json_dep", "drizzle-orm"),
    ]),
    ("TypeORM", "orm", [
        ("pkg_json_dep", "typeorm"),
    ]),
    ("Mongoose", "orm", [
        ("pkg_json_dep", "mongoose"),
        ("file_content", r"mongoose\.Schema|mongoose\.model"),
    ]),
    # --- ML Frameworks ---
    ("PyTorch", "ml-framework", [
        ("pypi", "torch"),
        ("file_content", r"import torch|from torch"),
    ]),
    ("TensorFlow", "ml-framework", [
        ("pypi", "tensorflow"),
        ("file_content", r"import tensorflow|from tensorflow"),
    ]),
    ("Keras", "ml-framework", [
        ("pypi", "keras"),
        ("file_content", r"import keras|from keras"),
    ]),
    ("scikit-learn", "ml-framework", [
        ("pypi", "scikit-learn"),
        ("file_content", r"from sklearn|import sklearn"),
    ]),
    ("JAX", "ml-framework", [
        ("pypi", "jax"),
        ("file_content", r"import jax|from jax"),
    ]),
    ("Hugging Face Transformers", "ml-framework", [
        ("pypi", "transformers"),
        ("file_content", r"from transformers import|import transformers"),
    ]),
    ("XGBoost", "ml-framework", [
        ("pypi", "xgboost"),
        ("file_content", r"import xgboost|from xgboost"),
    ]),
    ("LightGBM", "ml-framework", [
        ("pypi", "lightgbm"),
        ("file_content", r"import lightgbm|from lightgbm"),
    ]),
    ("pandas", "ml-framework", [
        ("pypi", "pandas"),
        ("file_content", r"import pandas|from pandas"),
    ]),
    ("NumPy", "ml-framework", [
        ("pypi", "numpy"),
        ("file_content", r"import numpy|from numpy"),
    ]),
    ("MLflow", "ml-framework", [
        ("pypi", "mlflow"),
        ("file_content", r"import mlflow|mlflow\.log"),
    ]),
    ("Weights & Biases", "ml-framework", [
        ("pypi", "wandb"),
        ("file_content", r"import wandb|wandb\.init"),
    ]),
    # --- Data visualization ---
    ("Matplotlib", "data-visualization", [
        ("pypi", "matplotlib"),
        ("file_content", r"import matplotlib|from matplotlib"),
    ]),
    ("Seaborn", "data-visualization", [
        ("pypi", "seaborn"),
        ("file_content", r"import seaborn|from seaborn"),
    ]),
    ("Plotly", "data-visualization", [
        ("pypi", "plotly"),
        ("pkg_json_dep", "plotly"),
    ]),
    # --- Containerization ---
    ("Docker", "containerization", [
        ("file_exists", "Dockerfile"),
        ("file_exists", "docker-compose.yml"),
        ("file_exists", "docker-compose.yaml"),
        ("file_exists", ".dockerignore"),
    ]),
    ("Kubernetes", "containerization", [
        ("file_exists", "k8s"),
        ("file_exists", "kubernetes"),
        ("path_pattern", r"deployment\.ya?ml$|service\.ya?ml$|ingress\.ya?ml$"),
    ]),
    # --- Cloud / Deployment ---
    ("GitHub Actions", "cloud", [
        ("path_pattern", r"\.github/workflows/.*\.ya?ml$"),
    ]),
    ("Vercel", "cloud", [
        ("file_exists", "vercel.json"),
        ("file_content", r"vercel\.app|VERCEL"),
    ]),
    ("Render", "cloud", [
        ("file_exists", "render.yaml"),
        ("file_exists", "render.yml"),
    ]),
    ("Netlify", "cloud", [
        ("file_exists", "netlify.toml"),
        ("file_content", r"netlify\.app|NETLIFY"),
    ]),
    ("Railway", "cloud", [
        ("file_exists", "railway.json"),
        ("file_exists", "railway.toml"),
    ]),
    ("Fly.io", "cloud", [
        ("file_exists", "fly.toml"),
    ]),
    ("AWS", "cloud", [
        ("file_exists", "serverless.yml"),
        ("file_exists", "serverless.yaml"),
        ("file_content", r"amazonaws\.com|AWS_REGION|AWS_ACCESS_KEY"),
        ("path_pattern", r"\.aws/"),
    ]),
    # --- Infrastructure ---
    ("Terraform", "infrastructure", [
        ("path_pattern", r"\.tf$"),
        ("file_exists", "terraform"),
    ]),
    # --- Linting / Formatting ---
    ("ESLint", "linting", [
        ("file_exists", ".eslintrc"),
        ("file_exists", ".eslintrc.js"),
        ("file_exists", ".eslintrc.ts"),
        ("file_exists", ".eslintrc.json"),
        ("file_exists", "eslint.config.js"),
        ("file_exists", "eslint.config.mjs"),
        ("pkg_json_dep", "eslint"),
    ]),
    ("Prettier", "linting", [
        ("file_exists", ".prettierrc"),
        ("file_exists", ".prettierrc.json"),
        ("file_exists", "prettier.config.js"),
        ("pkg_json_dep", "prettier"),
    ]),
    ("Black", "linting", [
        ("pypi", "black"),
    ]),
    ("Ruff", "linting", [
        ("pypi", "ruff"),
        ("file_exists", "ruff.toml"),
    ]),
    # --- Package managers ---
    ("npm", "package-manager", [
        ("file_exists", "package-lock.json"),
    ]),
    ("yarn", "package-manager", [
        ("file_exists", "yarn.lock"),
    ]),
    ("pnpm", "package-manager", [
        ("file_exists", "pnpm-lock.yaml"),
    ]),
    ("Poetry", "package-manager", [
        ("file_exists", "poetry.lock"),
        ("pypi", "poetry"),
    ]),
    ("UV", "package-manager", [
        ("file_exists", "uv.lock"),
        ("file_content", r"\[tool\.uv\]"),
    ]),
    # --- Notebooks ---
    ("Jupyter", "notebook", [
        ("path_pattern", r"\.ipynb$"),
    ]),
    # --- CLI frameworks ---
    ("Click", "cli-framework", [
        ("pypi", "click"),
        ("file_content", r"import click|from click import|@click\.command"),
    ]),
    ("Typer", "cli-framework", [
        ("pypi", "typer"),
        ("file_content", r"import typer|from typer"),
    ]),
    ("argparse", "cli-framework", [
        ("file_content", r"import argparse|ArgumentParser\(\)"),
    ]),
    # --- React ecosystem ---
    ("React Router", "framework", [
        ("pkg_json_dep", "react-router-dom"),
        ("pkg_json_dep", "react-router"),
        ("file_content", r"from ['\"]react-router-dom['\"]|from ['\"]react-router['\"]"),
    ]),
    ("TanStack Query", "framework", [
        ("pkg_json_dep", "@tanstack/react-query"),
    ]),
    ("Redux", "framework", [
        ("pkg_json_dep", "@reduxjs/toolkit"),
        ("pkg_json_dep", "redux"),
    ]),
    ("Zustand", "framework", [
        ("pkg_json_dep", "zustand"),
    ]),
    ("Tailwind CSS", "styling", [
        ("pkg_json_dep", "tailwindcss"),
        ("file_exists", "tailwind.config.js"),
        ("file_exists", "tailwind.config.ts"),
    ]),
    # --- Type safety / validation ---
    ("Zod", "validation", [
        ("pkg_json_dep", "zod"),
        ("file_content", r"from ['\"]zod['\"]|import.*zod"),
    ]),
    ("Pydantic", "validation", [
        ("pypi", "pydantic"),
        ("file_content", r"from pydantic import|import pydantic"),
    ]),
]


# ---------------------------------------------------------------------------
# Main analyzer function
# ---------------------------------------------------------------------------

def analyze(
    files: list[dict],
    contents: dict[str, str],
) -> list[DetectedTechnology]:
    """
    Detect technologies from file tree and content.

    Args:
        files:    list of file metadata dicts (path, type, size)
        contents: dict mapping path → decoded text

    Returns:
        list of DetectedTechnology, each with evidence and confidence.
        Only technologies with at least one concrete evidence signal are returned.
    """
    paths = {f["path"] for f in files if f.get("type") == "blob"}
    filenames_lower = {p.rsplit("/", 1)[-1].lower() for p in paths}

    # Parse package.json if available
    pkg_deps: set[str] = set()
    pkg_dev_deps: set[str] = set()
    for path, text in contents.items():
        if path.endswith("package.json") and not _is_nested_pkg(path):
            try:
                data = json.loads(text)
                pkg_deps.update(data.get("dependencies", {}).keys())
                pkg_dev_deps.update(data.get("devDependencies", {}).keys())
            except (json.JSONDecodeError, AttributeError):
                pass

    # Parse Python deps
    py_deps: set[str] = _extract_python_deps(paths, contents)

    results: list[DetectedTechnology] = []
    for name, category, patterns in _TECH_DEFINITIONS:
        evidence: list[str] = []
        for source, pattern in patterns:
            match source:
                case "pkg_json_dep":
                    if pattern in pkg_deps or pattern in pkg_dev_deps:
                        evidence.append(f"`package.json` dependency: `{pattern}`")
                case "pkg_json_dev":
                    if pattern in pkg_dev_deps:
                        evidence.append(f"`package.json` devDependency: `{pattern}`")
                case "pypi":
                    if pattern in py_deps:
                        evidence.append(f"Python dependency: `{pattern}`")
                case "file_exists":
                    if _file_exists_anywhere(pattern.lower(), filenames_lower, paths):
                        evidence.append(f"`{pattern}` detected")
                case "file_content":
                    matches = _find_content_matches(pattern, contents)
                    if matches:
                        sample = matches[:2]
                        evidence.append(
                            f"Pattern `{pattern[:40]}` in: {', '.join(f'`{p}`' for p in sample)}"
                        )
                case "path_pattern":
                    matches = [p for p in paths if re.search(pattern, p, re.I)]
                    if matches:
                        sample = matches[:2]
                        evidence.append(
                            f"Files matching `{pattern}`: {', '.join(f'`{p}`' for p in sample)}"
                        )

        if evidence:
            results.append(DetectedTechnology(
                name=name,
                category=category,
                evidence=evidence,
                confidence=_confidence(len(evidence)),
            ))

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_nested_pkg(path: str) -> bool:
    """Ignore package.json files inside node_modules or other nested dirs."""
    parts = path.split("/")
    return any(p in {"node_modules", ".pnpm", "vendor"} for p in parts[:-1])


def _extract_python_deps(paths: set[str], contents: dict[str, str]) -> set[str]:
    deps: set[str] = set()
    for path, text in contents.items():
        if path.endswith("requirements.txt"):
            for line in text.splitlines():
                line = re.sub(r"[><=!#\s].*", "", line.strip()).lower()
                if line:
                    deps.add(line)
        elif path.endswith(("pyproject.toml", "setup.py", "setup.cfg", "Pipfile")):
            # Extract package names with a simple pattern
            for m in re.findall(r"""['"]([\w\-]+)['"]\s*(?:[><=!]|,|$)""", text):
                deps.add(m.lower())
            # Also capture simple word tokens in dependencies sections
            for line in text.splitlines():
                if re.search(r"dependencies|requires|install_requires", line, re.I):
                    continue
                m = re.match(r'^\s*["\']?([\w][\w\-]+)["\']?\s*(?:[><=!,\[]|$)', line)
                if m:
                    deps.add(m.group(1).lower())
    return deps


def _file_exists_anywhere(filename_lower: str, filenames: set[str], paths: set[str]) -> bool:
    if filename_lower in filenames:
        return True
    # Also check if filename_lower is a directory component
    return any(
        filename_lower in p.lower().split("/")
        for p in paths
    )


def _find_content_matches(pattern: str, contents: dict[str, str]) -> list[str]:
    result = []
    for path, text in contents.items():
        if re.search(pattern, text, re.I | re.MULTILINE):
            result.append(path)
        if len(result) >= 5:
            break
    return result


def _confidence(signal_count: int) -> Confidence:
    if signal_count >= 3:
        return Confidence.HIGH
    if signal_count >= 2:
        return Confidence.MEDIUM
    return Confidence.LOW
