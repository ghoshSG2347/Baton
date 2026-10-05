import re

METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


def _iter_values(payload, keys):
    if not isinstance(payload, dict):
        return []
    values = []
    for key in keys:
        value = payload.get(key, [])
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            values.extend(value)
    return values


def normalize_endpoint(entry: str) -> str:
    if not entry or not isinstance(entry, str):
        return ""

    endpoint = entry.strip()
    if not endpoint:
        return ""

    prefix_match = re.match(r"^(?P<prefix>.+?):\s*(?P<rest>(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+\S.*|/.*)$", endpoint, re.I)
    if prefix_match:
        candidate_prefix = prefix_match.group("prefix").strip()
        candidate_rest = prefix_match.group("rest").strip()
        if candidate_prefix and not re.match(r"^(?:https?:|wss?:|ftp:)", candidate_prefix, re.I):
            if re.search(r"[\\/].*\.[A-Za-z0-9]+$", candidate_prefix) or re.search(r"\.[A-Za-z0-9]+$", candidate_prefix):
                endpoint = candidate_rest

    endpoint = re.sub(r"\s+", " ", endpoint).strip()
    if not endpoint:
        return ""

    parts = endpoint.split(None, 1)
    if len(parts) == 2 and parts[0].upper() in METHODS:
        return f"{parts[0].upper()} {parts[1].strip()}"
    return endpoint


def compare(frontend: dict, backend: dict) -> dict:
    frontend = frontend or {}
    backend = backend or {}
    if 'canonical_api' in frontend and 'canonical_api' in backend:
        return _compare_canonical(frontend['canonical_api'], backend['canonical_api'])

    frontend_values = _iter_values(frontend, ["api_calls"]) if frontend.get("api_calls") else _iter_values(frontend, ["routes"])
    backend_values = _iter_values(backend, ["routes"]) if backend.get("routes") else _iter_values(backend, ["api_calls"])

    fe_endpoints = []
    be_endpoints = []
    for values, target in ((frontend_values, fe_endpoints), (backend_values, be_endpoints)):
        for value in values:
            endpoint = normalize_endpoint(value)
            if endpoint:
                target.append(endpoint)

    frontend_keys = {_endpoint_key(item) for item in fe_endpoints}
    backend_keys = {_endpoint_key(item) for item in be_endpoints}

    unmatched_fe = sorted({item for item in fe_endpoints if _endpoint_key(item) not in backend_keys})
    unmatched_be = sorted({item for item in be_endpoints if _endpoint_key(item) not in frontend_keys})
    compatible = frontend_keys <= backend_keys if frontend_keys else frontend_keys == backend_keys

    return {
        "frontend_routes": sorted(fe_endpoints),
        "backend_routes": sorted(be_endpoints),
        "unmatched_frontend_routes": unmatched_fe,
        "unmatched_backend_routes": unmatched_be,
        "compatible": compatible,
    }


def _endpoint_key(endpoint: str) -> str:
    if not endpoint:
        return ""
    match = re.match(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(.*)$", endpoint.strip(), re.I)
    if match:
        return match.group(2).strip()
    return endpoint.strip()


def _compare_canonical(frontend, backend):
    from app.analyzers.dependency_analyzer import paths_match
    consumers = [c for c in frontend.get('consumers', []) if not c.get('external')]
    endpoints = backend.get('endpoints', [])
    def matched(call, route):
        return route['method'] in {call['method'], 'UNKNOWN'} and paths_match(route['route'], call['route'])
    def label(endpoint):
        return f"{endpoint['method']} {endpoint['route']}"
    unmatched_calls = [label(c) for c in consumers if not any(matched(c, e) for e in endpoints)]
    unmatched_endpoints = [label(e) for e in endpoints if not any(matched(c, e) for c in consumers)]
    return {
        'frontend_routes': sorted({label(c) for c in consumers}),
        'backend_routes': sorted({label(e) for e in endpoints}),
        'unmatched_frontend_routes': sorted(set(unmatched_calls)),
        'unmatched_backend_routes': sorted(set(unmatched_endpoints)),
        'compatible': not unmatched_calls,
    }
