"""Question routing and bounded retrieval over Part 2 records, without I/O or analysis."""
import json
import re
from collections import Counter
from app.core.exceptions import BatonError


INTENTS = [
    ('BRANCH_COMPARISON', r'compare|difference.*between|what changed between', (8, 11, 6, 7, 13, 18)),
    ('IMPLEMENTATION_GAP', r'incomplete|unfinished|missing|gap|not implemented', (6, 7, 18)),
    ('NEXT_TASK', r'work on|do next|next task|prioriti', (6, 7, 16, 17, 18)),
    ('ROLE_GUIDANCE', r'developer do|my duties|my role|ownership|handoff', (6, 11, 16, 17)),
    ('FILE_EXPLANATION', r'\bfile\b|\bfunction\b|\bsource\b|\.(tsx?|jsx?|py|rs|go|java|cpp|c|ipynb)\b', (9, 8, 11)),
    ('API_ANALYSIS', r'endpoint|\bapi\b|contract|\btype\b|caller', (11, 8, 9)),
    ('DEPENDENCY_ANALYSIS', r'dependenc|package|import|breaks if', (13, 8, 11)),
    ('DATA_FLOW', r'data flow|pipeline|training|train|evaluat|dataset', (12, 8, 9)),
    ('CONFLICT_ANALYSIS', r'conflict|contradiction|inconsisten|healthy|health', (18, 14, 5, 6)),
    ('INTEGRATION_ANALYSIS', r'integration|connect.*component', (11, 8, 13, 18)),
    ('DEPLOYMENT', r'deploy|hosting|operational', (15, 14)),
    ('ONBOARDING', r'joined|onboard|teach me|reading order', (3, 4, 8, 9, 10, 11, 14, 15)),
    ('ARCHITECTURE', r'architecture|frontend|backend|component', (8, 9, 10, 11)),
    ('STATUS', r'status|complete|completed|implemented|progress', (7, 6, 18)),
    ('DOCUMENTATION', r'document|readme|prd|specification', (4, 5, 6)),
    ('PROJECT_OVERVIEW', r'what is this|explain.*project|overview|summary', (3, 4, 7, 8)),
]
STOP = set('what which why how does do is are the this that it its me my for from with about explain give more context repository project please should could'.split())
CRITICAL_SECTIONS = {16, 18, 20}


def classify(question):
    value = question.lower()
    for name, pattern, sections in INTENTS:
        if re.search(pattern, value):
            return name, sections
    return 'GENERAL_REPOSITORY_QUERY', (3, 4, 8, 9, 11)


def artifact_command(question):
    value = question.lower()
    if not re.search(r'\b(create|generate|prepare|write|give me|make|produce)\b|^/(prd|design|tasks|prompt|handoff|context)', value):
        return None
    for pattern, kind in [(r'\bprd\b', 'prd'), (r'technical design|/design', 'technical_design'),
                          (r'task breakdown|\btasks\b|/tasks', 'tasks'), (r'handoff', 'handoff'),
                          (r'prompt', 'prompt'), (r'implementation plan|roadmap', 'implementation_plan'),
                          (r'context', 'context')]:
        if re.search(pattern, value):
            return kind
    return None


def words(value):
    return set(re.findall(r'[a-z][a-z0-9_-]{2,}', re.sub(r'([a-z])([A-Z])', r'\1 \2', value).lower())) - STOP


def record_index(context):
    return {record['id']: {**record, 'section': section['title'], 'section_number': section['number']}
            for section in context['sections'] for record in section['records']}


def retrieve(context, question, conversation, byte_budget):
    """Rank existing records; retain boundary/rule/conflict/unknown blocks whole.

    Stable IDs refer to the existing Context Model. No facts or graph edges are
    synthesized here. Follow-ups carry evidence references, not repeated answers.
    """
    index = record_index(context)
    intent, sections = classify(question)
    turns = conversation['turns'][-4:]
    previous_ids = {identifier for turn in turns[-1:] for identifier in turn['answer'].get('evidence_ids', [])}
    query = words(question)
    followup = bool(turns and (len(query) <= 4 or re.search(r'\b(it|that|this|those|more|too|now)\b', question.lower())))
    if followup:
        query |= words(turns[-1]['question'])
    duties = words(' '.join(context['member'].get('responsibilities', [])))
    owned = set(context['relevance']['editable_files'])
    path_hits = {path for record in index.values() for path in record['source_paths'] if path.lower() in question.lower()}
    score = lambda record: (len(query & words(record['text'])) * 4 +
                             (6 if record['section_number'] in sections else 0) +
                             (20 if path_hits & set(record['source_paths']) else 0) +
                             (8 if intent in {'ROLE_GUIDANCE', 'NEXT_TASK'} and owned & set(record['source_paths']) else 0) +
                             (len(duties & words(record['text'])) * 2 if intent in {'ROLE_GUIDANCE', 'NEXT_TASK'} else 0) +
                             (10 if followup and record['id'] in previous_ids else 0))
    mandatory = [r for r in index.values() if r['section_number'] in CRITICAL_SECTIONS or
                 (r['section_number'] == 19 and ':evidence:' not in r['id'])]
    packet = {'identity': context['identity'], 'completeness': context['completeness'],
              'member': context['member'], 'task': context['task'], 'intent': intent,
              'constraints': context['task'].get('constraints', []),
              'editable_files': context['relevance']['editable_files'],
              'protected_files': context['relevance']['protected_files'],
              'conversation_state': [{'question': turn['question'][:500],
                                      'evidence_ids': turn['answer'].get('evidence_ids', []),
                                      'intent': turn['answer'].get('intent')} for turn in turns],
              'previous_user_questions': [turn['question'][:500] for turn in turns],
              'records': mandatory, 'question': question,
              'partial': True, 'retrieval_notice': 'Relevant slice only; omitted evidence is not evidence of absence.',
              'omission_counts': dict(Counter(item['category'] for item in context['omission_manifest']))}
    size = lambda: len(json.dumps(packet, ensure_ascii=False).encode())
    if size() > byte_budget:
        raise BatonError('Critical rules, constraints and unknowns exceed the AI input budget. Narrow the supplied scope; no critical constraint was silently removed.', 413)
    chosen = {r['id'] for r in mandatory}
    for record in sorted(index.values(), key=lambda r: (-score(r), r['id'])):
        if record['id'] in chosen or score(record) <= 0 or len(chosen) >= 32:
            continue
        packet['records'].append(record)
        if size() > byte_budget - 300:
            packet['records'].pop()
            continue
        chosen.add(record['id'])
    packet['retrieval'] = {'records_available': len(index), 'records_retrieved': len(chosen),
                           'records_omitted': len(index) - len(chosen), 'budget_bytes': byte_budget}
    packet['partial'] = len(chosen) < len(index) or bool(context['omission_manifest'])
    packet['retrieval']['input_bytes'] = size()
    if size() > byte_budget:
        raise BatonError('The bounded AI request exceeds its input budget.', 413)
    return packet, {r['id']: r for r in packet['records']}
