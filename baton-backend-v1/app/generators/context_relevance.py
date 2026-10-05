"""Select relevance from canonical relationships; never establish new facts."""
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
import re

from app.intelligence.models import DirectoryRole
from app.schemas.context import ContextOptions, ContextType


@dataclass
class ContextRelevance:
    primary_files: list[str] = field(default_factory=list)
    dependency_files: list[str] = field(default_factory=list)
    selected_files: list[str] = field(default_factory=list)
    cross_boundary_files: list[str] = field(default_factory=list)
    editable_files: list[str] = field(default_factory=list)
    protected_files: list[str] = field(default_factory=list)
    reasons: dict[str, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    ownership_provided: bool = False
    status: str = 'UNKNOWN'


def in_scope(path, scope):
    """Match repository-relative files, directory prefixes or glob scopes."""
    scope = scope.replace('\\', '/').strip('/')
    if scope in {'.', '**', '*'}:
        return True
    if not scope:
        return False
    if any(c in scope for c in '*?['):
        return fnmatchcase(path, scope)
    return path == scope or path.startswith(scope + '/')


def scopes_match(path, scopes):
    return any(in_scope(path, scope) for scope in scopes)


def classification_for(path, intelligence):
    matches = [d for d in intelligence.directory_classifications
               if (d.path == '.' and '/' not in path) or (d.path != '.' and in_scope(path, d.path))]
    return max(matches, key=lambda d: len(d.path), default=None)


def effective_role(directory, intelligence):
    if directory is None:
        return None
    role = directory.role.value
    if directory.user_override and directory.override_source == 'USER':
        role = directory.user_override
    for override in intelligence.user_overrides:
        if override.target == directory.path and override.field == 'role' and override.source == 'USER':
            role = override.value
    return role


def role_categories(role):
    value = (role or '').lower()
    categories = set()
    mapping = [
        (r'front[ -]?end|\bui\b|web designer', {DirectoryRole.FRONTEND.value}),
        (r'back[ -]?end|api|server', {DirectoryRole.BACKEND.value}),
        (r'full[ -]?stack', {DirectoryRole.FRONTEND.value, DirectoryRole.BACKEND.value}),
        (r'\bml\b|machine learning|data scien|research', {DirectoryRole.ML_PIPELINE.value, DirectoryRole.DATA_PROCESSING.value}),
        (r'data engineer|etl|pipeline', {DirectoryRole.DATA_PROCESSING.value, DirectoryRole.ML_PIPELINE.value}),
        (r'devops|infrastructure|deploy|sre', {DirectoryRole.INFRASTRUCTURE.value, DirectoryRole.CONFIGURATION.value}),
        (r'\bqa\b|test|quality', {DirectoryRole.TESTS.value}),
        (r'cli|automation|script', {DirectoryRole.CLI.value}),
        (r'embedded|firmware|hardware', {DirectoryRole.EMBEDDED.value}),
        (r'library|sdk|domain', {DirectoryRole.SHARED.value}),
        (r'technical writer|documentation', {DirectoryRole.DOCUMENTATION.value}),
    ]
    for pattern, roles in mapping:
        if re.search(pattern, value):
            categories.update(roles)
    return categories


def select(intelligence, options: ContextOptions):
    selection = ContextRelevance()
    files = {f['path'] for f in intelligence.file_tree if f.get('type') == 'blob'}
    member = options.member
    ownership = member.ownership if member else []
    protected = member.do_not_touch if member else []
    selection.ownership_provided = bool(ownership)
    primary = set()

    def add(path, reason, target=primary):
        if path in files:
            target.add(path)
            selection.reasons.setdefault(path, [])
            if reason not in selection.reasons[path]:
                selection.reasons[path].append(reason)

    if options.context_type == ContextType.PROJECT:
        for path in files:
            add(path, 'Project-wide inventory')
    else:
        for path in files:
            if scopes_match(path, ownership):
                add(path, 'USER-provided ownership scope')
        categories = role_categories(member.role if member else None)
        for path in files:
            directory = classification_for(path, intelligence)
            if effective_role(directory, intelligence) in categories:
                add(path, 'Role relevance from canonical directory classification (INFERRED relevance)')
        if member:
            for scope in ownership + member.team_scope:
                if not any(in_scope(path, scope) for path in files):
                    selection.warnings.append(f'USER scope has no matching inventory path: {scope}')
            for path in files:
                if scopes_match(path, member.team_scope):
                    add(path, 'USER-provided team scope (not ownership)')
        if options.task:
            stop = {'that', 'this', 'with', 'from', 'into', 'must', 'should', 'implement', 'create', 'update', 'please', 'work', 'task', 'feature'}
            words = set(re.findall(r'[a-z][a-z0-9_-]{2,}', options.task.lower())) - stop
            labels = {p.path: ' '.join([p.path, *p.semantic_roles, *(s['name'] for s in p.symbols)]) for p in intelligence.parsed_files}
            for endpoint in intelligence.api_endpoints:
                labels[endpoint.source_file] = labels.get(endpoint.source_file, endpoint.source_file) + ' ' + endpoint.route + ' ' + (endpoint.handler or '')
            for path, label in labels.items():
                tokens = set(re.findall(r'[a-z][a-z0-9_-]{2,}', re.sub(r'([a-z])([A-Z])', r'\1 \2', label).lower()))
                if words & tokens:
                    add(path, 'Task text matches canonical path/symbol/stage/API labels (INFERRED relevance)')
            for requirement in intelligence.requirements:
                if words & set(re.findall(r'[a-z][a-z0-9_-]{2,}', requirement.intent.lower())):
                    for path in files:
                        if any(path in evidence for evidence in requirement.observed_code):
                            add(path, f'Task matches documented requirement {requirement.id} (INFERRED relevance)')
        if not primary:
            selection.warnings.append('Relevance could not be established from the supplied role/task/scopes. Showing the full canonical project rather than hiding unknown dependencies.')
            for path in files:
                add(path, 'UNKNOWN relevance; project-wide fallback')
            selection.status = 'UNKNOWN'
        else:
            selection.status = 'INFERRED'

    if options.context_type == ContextType.PROJECT:
        selection.status = 'PROJECT_WIDE'
    dependencies = set(primary)
    # Closure includes both ends of shared imports, APIs and data relationships.
    # These edges come from Part 1, not source parsing or independently matching APIs.
    graph = {}
    for source, targets in intelligence.resolved_dependencies.items():
        for target in targets:
            graph.setdefault(source, set()).add(target)
            graph.setdefault(target, set()).add(source)
    for endpoint in intelligence.api_endpoints:
        for caller in endpoint.callers:
            graph.setdefault(caller, set()).add(endpoint.source_file)
            graph.setdefault(endpoint.source_file, set()).add(caller)
        for model in intelligence.data_models:
            if model['name'] in endpoint.related_types:
                path = model['source_file']
                graph.setdefault(endpoint.source_file, set()).add(path)
                graph.setdefault(path, set()).add(endpoint.source_file)
    for data in intelligence.data_sources:
        for consumer in data.consumers:
            graph.setdefault(consumer, set()).add(data.path)
            graph.setdefault(data.path, set()).add(consumer)
    pending = list(primary)
    while pending:
        source = pending.pop()
        for target in sorted(graph.get(source, set())):
            if target in files and target not in dependencies:
                add(target, f'Canonical relationship with {source}', dependencies)
                pending.append(target)
    selection.primary_files = sorted(primary)
    selection.dependency_files = sorted(dependencies - primary)
    selection.selected_files = sorted(dependencies)
    selection.protected_files = sorted(p for p in dependencies if scopes_match(p, protected))
    selection.editable_files = sorted(p for p in dependencies if scopes_match(p, ownership) and not scopes_match(p, protected))
    selection.cross_boundary_files = sorted(p for p in dependencies if ownership and not scopes_match(p, ownership))
    if not ownership:
        selection.warnings.append('Ownership configuration was not provided. Relevance does not establish modification ownership.')
    overlaps = sorted(p for p in files if scopes_match(p, ownership) and scopes_match(p, protected))
    if overlaps:
        selection.warnings.append('USER ownership and do-not-touch scopes overlap; do-not-touch takes precedence for modification: ' + ', '.join(overlaps))
    omitted = set(intelligence.completeness.omitted_paths)
    for path in sorted(dependencies & omitted):
        selection.warnings.append(f'Relevant file content was omitted from the snapshot: {path}')
    return selection
