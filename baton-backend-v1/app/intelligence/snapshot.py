"""Replaceable, bounded process-local storage. Never durable or a permission boundary."""
from copy import deepcopy
from threading import RLock
from typing import Protocol
from app.intelligence.models import RepositoryIntelligence, SnapshotStatus
from app.intelligence.safety import sanitize_model
from app.core.secrets import secret_values

MAX_ENTRIES = 20
MAX_CACHE_BYTES = 40_000_000

class SnapshotStore(Protocol):
    def save(self, snapshot: RepositoryIntelligence) -> None: ...
    def load(self, owner, repo, branch, commit, folder=""): ...
    def exists(self, owner, repo, branch, commit, folder="") -> bool: ...
    def invalidate(self, owner, repo, branch=None, commit=None, folder=None) -> None: ...
    def metadata(self) -> list[dict]: ...

class MemorySnapshotStore:
    def __init__(self, max_entries=MAX_ENTRIES, max_bytes=MAX_CACHE_BYTES):
        self.entries = {}
        self.sizes = {}
        self.lock = RLock()
        self.max_entries = max_entries
        self.max_bytes = max_bytes

    @staticmethod
    def key(owner, repo, branch, commit, folder=""):
        return (owner.lower(), repo.lower(), branch, commit, folder.strip('/'), '1.1')

    def save(self, snapshot):
        snapshot = sanitize_model(snapshot, secret_values())
        if not snapshot.commit or snapshot.analysis_version != '1.1' or self.max_entries <= 0:
            return  # unknown states cannot be reused safely
        key = self.key(snapshot.owner, snapshot.repo, snapshot.branch, snapshot.commit, snapshot.project_root)
        import json
        from dataclasses import asdict
        size = len(json.dumps(asdict(snapshot), default=str).encode())
        if size > self.max_bytes:
            return
        with self.lock:
            self.entries.pop(key, None)
            self.sizes.pop(key, None)
            while self.entries and (len(self.entries) >= self.max_entries or sum(self.sizes.values()) + size > self.max_bytes):
                oldest = next(iter(self.entries))
                del self.entries[oldest]
                del self.sizes[oldest]
            self.entries[key] = deepcopy(snapshot)
            self.sizes[key] = size

    def load(self, owner, repo, branch, commit, folder=""):
        if not commit:
            return None
        with self.lock:
            return deepcopy(self.entries.get(self.key(owner, repo, branch, commit, folder)))

    def exists(self, owner, repo, branch, commit, folder=""):
        if not commit:
            return False
        with self.lock:
            return self.key(owner, repo, branch, commit, folder) in self.entries

    def invalidate(self, owner, repo, branch=None, commit=None, folder=None):
        with self.lock:
            for key in list(self.entries):
                if key[:2] == (owner.lower(), repo.lower()) and (branch is None or key[2] == branch) and (commit is None or key[3] == commit) and (folder is None or key[4] == folder.strip('/')):
                    del self.entries[key]
                    del self.sizes[key]

    def metadata(self):
        with self.lock:
            return [dict(owner=v.owner, repo=v.repo, branch=v.branch, commit=v.commit, folder=v.project_root, status=v.snapshot_status, generated=v.generated, analysis_version=v.analysis_version) for v in self.entries.values()]

_DEFAULT = MemorySnapshotStore()

def store(intelligence):
    _DEFAULT.save(intelligence)

save = store

def lookup(owner, repo, branch, commit, folder=""):
    return _DEFAULT.load(owner, repo, branch, commit, folder)

load = lookup

def exists(owner, repo, branch, commit, folder=""):
    return _DEFAULT.exists(owner, repo, branch, commit, folder)

def is_stale(owner, repo, branch, current_commit, folder=""):
    if not current_commit or exists(owner, repo, branch, current_commit, folder):
        return False
    return any(x['owner'].lower() == owner.lower() and x['repo'].lower() == repo.lower() and x['branch'] == branch and x['folder'] == folder.strip('/') and x['commit'] != current_commit for x in snapshot_info())

def get_stale_snapshot(owner, repo, branch, folder=""):
    for info in reversed(snapshot_info()):
        if (info['owner'].lower(), info['repo'].lower(), info['branch'], info['folder']) == (owner.lower(), repo.lower(), branch, folder.strip('/')):
            value = lookup(owner, repo, branch, info['commit'], folder)
            value.snapshot_status = SnapshotStatus.STALE
            return value
    return None

def invalidate(owner, repo, branch=None, commit=None, folder=None):
    _DEFAULT.invalidate(owner, repo, branch, commit, folder)

def clear_all():
    with _DEFAULT.lock:
        _DEFAULT.entries.clear()
        _DEFAULT.sizes.clear()

def snapshot_info():
    return _DEFAULT.metadata()

metadata = snapshot_info

def cache_size():
    return len(snapshot_info())
