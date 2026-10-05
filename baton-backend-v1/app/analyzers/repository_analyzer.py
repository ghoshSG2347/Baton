from app.intelligence.pipeline import run

class RepositoryAnalyzer:
    def analyze(self, files, contents, metadata=None):
        metadata = metadata or {}
        return run(files, contents, metadata, metadata.get('skipped_files', [])).to_legacy_analysis()
