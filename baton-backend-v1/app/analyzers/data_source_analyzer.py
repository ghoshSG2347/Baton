"""
Data source classification.

Classifies data files found in the repository into meaningful categories:
  dataset         — tabular/structured data for ML or analysis (CSV, Parquet, etc.)
  model-artifact  — trained model files (.pt, .pkl, .onnx, .h5, .safetensors)
  fixture         — test fixtures or seed data
  mock            — mock data for development/testing
  config          — application configuration (JSON, YAML, TOML config files)
  static-data     — static application data (lookup tables, translations, etc.)
  training-artifact — experiment outputs, checkpoints, logs
  test-data       — data used only in tests
  generated       — auto-generated files (don't analyze manually)
  seed            — database seed data
  unknown         — unclear classification

Critical: do NOT call every JSON file "mock data."
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Optional

from app.intelligence.models import Confidence, DataSource

# ---------------------------------------------------------------------------
# Extension-based classification signals
# ---------------------------------------------------------------------------

_DATASET_EXTENSIONS: frozenset[str] = frozenset({
    ".csv", ".tsv", ".parquet", ".feather", ".arrow",
    ".hdf5", ".h5", ".npy", ".npz", ".mat",
    ".jsonl", ".json_lines",
})

_MODEL_ARTIFACT_EXTENSIONS: frozenset[str] = frozenset({
    ".pt", ".pth", ".pkl", ".pickle",
    ".onnx", ".pb", ".tflite",
    ".safetensors", ".bin",
    ".h5",    # shared with HDF5 dataset — use context
    ".ckpt",
    ".joblib",
})

_CONFIG_EXTENSIONS: frozenset[str] = frozenset({
    ".env", ".ini", ".cfg", ".conf",
})

_CONFIG_FILENAMES: frozenset[str] = frozenset({
    ".env", ".env.example", ".env.sample", ".env.local",
    "config.json", "config.yaml", "config.yml", "config.toml",
    "settings.json", "settings.yaml", "settings.toml",
    "appsettings.json",
})

# Path fragments that hint at a particular classification
_PATH_HINTS: list[tuple[str, str]] = [
    # Exact fragment, classification
    ("test", "test-data"),
    ("spec", "test-data"),
    ("fixture", "fixture"),
    ("seed", "seed"),
    ("mock", "mock"),
    ("fake", "mock"),
    ("dummy", "mock"),
    ("sample", "static-data"),
    ("example", "static-data"),
    ("translation", "static-data"),
    ("locale", "static-data"),
    ("i18n", "static-data"),
    ("checkpoint", "training-artifact"),
    ("checkpoints", "training-artifact"),
    ("artifact", "training-artifact"),
    ("artifacts", "training-artifact"),
    ("experiment", "training-artifact"),
    ("run", "training-artifact"),
    ("logs", "training-artifact"),
    ("output", "training-artifact"),
    ("model", "model-artifact"),
    ("models", "model-artifact"),
    ("weights", "model-artifact"),
    ("pretrained", "model-artifact"),
    ("dataset", "dataset"),
    ("datasets", "dataset"),
    ("data", "dataset"),  # weak hint — need extension support
    ("raw_data", "dataset"),
    ("processed", "dataset"),
    ("features", "dataset"),
    ("generated", "generated"),
    ("dist", "generated"),
    ("build", "generated"),
]

# Content patterns that indicate dataset use
_DATASET_CONTENT_PATTERNS: list[str] = [
    r"pd\.read_csv|read_parquet|np\.load|torch\.load.*\.csv",
    r"read_csv\(|read_parquet\(|load_dataset\(",
    r"DataLoader|Dataset\(|from_csv|from_parquet",
]

# Content patterns that indicate model loading
_MODEL_CONTENT_PATTERNS: list[str] = [
    r"torch\.load\(|tf\.keras\.models\.load|joblib\.load\(",
    r"load_weights\(|from_pretrained\(",
    r"pickle\.load\(",
]


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def analyze(
    files: list[dict],
    contents: dict[str, str],
) -> list[DataSource]:
    """
    Classify data files in the repository.

    Args:
        files:    file tree metadata
        contents: decoded file contents (may be absent for large/binary files)

    Returns:
        list of DataSource with classification and evidence
    """
    sources: list[DataSource] = []

    # Build a set of paths that are consumed by Python/ML code
    consumed_by: dict[str, list[str]] = _find_data_consumers(contents)

    for f in files:
        path = f.get("path", "")
        if not path or f.get("type") != "blob":
            continue

        classification, evidence, confidence = _classify(path, contents, consumed_by)
        if classification is None:
            continue

        consumers = consumed_by.get(path, [])
        sources.append(DataSource(
            path=path,
            classification=classification,
            consumers=consumers,
            evidence=evidence,
            confidence=confidence,
        ))

    return sources


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------

def _classify(
    path: str,
    contents: dict[str, str],
    consumed_by: dict[str, list[str]],
) -> tuple[Optional[str], list[str], Confidence]:
    """Return (classification, evidence, confidence) or (None, [], LOW) if not a data file."""
    ext = PurePosixPath(path).suffix.lower()
    filename = PurePosixPath(path).name.lower()
    path_lower = path.lower()
    path_parts = set(path_lower.replace("\\", "/").split("/"))

    evidence: list[str] = []

    # --- Skip non-data files ---
    code_exts = {
        ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".c",
        ".cpp", ".cs", ".rb", ".php", ".sh", ".md", ".rst", ".txt",
        ".html", ".css", ".scss",
    }
    if ext in code_exts:
        return None, [], Confidence.LOW

    # --- Model artifact (check before dataset since .h5 is shared) ---
    if ext in _MODEL_ARTIFACT_EXTENSIONS:
        is_model = "model" in path_lower or "weight" in path_lower or "checkpoint" in path_lower
        is_data = "data" in path_lower or "dataset" in path_lower
        if is_model or (ext in {".pt", ".pth", ".onnx", ".safetensors", ".ckpt"}):
            evidence.append(f"Model artifact extension `{ext}`")
            return "model-artifact", evidence, Confidence.HIGH
        if ext == ".pkl" and is_data:
            evidence.append("Pickle file in data context")
            return "dataset", evidence, Confidence.MEDIUM
        evidence.append(f"Possible model artifact: `{ext}`")
        return "model-artifact", evidence, Confidence.MEDIUM

    # --- Dataset extensions ---
    if ext in _DATASET_EXTENSIONS:
        classification = "dataset"
        confidence = Confidence.MEDIUM
        evidence.append(f"Dataset file extension `{ext}`")

        consumers = consumed_by.get(path, [])
        if consumers:
            evidence.append(f"Consumed by: {', '.join(f'`{c}`' for c in consumers[:3])}")
            confidence = Confidence.HIGH

        # Path hints
        for hint, cls in _PATH_HINTS:
            if hint in path_parts:
                if cls == "test-data":
                    classification = "test-data"
                    evidence.append(f"Path contains `{hint}/` (test context)")
                elif cls == "training-artifact":
                    classification = "training-artifact"
                    evidence.append(f"Path contains `{hint}/`")
                break

        return classification, evidence, confidence

    # --- Config files ---
    if ext in _CONFIG_EXTENSIONS or filename in _CONFIG_FILENAMES:
        evidence.append(f"Configuration file: `{filename}`")
        return "config", evidence, Confidence.HIGH

    # --- JSON / YAML / TOML — need context ---
    if ext in {".json", ".yaml", ".yml", ".toml"}:
        return _classify_json_yaml(path, path_lower, path_parts, filename, ext, evidence, contents)

    return None, [], Confidence.LOW


def _classify_json_yaml(
    path: str,
    path_lower: str,
    path_parts: set[str],
    filename: str,
    ext: str,
    evidence: list[str],
    contents: dict[str, str],
) -> tuple[Optional[str], list[str], Confidence]:
    """Classify JSON/YAML/TOML files by context rather than assuming mock data."""

    # Config filenames
    if filename in _CONFIG_FILENAMES:
        evidence.append(f"Known configuration filename: `{filename}`")
        return "config", evidence, Confidence.HIGH

    # Path-based classification
    for hint, cls in _PATH_HINTS:
        if hint in path_parts:
            evidence.append(f"Path contains `{hint}/`")
            if cls in {"mock", "fixture", "seed", "test-data", "static-data"}:
                return cls, evidence, Confidence.MEDIUM

    # Package / build metadata — skip
    if filename in {
        "package.json", "package-lock.json", "tsconfig.json",
        "next.config.js", "vercel.json", "render.yaml",
        "pyproject.toml", "cargo.toml", "go.mod",
        "turbo.json", "nx.json",
    }:
        return None, [], Confidence.LOW   # project metadata, not data file

    # Generated / dist artifacts
    if any(p in path_parts for p in {"dist", "build", ".next", ".nuxt", "__pycache__"}):
        return "generated", ["Generated output path"], Confidence.HIGH

    consumers = _find_data_consumers(contents).get(path, [])
    if consumers:
        return 'static-data', [f'Referenced by {", ".join(sorted(set(consumers)))}'], Confidence.MEDIUM
    return 'unknown', [f'Structured file {path}; purpose not determined'], Confidence.LOW


def _find_data_consumers(contents: dict[str, str]) -> dict[str, list[str]]:
    """
    For each data file referenced in code, find which source files reference it.
    Returns {data_file_path: [consumer_paths]}
    """
    consumers: dict[str, list[str]] = {}
    patterns = [
        r"""['\"]([^'"]+\.(?:csv|parquet|json|pkl|h5|hdf5|npy|npz|tsv|feather))['\"]""",
        r"""open\s*\(\s*['\"]([^'"]+)['\"]""",
        r"""pd\.read_csv\s*\(\s*['\"]([^'"]+)['\"]""",
        r"""torch\.load\s*\(\s*['\"]([^'"]+)['\"]""",
    ]
    for src_path, text in contents.items():
        for pat in patterns:
            for m in re.finditer(pat, text, re.I):
                ref = m.group(1).strip("./")
                # Normalize: keep just the filename if it's a base path
                consumers.setdefault(ref, []).append(src_path)
    return consumers
