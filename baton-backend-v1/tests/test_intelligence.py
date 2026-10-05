import json
from dataclasses import asdict
from pathlib import Path

import pytest

from app.intelligence.pipeline import run
from app.intelligence.models import (
    DirectoryRole, EvidenceStatus, ImplementationStatus, ProjectType,
    SnapshotStatus, UserOverride,
)
from app.intelligence import snapshot
from app.intelligence.snapshot import MemorySnapshotStore
from app.analyzers.dependency_analyzer import _normalize_path, paths_match
from app.generators.context_generator import generate


FIXTURES = json.loads((Path(__file__).parent / 'fixtures/repositories.json').read_text())


def analyze(contents, **metadata):
    files = [{'path': p, 'type': 'blob', 'size': len(t.encode()), 'sha': 'blob-' + str(i)} for i, (p, t) in enumerate(contents.items())]
    return run(files, contents, {'owner': 'example', 'repo': 'project', 'branch': 'main', 'commit': 'commit-1', 'generated': '2026-10-05T00:00:00Z', **metadata}, [])


@pytest.mark.parametrize('fixture,expected,absent', [
    ('specification', ProjectType.SPECIFICATION_ONLY, ProjectType.BACKEND_API),
    ('readme', ProjectType.SPECIFICATION_ONLY, ProjectType.FRONTEND),
    ('ml', ProjectType.MACHINE_LEARNING, ProjectType.FRONTEND),
    ('frontend', ProjectType.FRONTEND, ProjectType.BACKEND_API),
    ('backend', ProjectType.BACKEND_API, ProjectType.FRONTEND),
    ('bookos', ProjectType.FULL_STACK, ProjectType.MACHINE_LEARNING),
    ('mixed', ProjectType.LIBRARY_SDK, ProjectType.SPECIFICATION_ONLY),
    ('scripts', ProjectType.SCRIPTING, ProjectType.BACKEND_API),
])
def test_universal_classification(fixture, expected, absent):
    intel = analyze(FIXTURES[fixture])
    assert expected in intel.project_types
    assert absent not in intel.project_types
    assert intel.project_type_evidence


def test_empty_repository():
    intel = analyze({})
    assert intel.project_types == [ProjectType.UNKNOWN]
    assert not intel.api_endpoints and not intel.components
    assert intel.completeness.files_discovered == 0


def test_prd_is_not_implementation_and_no_invented_features():
    intel = analyze(FIXTURES['specification'])
    assert intel.requirements
    assert all(r.status == ImplementationStatus.NOT_DETECTED for r in intel.requirements)
    assert all(r.category == EvidenceStatus.DOCUMENTED for r in intel.requirements)
    assert not intel.observed_features
    assert not intel.api_endpoints
    assert not intel.data_flows
    assert 'leaderboard' not in str(asdict(intel)).lower()


def test_documented_code_examples_are_not_observed():
    intel = analyze({'README.md': "# Features\nUses FastAPI\n```python\nfrom fastapi import FastAPI\n@app.get('/api/x')\ndef auth(): pass\n```\n- Users can authenticate.\n"})
    assert not intel.api_endpoints
    assert not intel.technologies
    assert all(r.status == ImplementationStatus.NOT_DETECTED for r in intel.requirements)


def test_matching_feature_is_candidate_not_behavioral_proof():
    intel = analyze({'PRD.md': '# Features\n- Users can login with email OTP.\n', 'login.py': 'def login():\n    return None\n'})
    req = intel.requirements[0]
    assert req.status == ImplementationStatus.PARTIALLY_IMPLEMENTED
    assert req.observed_code == ['login.py: login']
    assert req.missing_pieces


def test_literal_endpoint_requirement_can_be_mechanically_verified():
    intel = analyze({**FIXTURES['backend'], 'PRD.md': '# Requirements\n- Expose GET /health.\n'})
    assert intel.requirements[0].status == ImplementationStatus.IMPLEMENTED
    assert any('engine/main.py' in e for e in intel.requirements[0].evidence)


def test_odd_names_and_single_file_directories():
    intel = analyze({'backend/App.tsx': "import React from 'react';\nexport function App() { return <div />; }", 'frontend/main.py': 'from fastapi import FastAPI\napp=FastAPI()\n@app.get("/x")\ndef x(): return {}'})
    roles = {d.path: d for d in intel.directory_classifications}
    assert roles['backend'].role == DirectoryRole.FRONTEND
    assert roles['frontend'].role == DirectoryRole.BACKEND
    assert roles['backend'].observed_role == DirectoryRole.FRONTEND.value
    assert any('backend/App.tsx' in e for e in roles['backend'].evidence)


def test_ambiguous_directory_preserves_uncertainty():
    intel = analyze(FIXTURES['ambiguous'])
    assert next(d for d in intel.directory_classifications if d.path == 'core').role == DirectoryRole.AMBIGUOUS


def test_bookos_api_shared_contracts_rules_and_relationships():
    intel = analyze(FIXTURES['bookos'])
    endpoint = next(e for e in intel.api_endpoints if e.route == '/api/ask-book')
    assert endpoint.method == 'POST'
    assert endpoint.handler == 'askBook'
    assert endpoint.callers == ['client/AskBook.tsx']
    assert {r.source_path for r in intel.repository_rules} == {'AGENTS.md', '.builder/rules/architecture.mdc'}
    assert next(d for d in intel.directory_classifications if d.path == 'shared').role == DirectoryRole.SHARED
    assert 'server/ai.ts' in intel.resolved_dependencies['server/routes.ts']
    assert any(m['name'] == 'AskRequest' for m in intel.data_models)
    assert not intel.conflicts
    assert any('ask-book' in flow for flow in intel.data_flows)
    assert 'static-data' == next(d.classification for d in intel.data_sources if d.path == 'data/books.json')
    assert intel.parsed_files
    assert intel.documentation_content['docs/architecture.md']


def test_ml_pipeline_without_web_invention():
    intel = analyze(FIXTURES['ml'])
    assert not intel.api_endpoints
    assert not ({ProjectType.FRONTEND, ProjectType.BACKEND_API, ProjectType.FULL_STACK} & set(intel.project_types))
    roles = {role for p in intel.parsed_files for role in p.semantic_roles}
    assert {'training', 'model_definition', 'preprocessing', 'evaluation', 'dataset_loading'} <= roles
    assert any(p.parse_status == 'NOTEBOOK_CELLS_PARSED' for p in intel.parsed_files)
    assert any(d.classification == 'model-artifact' for d in intel.data_sources)
    assert all('Feature Engineering' not in f for f in intel.data_flows)
    assert any(d['name'] == 'torch' for d in intel.package_dependencies)


def test_mixed_language_structures():
    intel = analyze(FIXTURES['mixed'])
    assert {'Rust', 'Go', 'C++', 'Java'} <= {l.name for l in intel.languages}
    assert any(s['name'] == 'Record' for p in intel.parsed_files for s in p.symbols)
    assert any(p.entrypoints == ['main'] for p in intel.parsed_files)


@pytest.mark.parametrize('call', ["fetch('/api/wrong')", "fetch('/api/right', {method: 'POST'})"])
def test_api_path_or_method_mismatch(call):
    intel = analyze({'server/main.py': "from fastapi import FastAPI\napp=FastAPI()\n@app.get('/api/right')\ndef right(): return {}", 'client/api.ts': call})
    assert not intel.api_endpoints[0].callers
    assert any('API consumer' in c.description for c in intel.conflicts)


def test_dynamic_paths_query_trailing_slash_and_case():
    assert paths_match('/api/users/{id}', '/api/users/42/?sort=name')
    assert _normalize_path('https://example.com/API/Item/?q=1') == '/API/Item'
    assert not paths_match('/API/Item', '/api/item')
    intel = analyze({'server.py': "@app.get('/users/{id}')\ndef user(id): return {}", 'client.ts': "fetch('/users/42/?q=1')"})
    assert intel.api_endpoints[0].callers == ['client.ts']


def test_external_api_never_matched_to_local_route():
    intel = analyze({'main.py': "@app.get('/api/x')\ndef x(): return {}", 'client.ts': "fetch('https://vendor.example/api/x')"})
    assert not intel.api_endpoints[0].callers
    assert intel.api_consumers[0].external
    assert not intel.conflicts


def test_fastapi_literal_mount_and_handler():
    intel = analyze({'app/main.py': "from app.routes import router\napp.include_router(router, prefix='/api')", 'app/routes.py': "from fastapi import APIRouter\nrouter = APIRouter(prefix='/v1')\n@router.get('/items')\ndef items(): return []", 'client.ts': "fetch('/api/v1/items')"})
    assert intel.api_endpoints[0].route == '/api/v1/items'
    assert intel.api_endpoints[0].handler == 'items'
    assert intel.api_endpoints[0].callers == ['client.ts']


def test_readme_vs_code_and_opposing_instructions():
    intel = analyze({'README.md': '# API\nGET /api/old\nUses React\n', 'main.py': "from fastapi import FastAPI\n@app.get('/api/new')\ndef new(): return {}", 'AGENTS.md': '# Rules\n- Always use shared contracts.\n', '.builder/rules.md': '# Rules\n- Never use shared contracts.\n'})
    assert {'Documented API differs from observed routes', 'Documented technology not detected', 'Opposing repository instructions'} <= {c.description for c in intel.conflicts}


def test_requirement_id_priority_section_and_prose():
    intel = analyze({'product-description.md': '# Features\n- FR-001 P0 Users can search.\n  Preserve the exact query.\nUsers must authenticate.\n'})
    req = intel.requirements[0]
    assert req.id == 'FR-001' and req.priority == 'P0'
    assert req.source_section == 'Features' and req.source_line == 2
    assert req.intent.endswith('Preserve the exact query.')
    assert len(intel.requirements) == 2


def test_nested_agent_scope():
    intel = analyze({'core/AGENTS.md': '# Rules\n- Never execute source.\n'})
    assert intel.repository_rules[0].scope == 'directory: core'


def test_secrets_excluded_from_all_snapshot_fields_and_context():
    intel = analyze({'README.md': '# Rules\nAPI_KEY="topsecret"\nBearer private-bearer\nhttps://user:pass@example.com\n', '.env': 'PASSWORD=private-env', '.env.example': 'API_KEY=template-secret\nPUBLIC_URL=template-url\n', 'main.py': 'import os\nAPI_KEY="inline-secret"\nclass Model: pass\n# TODO github_pat_PRIVATEVALUE\nurl = os.getenv("API_URL")\n'})
    encoded = json.dumps(asdict(intel), default=str) + generate(intel, 20000)['markdown']
    for value in ('topsecret', 'private-bearer', 'user:pass', 'private-env', 'template-secret', 'template-url', 'inline-secret', 'github_pat_PRIVATEVALUE'):
        assert value not in encoded
    assert 'API_KEY' in intel.environment_variables
    assert 'API_URL' in intel.environment_variables
    assert intel.completeness.omitted_paths == ['.env']


def test_user_override_model_preserves_observation():
    intel = analyze(FIXTURES['backend'])
    directory = next(d for d in intel.directory_classifications if d.path == 'engine')
    intel.user_overrides.append(UserOverride('engine', 'role', directory.role.value, DirectoryRole.SHARED.value, reason='Shared domain module'))
    directory.user_override = DirectoryRole.SHARED.value
    directory.override_source = 'USER'
    assert directory.observed_role == DirectoryRole.BACKEND.value
    assert intel.user_overrides[0].source == 'USER'


def test_omitted_inventory_and_blob_metadata():
    files = [{'path': 'large.py', 'type': 'blob', 'sha': 'blob123', 'size': 300000}]
    intel = run(files, {}, {'commit': 'exact', 'omission_reasons': {'large.py': 'file_size_limit'}}, ['large.py'])
    assert intel.file_tree[0]['sha'] == 'blob123'
    assert intel.completeness.omission_reasons['large.py'] == 'file_size_limit'
    assert intel.snapshot_status == SnapshotStatus.PARTIAL


def test_filtered_inventory_cannot_classify_project():
    intel = analyze({'README.md': '# Reference', 'node_modules/react/App.tsx': "import React from 'react';"})
    assert ProjectType.FRONTEND not in intel.project_types
    assert len(intel.file_tree) == 2


def test_snapshot_save_load_copy_scope_commit_version_invalidation():
    store = MemorySnapshotStore()
    intel = analyze(FIXTURES['backend'])
    store.save(intel)
    loaded = store.load('EXAMPLE', 'PROJECT', 'main', 'commit-1')
    assert loaded == intel
    loaded.unknowns.append('mutation')
    assert store.load('example', 'project', 'main', 'commit-1').unknowns != loaded.unknowns
    assert store.load('example', 'project', 'main', 'commit-2') is None
    assert store.load('example', 'project', 'main', 'commit-1', 'engine') is None
    assert store.exists('example', 'project', 'main', 'commit-1')
    intel.project_root = 'engine'
    store.save(intel)
    store.invalidate('example', 'project', commit='commit-1', folder='engine')
    assert len(store.metadata()) == 1
    intel.analysis_version = 'old'
    intel.commit = 'commit-3'
    store.save(intel)
    assert len(store.metadata()) == 1


def test_snapshot_eviction_and_byte_bound():
    store = MemorySnapshotStore(max_entries=1)
    first = analyze({})
    store.save(first)
    second = analyze({}, commit='commit-2')
    store.save(second)
    assert not store.exists('example', 'project', 'main', 'commit-1')
    assert store.exists('example', 'project', 'main', 'commit-2')
    tiny = MemorySnapshotStore(max_bytes=1)
    tiny.save(first)
    assert not tiny.metadata()


def test_snapshot_staleness_latest_copy_and_unknown_commit():
    snapshot.clear_all()
    try:
        first = analyze({})
        snapshot.save(first)
        assert snapshot.is_stale('example', 'project', 'main', 'commit-2')
        assert snapshot.get_stale_snapshot('example', 'project', 'main').snapshot_status == SnapshotStatus.STALE
        assert snapshot.load('example', 'project', 'main', 'commit-1').snapshot_status == SnapshotStatus.CURRENT
        second = analyze({}, commit='commit-2')
        snapshot.save(second)
        assert not snapshot.is_stale('example', 'project', 'main', 'commit-2')
        assert snapshot.get_stale_snapshot('example', 'project', 'main').commit == 'commit-2'
        unknown = analyze({}, commit=None)
        snapshot.save(unknown)
        assert snapshot.cache_size() == 2
    finally:
        snapshot.clear_all()


def test_pipeline_determinism_and_strict_context_byte_budget():
    assert analyze(FIXTURES['bookos']) == analyze(FIXTURES['bookos'])
    assert len(generate(analyze(FIXTURES['bookos']), 80)['markdown'].encode()) <= 80


def test_intelligence_never_executes_source_or_notebooks(tmp_path):
    marker = tmp_path / 'executed'
    malicious = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\nclass Danger: pass\n"
    intel = analyze({'main.py': malicious, 'experiment.ipynb': json.dumps({'cells': [{'cell_type': 'code', 'source': [malicious]}]})})
    assert not marker.exists()
    assert any(p.parse_status == 'PARSED' for p in intel.parsed_files)
    assert any(p.parse_status == 'NOTEBOOK_CELLS_PARSED' for p in intel.parsed_files)


def test_api_request_response_shape_references_and_sql_model():
    intel = analyze({'main.py': 'from fastapi import FastAPI\napp = FastAPI()\n@app.post("/items", response_model=ItemResponse)\ndef items(req: ItemRequest): return {}', 'schema.sql': 'CREATE TABLE items (id INTEGER PRIMARY KEY, title TEXT);'})
    endpoint = intel.api_endpoints[0]
    assert endpoint.request_shape == 'ItemRequest'
    assert endpoint.response_shape == 'ItemResponse'
    assert endpoint.related_types == ['ItemRequest', 'ItemResponse']
    assert any(m['kind'] == 'table' and m['name'] == 'items' for m in intel.data_models)


@pytest.mark.parametrize('path,text,expected', [
    ('device/sketch.ino', 'void setup() {}\nvoid loop() {}', ProjectType.EMBEDDED_IOT),
    ('mobile/Screen.kt', 'import android.app.Activity\nclass Screen: Activity()', ProjectType.MOBILE),
    ('game/main.py', 'import pygame\npygame.init()', ProjectType.GAME),
    ('desktop/main.py', 'import tkinter\nwindow = tkinter.Tk()', ProjectType.DESKTOP),
    ('tool/main.py', 'import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument("--name")', ProjectType.CLI),
])
def test_additional_project_families(path, text, expected):
    assert expected in analyze({path: text}).project_types


def test_canonical_integration_keeps_methods_and_dynamic_paths():
    from app.services.integration_service import compare
    backend = analyze({'main.py': '@app.get("/items/{id}")\ndef item(id): return {}'}).to_legacy_analysis()
    matching = analyze({'client.ts': 'fetch("/items/42")'}).to_legacy_analysis()
    mismatch = analyze({'client.ts': 'fetch("/items/42", {method: "POST"})'}).to_legacy_analysis()
    assert compare(matching, backend)['compatible']
    assert not compare(mismatch, backend)['compatible']


def test_document_provenance_and_requirement_conflict():
    intel = analyze({'README.md': '# API\n- GET /old\n', 'main.py': '@app.get("/new")\ndef new(): return {}'})
    assert intel.documentation_sources[0].commit == 'commit-1'
    assert intel.documentation_sources[0].blob_sha == 'blob-0'
    assert intel.requirements[0].status == ImplementationStatus.CONFLICTING


def test_comments_and_docstrings_do_not_classify_or_create_routes():
    intel = analyze({'main.py': '# from fastapi import FastAPI\n"""import torch\n@app.get("/fake")\n"""\ndef utility(): pass\n', 'tool.ts': '// import React from "react";\n/* app.get("/fake", handler); */\nexport function utility() {}'})
    assert not intel.api_endpoints
    assert not intel.technologies
    assert ProjectType.FRONTEND not in intel.project_types
    assert ProjectType.BACKEND_API not in intel.project_types
    assert ProjectType.MACHINE_LEARNING not in intel.project_types


def test_flask_all_declared_methods_are_retained():
    intel = analyze({'main.py': 'from flask import Flask\napp = Flask(__name__)\n@app.route("/items", methods=["GET", "POST"])\ndef items(): return {}'})
    assert {e.method for e in intel.api_endpoints} == {'GET', 'POST'}


def test_deployment_presence_and_intent_not_platform_mentions():
    intel = analyze({'render.yaml': 'services:\n  - type: web\n', 'README.md': '# Architecture\nRender is a vendor.\nWe will deploy to Vercel.\n'})
    assert any('Render configuration present: render.yaml' in d for d in intel.observed_deployment)
    assert not any('Render' in d for d in intel.planned_deployment)
    assert any('Vercel' in d for d in intel.planned_deployment)
