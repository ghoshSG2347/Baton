from app.generators.context_generator import generate

def test_context():
    analysis = {
        "metadata": {
            "owner": "example",
            "repo": "app",
            "branch": "main",
            "commit": "sha123",
            "generated": "2026-10-04T12:00:00Z",
            "skipped_files": ["huge_file.py"],
        },
        "stack": {"detected": ["React", "TypeScript"]},
        "file_tree": [{"path": "src/App.tsx"}, {"path": "package.json"}],
        "routes": ["app/api/routes.py: /api/items"],
        "api_calls": ["src/App.tsx: /api/items"],
        "types": ["User"],
        "mock_data": ["mock_user.json"],
        "environment_variables": ["API_KEY"],
        "handoffs": [{"path": "src/App.tsx", "items": ["TODO: add auth"]}],
        "analysis_warnings": ["1 file omitted"],
    }
    result = generate(analysis, 5000)
    md = result["markdown"]
    assert "# Baton Context" in md
    assert "> Baton Repository Context" in md
    assert "## Source" in md
    assert "## Requesting Member" in md
    assert "## Do Not Touch" in md
    assert "## Project Stack" in md
    assert "## Project Structure" in md
    assert "## Team Rules" in md
    assert "## Source Member" in md
    assert "## Completed Work" in md
    assert "## Detected Frontend Expectations" in md
    assert "## Routes" in md
    assert "## API Calls" in md
    assert "## Types / Data Shapes" in md
    assert "## Mock Data" in md
    assert "## Environment Variables" in md
    assert "## Handoff" in md
    assert "## Shared Files" in md
    assert "## Possible Integration Issues" in md
    assert "## Stray / Out-of-structure Files" in md
    assert "## Not Detected" in md
    assert "## Files Included for Verification" in md
    assert "huge_file.py" in result["omitted"]
    assert result["estimated_tokens"] > 0

def test_context_byte_limit_trimming():
    analysis = {"metadata": {}, "stack": {"detected": []}, "file_tree": []}
    result = generate(analysis, max_bytes=80)
    assert len(result["markdown"].encode("utf-8")) <= 120
    assert any("trimmed" in msg.lower() for msg in result["omitted"])
