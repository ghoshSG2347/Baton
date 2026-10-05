"""
Dependency and API analysis.

This is an upgraded replacement for the old api_analyzer.py.

What it does:
  1. Detects API route declarations (server-side) with source file evidence
  2. Detects API calls from client code with source file evidence
  3. Matches frontend callers to backend endpoints
  4. Detects important import relationships between files
  5. Produces normalized ApiEndpoint records (not raw strings)

What it does NOT do:
  - Validate request/response schemas against each other (Phase 2+)
  - Execute any code
  - Assume frontend/backend exists — everything is optional

Backward compatibility:
  - Also produces the old-format `routes` and `api_calls` string lists
    for legacy API consumers (e.g. existing integration route).
"""

from __future__ import annotations

import re
from typing import Optional

from app.intelligence.models import ApiEndpoint, Confidence

# ---------------------------------------------------------------------------
# Route detection patterns
# ---------------------------------------------------------------------------

# Server-side route patterns: (pattern, method_group, path_group)
_ROUTE_PATTERNS: list[tuple[str, Optional[int], int]] = [
    # FastAPI / Flask / Starlette:  @app.get("/route") or @router.post("/route")
    (r'@(?:\w+)\.(?P<method>get|post|put|patch|delete|head|options)\s*\(\s*[\'"](?P<path>[^\'"]+)[\'"]',
     None, 0),
    # Express.js: app.get('/route', ...) or router.post('/route', ...)
    (r'(?:app|router)\.(?P<method>get|post|put|patch|delete|use)\s*\(\s*[\'"](?P<path>[^\'"]+)[\'"]',
     None, 0),
    # NestJS: @Get('/route'), @Post('/route')
    (r'@(?P<method>Get|Post|Put|Patch|Delete|Head|Options)\s*\(\s*[\'"](?P<path>[^\'"]+)[\'"]',
     None, 0),
    # Django URL patterns: path('route/', view)
    (r'path\s*\(\s*[\'"](?P<path>[^\'"]+)[\'"]', None, 0),
    # Flask route: @app.route('/path', methods=['POST'])
    (r'@\w+\.route\s*\(\s*[\'"](?P<path>[^\'"]+)[\'"](?:.*?methods\s*=\s*\[([^\]]+)\])?', None, 0),
]

# Client-side API call patterns
_CALL_PATTERNS: list[tuple[str, Optional[int], int]] = [
    # fetch('/api/endpoint') or fetch("https://example.com/api")
    (r'fetch\s*\(\s*[\'"](?P<url>[^\'"]+)[\'"]', None, 0),
    # axios.get/post('/api/endpoint')
    (r'axios\.(?P<method>get|post|put|patch|delete)\s*\(\s*[\'"](?P<url>[^\'"]+)[\'"]', None, 0),
    # $.ajax / $.get / $.post (jQuery)
    (r'\$\.(?:ajax|get|post)\s*\(\s*[\'"](?P<url>[^\'"]+)[\'"]', None, 0),
    # httpx / requests (Python clients)
    (r'(?:httpx|requests)\.(?P<method>get|post|put|patch|delete)\s*\(\s*[\'"](?P<url>[^\'"]+)[\'"]', None, 0),
    # Template literal: fetch(`/api/${id}`)  — capture just the static prefix
    (r'fetch\s*\(`(/api[^`$]*)\`', None, 0),
]

_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


# ---------------------------------------------------------------------------
# Main functions
# ---------------------------------------------------------------------------

def analyze_routes(contents: dict[str, str]) -> list[ApiEndpoint]:
    """
    Detect server-side route declarations.

    Returns list of ApiEndpoint (structured, with source file and evidence).
    """
    endpoints: list[ApiEndpoint] = []
    seen: set[str] = set()

    for file_path, text in contents.items():
        for pattern, _, _ in _ROUTE_PATTERNS:
            for m in re.finditer(pattern, text, re.I | re.MULTILINE):
                route = _extract_path(m)
                if not route:
                    continue
                method = _extract_method(m, text, route)
                key = f"{method}:{route}"
                if key in seen:
                    continue
                seen.add(key)
                endpoints.append(ApiEndpoint(
                    route=route,
                    method=method,
                    source_file=file_path,
                    evidence=[f"Route declaration in `{file_path}`"],
                ))

    return endpoints


def analyze_api_calls(contents: dict[str, str]) -> list[ApiEndpoint]:
    """
    Detect client-side API calls.
    Returns list of ApiEndpoint with callers populated.
    """
    calls: list[ApiEndpoint] = []
    seen: set[str] = set()

    for file_path, text in contents.items():
        for pattern, _, _ in _CALL_PATTERNS:
            for m in re.finditer(pattern, text, re.I | re.MULTILINE):
                url = _extract_url(m)
                if not url or not _is_api_path(url):
                    continue
                method = _extract_method_from_call(m)
                key = f"{method}:{_normalize_path(url)}"
                if key in seen:
                    # Update callers if same endpoint called from different file
                    for c in calls:
                        if _normalize_path(c.route) == _normalize_path(url):
                            if file_path not in c.callers:
                                c.callers.append(file_path)
                    continue
                seen.add(key)
                calls.append(ApiEndpoint(
                    route=_normalize_path(url),
                    method=method,
                    source_file=file_path,
                    callers=[file_path],
                    evidence=[f"API call in `{file_path}`"],
                ))

    return calls


def match_routes_to_calls(
    routes: list[ApiEndpoint],
    calls: list[ApiEndpoint],
) -> list[ApiEndpoint]:
    """
    Match frontend API calls to backend route declarations.
    Updates route.callers with matched call sources.
    Returns the enriched routes list.
    """
    for call in calls:
        call_key = _normalize_path(call.route)
        for route in routes:
            route_key = _normalize_path(route.route)
            if call_key == route_key or call_key.rstrip("/") == route_key.rstrip("/"):
                for caller in call.callers:
                    if caller not in route.callers:
                        route.callers.append(caller)
                route.evidence.append(f"Matched caller: `{call.source_file}`")
    return routes


def to_legacy_routes(routes: list[ApiEndpoint]) -> list[str]:
    """
    Produce the legacy `routes` string list format:
    "source/file.py: /api/path"
    """
    return [f"{e.source_file}: {e.method} {e.route}" for e in routes]


def to_legacy_api_calls(calls: list[ApiEndpoint]) -> list[str]:
    """
    Produce the legacy `api_calls` string list format:
    "source/file.ts: /api/path"
    """
    return [f"{e.source_file}: {e.route}" for e in calls]


def analyze_env_variables(contents: dict[str, str]) -> list[str]:
    """
    Extract environment variable names from code.
    Returns sorted list of unique variable names (NOT values).
    """
    env_vars: set[str] = set()
    for text in contents.values():
        # process.env.VAR_NAME (Node.js)
        for m in re.finditer(r"process\.env\.([A-Z][A-Z0-9_]+)", text):
            env_vars.add(m.group(1))
        # os.environ['VAR'] or os.environ.get('VAR') (Python)
        for m in re.finditer(
            r'os\.environ(?:\.get)?\s*\(\s*[\'"]([A-Z][A-Z0-9_]+)[\'"]', text
        ):
            env_vars.add(m.group(1))
        # os.getenv('VAR') (Python)
        for m in re.finditer(r'os\.getenv\s*\(\s*[\'"]([A-Z][A-Z0-9_]+)[\'"]', text):
            env_vars.add(m.group(1))
        # import.meta.env.VITE_VAR (Vite)
        for m in re.finditer(r"import\.meta\.env\.([A-Z][A-Z0-9_]+)", text):
            env_vars.add(m.group(1))

    return sorted(env_vars)


def analyze_important_types(contents: dict[str, str]) -> list[str]:
    """
    Extract important TypeScript/Python type definitions.
    Filters out common noise (html, badge, for, safety, event, etc.)

    Returns sorted list of meaningful type/interface/class names.
    """
    all_types: set[str] = set()

    _NOISE: frozenset[str] = frozenset({
        "html", "badge", "for", "safety", "event", "error", "any", "never",
        "void", "unknown", "string", "number", "boolean", "object", "array",
        "promise", "optional", "required", "partial", "readonly",
        "record", "map", "set", "type", "interface", "class", "enum",
        "null", "undefined", "true", "false", "if", "else", "export",
        "default", "import", "return", "const", "let", "var", "function",
    })

    for path, text in contents.items():
        # TypeScript: interface Name { ... } or type Name = ...
        if path.endswith((".ts", ".tsx", ".d.ts")):
            for m in re.finditer(
                r"(?:export\s+)?(?:interface|type)\s+([A-Z][A-Za-z0-9]+)", text
            ):
                name = m.group(1)
                if name.lower() not in _NOISE and len(name) >= 3:
                    all_types.add(name)
        # Python: class Name or dataclass or Pydantic model
        if path.endswith(".py"):
            for m in re.finditer(
                r"class\s+([A-Z][A-Za-z0-9]+)\s*(?:\(|:)", text
            ):
                name = m.group(1)
                if name.lower() not in _NOISE and len(name) >= 3:
                    all_types.add(name)

    return sorted(all_types)


def analyze_handoffs(contents: dict[str, str]) -> list[dict]:
    """
    Extract TODO/FIXME/HANDOFF markers.
    Returns list of {path, items} dicts (preserves old format).
    """
    results: list[dict] = []
    for path, text in contents.items():
        items = [
            line.strip()
            for line in text.splitlines()
            if re.search(r"\b(?:TODO|FIXME|HANDOFF|HACK)\b", line, re.I)
        ]
        if items:
            results.append({"path": path, "items": items[:10]})
    return results


def analyze_imports(contents: dict[str, str]) -> dict[str, list[str]]:
    """
    Build a lightweight import dependency map.
    Returns {file_path: [imported_paths]} for local (relative) imports only.
    """
    deps: dict[str, list[str]] = {}
    for path, text in contents.items():
        local_imports: list[str] = []
        # JS/TS relative imports
        for m in re.finditer(r"from\s+['\"](\./[^'\"]+|\.\.\/[^'\"]+)['\"]", text):
            local_imports.append(m.group(1))
        # Python relative imports
        for m in re.finditer(r"from\s+(\.{1,2}[\w.]+)\s+import", text):
            local_imports.append(m.group(1))
        if local_imports:
            deps[path] = local_imports
    return deps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_path(match: re.Match) -> Optional[str]:
    try:
        return match.group("path")
    except IndexError:
        return None


def _extract_url(match: re.Match) -> Optional[str]:
    try:
        return match.group("url")
    except IndexError:
        try:
            return match.group(1)
        except IndexError:
            return None


def _extract_method(match: re.Match, text: str, route: str) -> str:
    try:
        method = match.group("method").upper()
        if method in _HTTP_METHODS:
            return method
    except (IndexError, AttributeError):
        pass
    # Check for methods= in Flask @app.route style
    remaining = text[match.end():match.end() + 100]
    methods_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", remaining, re.I)
    if methods_match:
        m_list = re.findall(r"['\"](\w+)['\"]", methods_match.group(1))
        if m_list:
            return m_list[0].upper()
    return "UNKNOWN"


def _extract_method_from_call(match: re.Match) -> str:
    try:
        method = match.group("method").upper()
        if method in _HTTP_METHODS:
            return method
    except (IndexError, AttributeError):
        pass
    return "GET"


def _is_api_path(url: str) -> bool:
    """Filter out non-API URLs (static assets, full external URLs we don't care about)."""
    if url.startswith(("https://", "http://", "//")) and "/api" not in url:
        return False
    # Must start with / or be a relative path with /api
    return url.startswith("/") or "/api" in url


def _normalize_path(path: str) -> str:
    """
    Normalize a path for comparison:
    - Remove query strings
    - Remove trailing slashes
    - Remove template literal variables like ${id}
    """
    # Remove query string
    path = path.split("?")[0]
    # Remove JS template literal variables
    path = re.sub(r"\$\{[^}]+\}", ":param", path)
    # Remove trailing slash
    path = path.rstrip("/")
    return path.lower()
