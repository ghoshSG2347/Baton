"""Conservative comparisons: candidate code is not proof of product behavior."""
import re
from app.intelligence.models import ImplementationStatus, Confidence, IntelligenceConflict
from app.analyzers.code_structure_analyzer import code_contents, analyze
from app.analyzers.dependency_analyzer import _normalize_path


def reconcile(requirements, contents, api_endpoints, api_calls, directory_classifications, parsed_files=None):
    parsed = parsed_files if parsed_files is not None else analyze(code_contents(contents))
    symbols = [(item.path, symbol['name']) for item in parsed for symbol in item.symbols]
    observed, missing = [], []
    for req in requirements:
        # Match explicit identifiers, not generic domain vocabulary or comments.
        identifiers = re.findall(r'`([A-Za-z_][\w]*)`', req.intent)
        terms = set(re.findall(r'[a-z]{4,}', req.intent.lower())) - {'must', 'should', 'users', 'user', 'system', 'provide', 'support', 'feature', 'with', 'will', 'have', 'that', 'this', 'from', 'using', 'allow'}
        candidates = []
        for path, name in symbols:
            words = set(re.findall(r'[a-z]{4,}', re.sub(r'([a-z])([A-Z])', r'\1 \2', name).lower()))
            if name in identifiers or terms & words:
                candidates.append(f'{path}: {name}')
        routes = re.findall(r'(?:GET|POST|PUT|PATCH|DELETE)\s+(/[^\s`]+)', req.intent, re.I)
        for route in routes:
            candidates.extend(f'{e.source_file}: {e.method} {e.route}' for e in api_endpoints if _normalize_path(e.route) == _normalize_path(route))
        req.observed_code = sorted(set(candidates))
        req.confidence = Confidence.LOW
        if candidates:
            req.status = ImplementationStatus.PARTIALLY_IMPLEMENTED
            req.missing_pieces = ['Candidate implementation detected; behavior and completeness are not verified.']
            req.evidence.extend(req.observed_code)
        else:
            req.status = ImplementationStatus.NOT_DETECTED
            req.missing_pieces = ['No matching implementation detected in collected source; absence is not proof of nonimplementation.']
            missing.append(req.intent)
        # A literal endpoint-exposure requirement has a mechanically verifiable
        # scope. This certifies only its declaration, never behavior behind it.
        endpoint_requirement = re.fullmatch(r'Expose\s+(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s`]+)\.?', req.intent.strip(), re.I)
        if endpoint_requirement:
            method, route = endpoint_requirement.groups()
            route = route.rstrip('.')
            matched = [e for e in api_endpoints if e.method == method.upper() and _normalize_path(e.route) == _normalize_path(route)]
            if matched:
                req.status = ImplementationStatus.IMPLEMENTED
                req.confidence = Confidence.HIGH
                req.observed_code = [f'{e.source_file}: {e.method} {e.route}' for e in matched]
                req.missing_pieces = []
                req.evidence.extend(req.observed_code)
                if req.intent in missing:
                    missing.remove(req.intent)
        # Only observed symbols/endpoints belong in observed_features.
        observed.extend(req.observed_code)
    return requirements, [], sorted(set(observed)), missing


def detect_doc_vs_code_conflicts(doc_sources, contents, api_endpoints, directory_classifications):
    conflicts = []
    observed = code_contents(contents)
    all_code = '\n'.join(observed.values())
    technologies = {
        'React': r"from ['\"]react['\"]|import React",
        'FastAPI': r'from fastapi import|import fastapi',
        'Flask': r'from flask import|import flask',
        'Django': r'from django|import django',
        'PostgreSQL': r'postgres|psycopg',
        'SQLite': r'sqlite',
    }
    for doc in doc_sources:
        text = contents.get(doc.path, '')
        # Explicit present-tense claims only; future intent is not a conflict.
        for line in text.splitlines():
            if re.search(r'planned|will|should|must|future|intend', line, re.I):
                continue
            for name, pattern in technologies.items():
                if re.search(rf'(?:uses?|built with|implemented with)\s+{name}\b', line, re.I) and observed and not re.search(pattern, all_code, re.I):
                    conflicts.append(IntelligenceConflict('Documented technology not detected', doc.path, line.strip(), 'Collected source', f'{name} not detected; analysis may be incomplete'))
            for method, route in re.findall(r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s`]+)', line, re.I):
                route = route.rstrip('.,;')
                if doc.role in {'PRD', 'REQUIREMENTS', 'SPECIFICATION'} and re.search(r'\b(?:expose|implement|create|add)\b', line, re.I):
                    continue  # an intended endpoint is not a claim it exists
                if api_endpoints and not any(e.method == method.upper() and _normalize_path(e.route) == _normalize_path(route) for e in api_endpoints):
                    conflicts.append(IntelligenceConflict('Documented API differs from observed routes', doc.path, f'{method.upper()} {route}', ', '.join(sorted({e.source_file for e in api_endpoints})), 'No matching collected route'))
    # Detect explicitly opposite instructions without attempting semantic resolution.
    instructions = []
    for doc in doc_sources:
        if doc.role not in {'AGENTS', 'RULES', 'CONTRIBUTING'}: continue
        for line in contents.get(doc.path, '').splitlines():
            match = re.search(r'\b(?:must|always|never|must not)\s+(.+)', line, re.I)
            if match:
                negative = bool(re.search(r'never|must not', match[0], re.I))
                action = re.sub(r'^(?:not\s+)', '', match[1].lower()).strip(' .')
                for other_path, other_action, other_negative in instructions:
                    if action == other_action and negative != other_negative:
                        conflicts.append(IntelligenceConflict('Opposing repository instructions', other_path, other_action, doc.path, line.strip()))
                instructions.append((doc.path, action, negative))
    return conflicts
