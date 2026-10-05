"""Static structure extraction. Parsing never imports or executes source."""
import ast
import json
import re
import tomllib
import io
import tokenize
from pathlib import PurePosixPath
from app.intelligence.models import FileStructure

CODE_EXTENSIONS = {'.py', '.pyi', '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.java', '.kt', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.dart', '.swift', '.ino', '.sh', '.ps1', '.vue', '.svelte', '.r', '.jl', '.gd', '.sql'}


def code_contents(contents):
    return {p: t for p, t in contents.items() if PurePosixPath(p).suffix.lower() in CODE_EXTENSIONS}


def implementation_contents(contents):
    """Ignore comments and Python docstrings while preserving source lines."""
    result = {}
    for path, text in code_contents(contents).items():
        if path.endswith(('.py', '.pyi')):
            offsets = [0]
            for line in text.splitlines(keepends=True):
                offsets.append(offsets[-1] + len(line))
            spans = []
            try:
                for token in tokenize.generate_tokens(io.StringIO(text).readline):
                    if token.type == tokenize.COMMENT:
                        spans.append((offsets[token.start[0] - 1] + token.start[1], offsets[token.end[0] - 1] + token.end[1]))
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        # AST columns are UTF-8 byte offsets; convert to characters.
                        lines = text.splitlines()
                        start = offsets[node.lineno - 1] + len(lines[node.lineno - 1].encode()[:node.col_offset].decode())
                        end = offsets[node.end_lineno - 1] + len(lines[node.end_lineno - 1].encode()[:node.end_col_offset].decode())
                        spans.append((start, end))
            except (SyntaxError, tokenize.TokenError, IndentationError, ValueError, RecursionError):
                pass
            for start, end in sorted(spans, reverse=True):
                text = text[:start] + re.sub(r'[^\n]', ' ', text[start:end]) + text[end:]
        elif PurePosixPath(path).suffix.lower() in {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.java', '.kt', '.c', '.cpp', '.h', '.hpp', '.cs', '.rs', '.go'}:
            # Preserve quoted literals, remove only unquoted comment spans.
            pattern = r'''"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)'''
            text = re.sub(pattern, lambda m: re.sub(r'[^\n]', ' ', m[0]) if m.group('comment') else m[0], text)
        result[path] = text
    return result


def semantic_roles(text):
    patterns = {
        'model_definition': r'\b(?:nn\.Module|torch\.nn|keras\.Model|Sequential)\b',
        'training': r'\b(?:model\.fit|model\.train|trainer\.train|loss\.backward|optimizer\.step)\s*\(',
        'preprocessing': r'\b(?:fit_transform|dropna|fillna|StandardScaler|train_test_split)\b',
        'evaluation': r'\b(?:accuracy_score|f1_score|confusion_matrix|classification_report|model\.eval)\b',
        'inference': r'\b(?:predict|predict_proba|inference_mode)\s*\(',
        'dataset_loading': r'\b(?:read_csv|read_parquet|load_dataset|DataLoader|np\.load)\b',
    }
    return [role for role, pattern in patterns.items() if re.search(pattern, text)]


def analyze(contents):
    result = []
    for path, text in code_contents(contents).items():
        item = FileStructure(path=path, parse_status='PATTERN_EXTRACTED', semantic_roles=semantic_roles(text))
        if path.endswith(('.py', '.pyi')):
            try:
                tree = ast.parse(text)
                item.parse_status = 'PARSED'
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        item.symbols.append({'name': node.name, 'kind': type(node).__name__, 'line': node.lineno, 'decorators': [ast.unparse(d) for d in node.decorator_list], 'parameters': [a.arg for a in node.args.args] if hasattr(node, 'args') else [], 'returns': ast.unparse(node.returns) if getattr(node, 'returns', None) else None})
                        if isinstance(node, ast.ClassDef):
                            item.symbols[-1]['bases'] = [ast.unparse(base) for base in node.bases]
                            item.symbols[-1]['fields'] = [{'name': field.target.id, 'annotation': ast.unparse(field.annotation)} for field in node.body if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name)]
                    elif isinstance(node, ast.Import):
                        item.imports.extend(a.name for a in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        item.imports.append('.' * node.level + (node.module or ''))
                if re.search(r'''if __name__\s*==\s*['"]__main__['"]''', text):
                    item.entrypoints.append('__main__')
            except (SyntaxError, ValueError, RecursionError, MemoryError):
                item.parse_status = 'PARSE_FAILED'
        else:
            for m in re.finditer(r'\b(class|interface|type|function|fn|struct|enum)\s+(\w+)', text):
                item.symbols.append({'kind': m[1], 'name': m[2], 'line': text.count('\n', 0, m.start()) + 1})
                # A missing canonical contract field needed by Part 2. Keep
                # simple TS property declarations, never reinterpret source in
                # a context view. Nested/computed/method shapes remain unknown.
                if path.endswith(('.ts', '.tsx')) and m[1] in {'interface', 'type'}:
                    body = re.match(r'\s*(?:=\s*)?\{([^{}]*)\}', text[m.end():])
                    if body:
                        item.symbols[-1]['fields'] = [
                            {'name': prop[1], 'annotation': prop[3].strip(), 'optional': bool(prop[2])}
                            for prop in re.finditer(r'(?:^|[;\n])\s*(?:readonly\s+)?([\w$]+)(\?)?\s*:\s*([^;\n{}]+)', body[1])
                        ]
                        item.symbols[-1]['field_extraction'] = 'flat_declared_properties_only'
            for m in re.finditer(r'\b(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>', text):
                item.symbols.append({'kind': 'function', 'name': m[1], 'line': text.count('\n', 0, m.start()) + 1})
            for m in re.finditer(r'''(?:import|from|require\()\s*['"]([^'"]+)['"]''', text):
                item.imports.append(m[1])
            if re.search(r'\bmain\s*\(', text):
                item.entrypoints.append('main')
            if path.endswith(('.java', '.kt')):
                package = re.search(r'(?m)^\s*package\s+([\w.]+)', text)
                if package:
                    item.imports.append('package:' + package[1])
                for m in re.finditer(r'\b(?:public|protected|private)\s+(?:static\s+)?\w+(?:<[^>]+>)?\s+(\w+)\s*\(([^)]*)\)', text):
                    item.symbols.append({'kind': 'method', 'name': m[1], 'parameters': m[2], 'line': text.count('\n', 0, m.start()) + 1})
            if path.endswith('.sql'):
                for m in re.finditer(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.]+)\s*\(([^;]+)\)', text, re.I):
                    item.symbols.append({'kind': 'table', 'name': m[1], 'fields': m[2].strip(), 'line': text.count('\n', 0, m.start()) + 1})
        result.append(item)
    for path, text in contents.items():
        if not path.endswith('.ipynb'):
            continue
        item = FileStructure(path=path, parse_status='PARSE_FAILED')
        try:
            notebook = json.loads(text)
            source = '\n'.join(''.join(c.get('source', [])) for c in notebook.get('cells', []) if c.get('cell_type') == 'code')
            item.semantic_roles = semantic_roles(source)
            item.parse_status = 'NOTEBOOK_CELLS_PARSED'
            item.imports = re.findall(r'(?m)^\s*(?:import|from)\s+([\w.]+)', source)
        except (ValueError, TypeError, AttributeError):
            pass
        result.append(item)
    return result


def manifests(contents):
    dependencies, scripts = [], {}
    for path, text in contents.items():
        name = PurePosixPath(path).name
        try:
            if name == 'package.json':
                data = json.loads(text)
                scripts[path] = data.get('scripts', {})
                for group in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies'):
                    for package, version in data.get(group, {}).items():
                        dependencies.append({'name': package, 'version': version, 'source_file': path, 'group': group})
            elif name in {'pyproject.toml', 'Cargo.toml'}:
                data = tomllib.loads(text)
                if name == 'pyproject.toml':
                    for dep in data.get('project', {}).get('dependencies', []):
                        dependencies.append({'name': dep, 'source_file': path, 'group': 'dependencies'})
                else:
                    for group in ('dependencies', 'dev-dependencies', 'build-dependencies'):
                        for package, version in data.get(group, {}).items():
                            dependencies.append({'name': package, 'version': version, 'source_file': path, 'group': group})
            elif re.fullmatch(r'requirements(?:[-_.]\w+)?\.txt', name):
                for line in text.splitlines():
                    match = re.match(r'([\w.-]+)(.*)', line.strip())
                    if match:
                        dependencies.append({'name': match[1], 'version': match[2].split('#')[0].strip(), 'source_file': path, 'group': 'dependencies'})
            elif name == 'go.mod':
                for match in re.finditer(r'(?m)^\s*(?:require\s+)?([\w.-]+/[\w./-]+)\s+(v\S+)', text):
                    dependencies.append({'name': match[1], 'version': match[2], 'source_file': path, 'group': 'dependencies'})
        except (ValueError, TypeError, AttributeError):
            continue
    return dependencies, scripts
