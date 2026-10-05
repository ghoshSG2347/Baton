"""Compatibility projection; no independent framework interpretation."""
def analyze(files):
    from app.intelligence.pipeline import run
    intelligence = run(files, {}, {}, [])
    return {'detected': intelligence.stack_detected, 'languages': intelligence.stack_languages}
