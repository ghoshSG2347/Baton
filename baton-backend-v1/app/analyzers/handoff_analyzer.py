"""Compatibility projection of canonical handoff findings."""
def analyze(contents):
    from app.intelligence.pipeline import run
    files = [{'path': p, 'type': 'blob'} for p in contents]
    return run(files, contents, {}, []).handoffs
