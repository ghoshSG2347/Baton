def normalize_endpoint(entry: str) -> str:
    if not entry or not isinstance(entry, str):
        return ""
    endpoint = entry.split(": ", 1)[1] if ": " in entry else entry
    endpoint = endpoint.strip()
    parts = endpoint.split(None, 1)
    if len(parts) == 2 and parts[0].upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
        endpoint = f"{parts[0].upper()} {parts[1].strip()}"
    return endpoint

def compare(frontend: dict, backend: dict) -> dict:
    raw_fe = frontend.get("api_calls", []) + frontend.get("routes", [])
    raw_be = backend.get("routes", []) + backend.get("api_calls", [])
    fe_endpoints = {norm for x in raw_fe if (norm := normalize_endpoint(x))}
    be_endpoints = {norm for x in raw_be if (norm := normalize_endpoint(x))}
    unmatched_fe = sorted(fe_endpoints - be_endpoints)
    unmatched_be = sorted(be_endpoints - fe_endpoints)
    compatible = (fe_endpoints <= be_endpoints) if fe_endpoints else (fe_endpoints == be_endpoints)
    return {
        "frontend_routes": sorted(fe_endpoints),
        "backend_routes": sorted(be_endpoints),
        "unmatched_frontend_routes": unmatched_fe,
        "unmatched_backend_routes": unmatched_be,
        "compatible": compatible,
    }
