"""Bounded process-local chat history, isolated by authenticated context binding."""
from copy import deepcopy
from collections import OrderedDict
from threading import RLock
from time import monotonic
from uuid import uuid4
from app.core.exceptions import BatonError


class ConversationStore:
    def __init__(self, capacity=100, ttl=3600):
        self.entries = OrderedDict()
        self.lock = RLock()
        self.capacity, self.ttl = capacity, ttl

    def load(self, identifier, binding):
        if not identifier:
            return {'id': None, 'revision': 0, 'turns': []}
        with self.lock:
            item = self.entries.get(identifier)
            if not item or item['binding'] != binding or monotonic() - item['updated'] > self.ttl:
                raise BatonError('Conversation expired or its repository, commit, role or authorization changed. Start a new conversation.', 409)
            return deepcopy(item)

    def append(self, identifier, binding, revision, question, answer):
        with self.lock:
            existing = self.load(identifier, binding) if identifier else {'revision': 0, 'turns': []}
            if existing['revision'] != revision:
                raise BatonError('Conversation changed while answering. Retry the question.', 409)
            if len(existing['turns']) >= 20:
                raise BatonError('Conversation limit reached. Start a new conversation.', 409)
            identifier = identifier or uuid4().hex
            item = {'id': identifier, 'binding': binding, 'revision': revision + 1,
                    'updated': monotonic(), 'turns': [*existing['turns'], {'question': question, 'answer': answer}]}
            self.entries.pop(identifier, None)
            while len(self.entries) >= self.capacity:
                self.entries.popitem(last=False)
            self.entries[identifier] = item
            return identifier


CONVERSATIONS = ConversationStore()
