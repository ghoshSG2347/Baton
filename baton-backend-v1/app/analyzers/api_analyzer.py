"""Compatibility adapter; API facts come from the canonical analyzer."""
from app.analyzers import dependency_analyzer as api

def analyze(contents):
    from app.analyzers.code_structure_analyzer import code_contents
    from app.intelligence.safety import sanitize_file, sensitive_path
    contents = code_contents({p: sanitize_file(p, t) for p, t in contents.items() if not sensitive_path(p)})
    return {
        'routes': api.to_legacy_routes(api.analyze_routes(contents)),
        'api_calls': api.to_legacy_api_calls(api.analyze_api_calls(contents)),
        'environment_variables': api.analyze_env_variables(contents),
    }
