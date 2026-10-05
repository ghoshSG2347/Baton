"""Compatibility projection of canonical type/data findings."""
def analyze(contents):
    from app.intelligence.pipeline import run
    files = [{'path': p, 'type': 'blob', 'size': len(t.encode())} for p, t in contents.items()]
    intelligence = run(files, contents, {}, [])
    return {'types': intelligence.types, 'mock_data': intelligence.mock_data}
