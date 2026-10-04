from datetime import datetime, timezone

from app.utils.token_budget import estimate_tokens, fit_context


def _bullets(values):
    return [f"- {value}" for value in values] or ["- None detected"]


def generate(analysis, max_bytes):
    metadata = analysis.get("metadata", {})
    stack = analysis.get("stack", {}).get("detected", [])
    files = analysis.get("file_tree", [])
    lines = [
        "# Baton Context",
        "> Baton Repository Context",
        "",
        "## Source",
        f"- Repository: {metadata.get('owner', 'unknown')}/{metadata.get('repo', 'unknown')}",
        f"- Branch: {metadata.get('branch', 'unknown')}",
        f"- Commit: {metadata.get('commit') or 'Not available'}",
        f"- Generated: {metadata.get('generated') or datetime.now(timezone.utc).isoformat()}",
        "",
        "## Requesting Member",
        "- Name: Not configured",
        "- Role: Not configured",
        "- Owns: Not configured",
        "",
        "## Do Not Touch",
        "- No ownership boundaries configured",
        "",
        "## Project Stack",
    ]
    lines += _bullets(stack or ["Not detected"])
    lines += ["", "## Project Structure"] + _bullets([x.get("path") for x in files])
    lines += ["", "## Team Rules", "- No team rules supplied", "", "## Source Member", "- Not configured"]
    lines += ["", "## Completed Work", "- Deterministic repository scan completed"]
    lines += ["", "## Detected Frontend Expectations"] + _bullets(analysis.get("types", []))
    for title, key in (
        ("Routes", "routes"),
        ("API Calls", "api_calls"),
        ("Types / Data Shapes", "types"),
        ("Mock Data", "mock_data"),
        ("Environment Variables", "environment_variables"),
        ("Handoff", "handoffs"),
        ("Shared Files", "shared_files"),
        ("Possible Integration Issues", "analysis_warnings"),
        ("Stray / Out-of-structure Files", "stray_files"),
    ):
        lines += ["", f"## {title}"] + _bullets(analysis.get(key, []))
    lines += [
        "",
        "## Not Detected",
        "- Ownership configuration, contracts, and recent commit subjects were not supplied to this request.",
        "",
        "## Files Included for Verification",
    ] + _bullets([x.get("path") for x in files])

    raw = "\n".join(lines)
    text = fit_context(raw, max_bytes)
    omitted = []
    if len(text) < len(raw):
        omitted.append("Context was trimmed to the configured byte budget.")
    omitted += metadata.get("skipped_files", [])
    return {"markdown": text, "estimated_tokens": estimate_tokens(text), "omitted": omitted}
