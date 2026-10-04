from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.utils.text_utils import language_for

def test_analysis_is_deterministic():
    files = [{"path": "package.json", "type": "blob"}, {"path": "main.py", "type": "blob"}]
    contents = {"package.json": "{}", "main.py": "print('hello')"}
    metadata = {
        "owner": "test-owner",
        "repo": "test-repo",
        "branch": "main",
        "folder": "",
        "commit": "abcdef123456",
        "generated": "2026-10-04T12:00:00+00:00",
        "files_analyzed": 2,
    }
    r = RepositoryAnalyzer().analyze(files, contents, metadata)
    assert "Node.js" in r["stack"]["detected"]
    assert "Python" in r["stack"]["detected"]
    assert r["metadata"]["commit"] == "abcdef123456"
    assert r["metadata"]["generated"] == "2026-10-04T12:00:00+00:00"
    assert r["metadata"]["files_analyzed"] == 2

def test_language_detection():
    assert language_for("app/main.py") == "python"
    assert language_for("src/App.tsx") == "typescript"
    assert language_for("src/index.ts") == "typescript"
    assert language_for("src/component.jsx") == "javascript"
    assert language_for("src/script.js") == "javascript"
    assert language_for("data.json") == "json"
    assert language_for("README.md") == "markdown"
    assert language_for("pyproject.toml") == "toml"
    assert language_for("unknown.xyz") is None

def test_analysis_skipped_files():
    metadata = {
        "owner": "o", "repo": "r", "branch": "b", "folder": "",
        "commit": "sha", "generated": "2026-10-04T00:00:00Z", "files_analyzed": 1,
        "skipped_files": ["big_binary.bin", "extra_file.py"]
    }
    r = RepositoryAnalyzer().analyze([{"path": "main.py", "type": "blob"}], {"main.py": ""}, metadata)
    assert r["metadata"]["skipped_files"] == ["big_binary.bin", "extra_file.py"]

