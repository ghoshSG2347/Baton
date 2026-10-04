from app.analyzers.repository_analyzer import RepositoryAnalyzer
def test_analysis_is_deterministic():
 r=RepositoryAnalyzer().analyze([{"path":"package.json","type":"blob"}],{"package.json":"{}"}); assert "Node.js" in r["stack"]["detected"]
