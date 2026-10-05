"""Part 3 consumers: shared context, validated evidence, artifacts and branch views."""
import hmac
import json
import secrets
from app.core.config import get_settings
from app.core.exceptions import BatonError
from app.core.secrets import secret_values
from app.generators.context_builder import scrub
from app.generators.context_relevance import scopes_match
from app.intelligence.safety import sanitize
from app.schemas.context import ContextRequest
from app.schemas.workspace import EvidenceSelection
from app.services.ai_provider import GeminiProvider
from app.services.context_service import ContextService
from app.services.conversations import CONVERSATIONS
from app.services.workspace_retrieval import retrieve, classify, artifact_command
from app.services.workspace_artifacts import render_artifact
from app.services.context_snapshot import ContextSnapshotService
from app.services.github_service import GitHubService
import logging
import re
import time


_BINDING_KEY = secrets.token_bytes(32)
METRICS = logging.getLogger('baton.workspace.metrics')



class WorkspaceService:
    def __init__(self, contexts=None, provider=None, conversations=None):
        self.contexts = contexts or ContextService()
        self.provider = provider or GeminiProvider()
        self.conversations = conversations or CONVERSATIONS

    async def context(self, req, token=None):
        # Reuse Part 2 once, with its existing authorization and no-scan policy.
        fields = {key: value for key, value in req.model_dump().items() if key in ContextRequest.model_fields}
        fields['include_markdown'] = True
        fields['max_bytes'] = min(req.max_bytes or get_settings().ai_context_bytes, get_settings().ai_context_bytes)
        if req.continue_snapshot:
            if not req.commit:
                raise BatonError('Choose an analyzed commit before continuing with an older snapshot.', 422)
            data = await self.contexts.create(ContextRequest(**fields), token, allow_snapshot=True)
        else:
            data = await self.contexts.create(ContextRequest(**fields), token)
        if not data['context']['usable']:
            raise BatonError('The context budget cannot retain a usable grounded briefing.', 413)
        return data

    async def inspect(self, req, token=None):
        try:
            data = await self.context(req, token)
        except BatonError as exc:
            if exc.status_code != 409:
                raise
            snapshots = self.contexts.snapshots or ContextSnapshotService(token)
            branch = req.branch or (await snapshots.github.repository(req.owner, req.repo)).get('default_branch', 'HEAD')
            state = await snapshots.github.commit(req.owner, req.repo, branch)
            head = state.get('sha')
            matches = [m for m in snapshots.store.metadata() if
                       (m['owner'].lower(), m['repo'].lower(), m['branch'], m['folder']) ==
                       (req.owner.lower(), req.repo.lower(), branch, req.folder.strip('/'))]
            latest = matches[-1] if matches else None
            METRICS.info('snapshot_miss stored_snapshot=%s', bool(latest))
            return scrub({'available': False, 'identity': {'repository': f'{req.owner}/{req.repo}',
                          'branch': branch, 'commit': latest['commit'] if latest else '',
                          'current_head': head, 'snapshot_status': 'STALE' if latest else 'UNAVAILABLE',
                          'analysis_timestamp': latest['generated'] if latest else '', 'project_root': req.folder},
                          'warnings': ['Repository changed since the current intelligence snapshot.' if latest else
                                       'The selected branch does not currently have a valid repository intelligence snapshot.'],
                          'markdown': '', 'sections': [], 'completeness': {'status': 'UNKNOWN'},
                          'relevance': {'editable_files': [], 'protected_files': [], 'cross_boundary_files': [], 'warnings': []},
                          'omission_manifest': [], 'provider': {'name': 'gemini', 'configured': bool(get_settings().gemini_api_key.get_secret_value() and get_settings().gemini_model)}}, secret_values(token))
        METRICS.info('snapshot_hit')
        return scrub({**data['context'], 'markdown': data['markdown'],
                      'available': True,
                      'estimated_tokens': data['estimated_tokens'],
                      'provider': {'name': 'gemini', 'configured': bool(get_settings().gemini_api_key.get_secret_value() and get_settings().gemini_model)}}, secret_values(token))

    async def chat(self, req, token=None):
        started = time.monotonic()
        # Read project truth with the same Part 2 projection. Role/ownership remain
        # supplied boundaries and ranking signals, not a restriction on read access.
        data = await self.context(req.model_copy(update={'context_type': 'project'}), token)
        context = data['context']
        question = sanitize(req.message.strip(), secret_values(token))
        if not question or question == '[REDACTED]':
            raise BatonError('Enter a repository question without credentials.', 422)
        binding_data = {'identity': context['identity'], 'member': context['member'],
                        'task': context['task'], 'requested_context_type': req.context_type,
                        'credential': token or get_settings().github_token}
        # Generated time changes each call; commit/context parameters bind scope.
        binding_data['identity'] = {k: v for k, v in binding_data['identity'].items() if k != 'generated_at'}
        binding = hmac.new(_BINDING_KEY, json.dumps(binding_data, sort_keys=True).encode(), 'sha256').hexdigest()
        conversation = self.conversations.load(req.conversation_id, binding)
        packet, records = retrieve(context, question, conversation, get_settings().ai_input_bytes)
        packet['user_overrides'] = [turn['answer']['user_override'] for turn in conversation['turns']
                                    if turn['answer'].get('user_override')]
        mode = 'general' if re.search(r'general (concept|explanation)|conceptually|in general|what is .+ in general', question.lower()) else 'recommendation' if re.search(r'recommend|should|improve|work on|do next|next task', question.lower()) else 'repository'
        packet['mode'] = mode
        command = artifact_command(question)
        artifact = None
        comparison = None
        override_match = re.search(r'(?:folder\s+|directory\s+)([\w./-]+)\s+(?:is\s+)?actually\s+(.+)', question, re.I)
        user_override = {'target': override_match.group(1), 'value': override_match.group(2), 'source': 'USER_PROVIDED'} if override_match else None
        secret_request = bool(re.search(r'(show|reveal|print|expose|give).*(secret|api.?key|token|credential|cookie|\.env)', question.lower()))
        branch_names = re.findall(r'\b(?:branch\s+)([\w./-]+)', question, flags=re.I)
        branch_names += re.findall(r'what does\s+([\w.-]+/[\w./-]+)\s+(?:currently\s+)?contain', question, flags=re.I)
        wrong_branch = any(name != context['identity']['branch'] for name in branch_names)
        compare_match = re.search(r'(?:compare|difference(?:s)? between|changed between)\s+([\w./-]+)\s+(?:and|vs\.?|with)\s+([\w./-]+)', question, re.I)
        if secret_request:
            selection = EvidenceSelection(status='out_of_scope')
        elif user_override:
            selection = EvidenceSelection(status='unknown')
        elif compare_match:
            from app.schemas.workspace import CompareRequest
            base, other = compare_match.groups()
            comparison = await self.compare(CompareRequest(**{**req.model_dump(exclude={'message', 'conversation_id'}),
                                                               'branch': base, 'commit': req.commit if base == req.branch else None,
                                                               'continue_snapshot': req.continue_snapshot if base == req.branch else False,
                                                               'compare_branch': other}), token)
            selection = EvidenceSelection(status='unknown')
        elif wrong_branch:
            selection = EvidenceSelection(status='out_of_scope')
        elif command:
            from app.schemas.workspace import ArtifactRequest
            target = next((agent for agent in ['Anti-Gravity', 'Claude Code', 'Cursor', 'Codex'] if agent.lower() in question.lower()), 'Coding agent')
            if command == 'handoff':
                target = question
            objective = req.task or (conversation['turns'][-1]['question'] if conversation['turns'] else None)
            if command in {'technical_design', 'tasks', 'context', 'handoff'}:
                objective = question
            if command == 'prompt':
                explicit = re.search(r'prompt\s+for\s+(.+)', question, re.I)
                if explicit and explicit.group(1).lower().strip(' .') not in {'this', 'that', 'the project', 'this project'}:
                    objective = explicit.group(1)
                if not objective:
                    objective = 'Audit the supplied repository evidence and investigate only documented gaps within authorized ownership.'
            values = scrub({**req.model_dump(exclude={'message', 'conversation_id'}), 'artifact_type': command,
                            'task': objective, 'target': target}, secret_values(token))
            artifact = render_artifact(ArtifactRequest(**values), data)
            selection = EvidenceSelection(status='unknown')
        else:
            # An explicitly named file may require exact source. Retrieve one region
            # from the pinned commit; never walk trees or trigger analysis.
            source_paths = {p for f in data['analysis']['file_tree'] if f.get('type') == 'blob' for p in [f['path']]}
            requested = [p for p in source_paths if p.lower() in question.lower()]
            if classify(question)[0] == 'FILE_EXPLANATION' and requested:
                path = sorted(requested)[0]
                source = await self.source(req, path, token, data=data)
                record = {'id': 'source:' + path, 'section': 'Exact source region (OBSERVED)', 'section_number': 9,
                          'text': f'OBSERVED `{path}` lines {source["start_line"]}–{source["end_line"]} at `{context["identity"]["commit"]}`:\n\n```{source["language"]}\n{source["content"]}\n```', 'source_paths': [path]}
                # Source fits the same budget; retrieve again with this bounded record.
                expanded = {**context, 'sections': [*context['sections'], {'number': 9, 'title': record['section'], 'records': [record]}]}
                packet, records = retrieve(expanded, question, conversation, get_settings().ai_input_bytes)
                packet['mode'] = mode
            packet['retrieval']['input_bytes'] = len(json.dumps(packet, ensure_ascii=False).encode())
            if packet['retrieval']['input_bytes'] > get_settings().ai_input_bytes:
                raise BatonError('The AI input exceeds its bounded retrieval budget.', 413)
            try:
                selection = await self.provider.select(packet)
            except BatonError:
                METRICS.info('ai_failure latency_ms=%d', (time.monotonic() - started) * 1000)
                raise
        try:
            selection = EvidenceSelection.model_validate(selection)
        except ValueError:
            raise BatonError('AI returned an invalid grounded selection.', 502) from None
        ids = list(dict.fromkeys(selection.evidence_ids))
        if any(identifier not in records for identifier in ids):
            raise BatonError('AI referenced evidence outside the current context. No answer was accepted.', 502)
        if selection.status == 'grounded' and not ids:
            raise BatonError('AI did not provide evidence for its answer. No answer was accepted.', 502)
        if selection.status != 'grounded' and (ids or selection.actions):
            raise BatonError('AI returned an inconsistent evidence status.', 502)
        actions = []
        for action in selection.actions:
            if (action.evidence_id not in ids or
                    action.target_path not in context['relevance']['editable_files'] or
                    action.target_path not in records[action.evidence_id]['source_paths'] or
                    (action.kind == 'resolve_conflict' and records[action.evidence_id]['section'] != 'Conflicts, Risks and Unknowns')):
                raise BatonError('AI proposed an action outside supplied ownership or evidence. No action was accepted.', 502)
            verb = {'inspect': 'Inspect', 'verify': 'Verify the recorded declaration in', 'resolve_conflict': 'Review the recorded conflict involving'}[action.kind]
            actions.append({'kind': action.kind, 'target_path': action.target_path, 'evidence_id': action.evidence_id,
                            'text': f'{verb} {action.target_path}. This is guidance, not an executed change.'})
        excerpts = [records[identifier] for identifier in ids]
        if selection.status == 'grounded':
            answer = 'The current snapshot contains the following relevant evidence. Documented intent and static declarations do not certify runtime behavior.\n\n' + '\n\n'.join(
                f'### {record["section"]}\n\n{record["text"]}\n\nEvidence reference: `{record["id"]}`' for record in excerpts)
        elif selection.status == 'out_of_scope':
            answer = 'This question is outside the connected repository and supplied development scope. Ask about the analyzed project, its contracts, documented requirements, or your configured duties.'
        else:
            answer = "UNKNOWN: I can't determine that from the connected repository and available project context. Not detected in retained evidence is not proof of absence. Check source omissions or explicitly refresh intelligence."
        if secret_request:
            answer = "I can't expose secret credentials."
        elif user_override:
            answer = f'USER_PROVIDED / USER_OVERRIDE: `{user_override["target"]}` — {user_override["value"]}.\n\nThe override is retained in this scoped conversation alongside repository evidence. Canonical classifications are preserved; any conflicting source classification remains a separate finding.'
        elif wrong_branch and not comparison:
            answer = f'The active branch is `{context["identity"]["branch"]}`. Switch to the requested branch and load its intelligence, or explicitly compare both branches. No facts from the active branch were substituted.'
        elif artifact:
            answer = artifact['summary'] + '\n\nOpen the generated artifact to review evidence, constraints and open questions.'
        elif comparison:
            answer = f'Compared `{comparison["before"]["branch"]}` at `{comparison["before"]["commit"]}` with `{comparison["after"]["branch"]}` at `{comparison["after"]["commit"]}`. Findings retain separate branch identities; no branches were merged.'
        for reasoning in selection.reasoning:
            refs = reasoning.evidence_ids
            if reasoning.category == 'GENERAL_EXPLANATION':
                if mode != 'general' or refs:
                    raise BatonError('General explanation was not explicitly requested or was mixed with project evidence.', 502)
            elif not refs or any(ref not in ids for ref in refs):
                raise BatonError('AI reasoning did not cite selected repository evidence.', 502)
            if reasoning.category == 'RECOMMENDATION' and mode != 'recommendation':
                raise BatonError('Unrequested recommendations were rejected.', 502)
            answer += f'\n\n### {reasoning.category} — not a project fact\n\n{sanitize(reasoning.text, secret_values(token))}\n\nReferences: ' + ', '.join(f'`{ref}`' for ref in refs)
        if mode == 'recommendation':
            answer = '## CURRENT PRODUCT\n\n' + answer.replace('### RECOMMENDATION', '## POSSIBLE RECOMMENDATIONS\n\n### RECOMMENDATION')
        if context.get('warnings'):
            answer = '> STALE: ' + ' '.join(context['warnings']) + '\n\n' + answer
        response = scrub({'status': selection.status, 'answer': answer, 'citations': excerpts,
                          'artifact': artifact, 'comparison': comparison, 'intent': packet['intent'],
                          'confidence': 'LOW' if selection.reasoning else 'UNKNOWN' if not ids else 'See confidence on each cited canonical record; static evidence only.',
                          'warnings': context.get('warnings', []), 'retrieval': packet['retrieval'],
                          'actions': actions, 'identity': context['identity'],
                          'completeness': context['completeness'], 'omission_manifest': context['omission_manifest']}, secret_values(token))
        identifier = self.conversations.append(req.conversation_id, binding, conversation['revision'], question,
                                               {'status': response['status'], 'evidence_ids': ids, 'actions': actions, 'intent': packet['intent'], 'user_override': user_override})
        response['conversation_id'] = identifier
        response['revision'] = conversation['revision'] + 1
        METRICS.info('chat_complete intent=%s records=%d input_bytes=%d ai_called=%s latency_ms=%d',
                     packet['intent'], len(records), packet['retrieval']['input_bytes'], not (command or comparison or secret_request or wrong_branch), (time.monotonic() - started) * 1000)
        return response

    async def artifact(self, req, token=None):
        data = await self.context(req, token)
        context = data['context']
        safe_request = req.model_copy(update=scrub(req.model_dump(), secret_values(token)))
        return scrub(render_artifact(safe_request, data), secret_values(token))

    async def source(self, req, path, token=None, start_line=1, data=None):
        data = data or await self.context(req, token)
        inventory = {f['path'] for f in data['analysis']['file_tree'] if f.get('type') == 'blob'}
        if path not in inventory or '..' in path.split('/') or path.startswith('/'):
            raise BatonError('Source path is outside the selected snapshot inventory.', 422)
        if re.search(r'(^|/)(\.env(?:\..*)?|credentials|secrets?|id_rsa|id_ed25519)(/|$)|\.(pem|key|p12|pfx)$', path, re.I):
            raise BatonError("I can't expose secret credentials.", 403)
        start_line = max(1, min(start_line, 100000))
        result = await GitHubService(token).file(req.owner, req.repo, data['context']['identity']['commit'], path)
        lines = sanitize(result['content'], secret_values(token)).splitlines()
        region, size = [], 0
        for line in lines[start_line - 1:start_line + 79]:
            if size + len(line.encode()) > 6000:
                break
            region.append(line)
            size += len(line.encode()) + 1
        return {'path': path, 'content': '\n'.join(region), 'language': result['language'],
                'start_line': start_line, 'end_line': start_line + len(region) - 1,
                'partial': start_line > 1 or start_line - 1 + len(region) < len(lines),
                'identity': data['context']['identity']}

    async def compare(self, req, token=None):
        before = await self.context(req, token)
        other = req.model_copy(update={'branch': req.compare_branch, 'commit': req.compare_commit, 'continue_snapshot': False})
        after = await self.context(other, token)
        left = {f['path']: f.get('sha') for f in before['analysis']['file_tree'] if f.get('type') == 'blob'}
        right = {f['path']: f.get('sha') for f in after['analysis']['file_tree'] if f.get('type') == 'blob'}
        common = set(left) & set(right)
        endpoints = lambda data: {(e['source_file'], e['method'], e['route']):
                                 {k: e.get(k) for k in ('request_shape', 'response_shape', 'related_types')}
                                 for e in data['analysis']['canonical_api']['endpoints']}
        old_api, new_api = endpoints(before), endpoints(after)
        api_changes = [{'source_file': key[0], 'method': key[1], 'route': key[2],
                        'before': old_api.get(key), 'after': new_api.get(key)}
                       for key in sorted(set(old_api) | set(new_api)) if old_api.get(key) != new_api.get(key)]
        changed = sorted(p for p in common if left[p] and right[p] and left[p] != right[p])
        protection = {path for path in set(left) | set(right)
                      if scopes_match(path, before['context']['member'].get('do_not_touch', []))}
        categories = {'architecture': {8, 9, 10}, 'requirements': {6}, 'implementation_status': {7},
                      'dependencies': {13}, 'risks_and_conflicts': {18}, 'deployment': {15}, 'data_flow': {12}}
        findings = {}
        for category, numbers in categories.items():
            def values(data):
                return {record['id'].split(':', 2)[-1]: record for section in data['context']['sections']
                        if section['number'] in numbers for record in section['records']}
            old, new = values(before), values(after)
            findings[category] = [{'record': key, 'before': old.get(key), 'after': new.get(key),
                                   'before_branch': before['context']['identity']['branch'],
                                   'after_branch': after['context']['identity']['branch']}
                                  for key in sorted(set(old) | set(new)) if old.get(key, {}).get('text') != new.get(key, {}).get('text')]
        return scrub({'before': before['context']['identity'], 'after': after['context']['identity'],
                      'completeness': {'before': before['context']['completeness'], 'after': after['context']['completeness']},
                      'only_in_before_inventory': sorted(set(left) - set(right)),
                      'only_in_after_inventory': sorted(set(right) - set(left)),
                      'changed_blob_paths': changed,
                      'unknown_blob_paths': sorted(p for p in common if not left[p] or not right[p]),
                      'contract_changes': api_changes, 'findings': findings,
                      'protected_changes': sorted(protection & (set(changed) | (set(left) ^ set(right)))),
                      'warnings': ['Comparison uses analyzed inventories and retained contracts, not a Git merge or runtime compatibility check. Inventory-only differences can reflect omitted/truncated discovery. No branches or files were changed.']}, secret_values(token))
