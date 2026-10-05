"""
Repository Intelligence Snapshot Cache.

Provides a bounded in-memory snapshot cache keyed by (owner, repo, branch, commit).
This avoids re-analyzing the same repository state on repeated context requests.

Design constraints:
  - No GitHub tokens or secrets are stored in the cache.
  - Cache is keyed by owner/repo/branch/commit for precise staleness detection.
  - Cache is bounded to MAX_ENTRIES to limit memory usage.
  - Stale detection: if a new commit is detected for a cached branch, the
    snapshot is marked STALE rather than silently returned as current.
  - Replace with durable persistence (Redis, DB) later without changing
    the intelligence model or pipeline — only this module changes.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Optional

from app.intelligence.models import RepositoryIntelligence, SnapshotStatus

_CACHE: dict[str, RepositoryIntelligence] = {}
_LOCK = threading.Lock()
MAX_ENTRIES = 20    # bounded to avoid unbounded memory growth


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def _exact_key(owner: str, repo: str, branch: str, commit: str) -> str:
    """Exact cache key including commit SHA."""
    return f"{owner.lower()}/{repo.lower()}@{branch}#{commit}"


def _branch_prefix(owner: str, repo: str, branch: str) -> str:
    """Prefix used to find any cached entry for a given branch."""
    return f"{owner.lower()}/{repo.lower()}@{branch}#"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def store(intelligence: RepositoryIntelligence) -> None:
    """
    Store a RepositoryIntelligence snapshot.
    Evicts the oldest entry when the cache is full.
    NEVER stores GitHub tokens or secret values.
    """
    if not intelligence.commit:
        # Without a commit SHA we cannot reliably detect staleness — store
        # with a synthetic key but mark as PARTIAL.
        intelligence.snapshot_status = SnapshotStatus.PARTIAL
        key = _exact_key(intelligence.owner, intelligence.repo, intelligence.branch, "unknown")
    else:
        key = _exact_key(
            intelligence.owner, intelligence.repo, intelligence.branch, intelligence.commit
        )
        intelligence.snapshot_status = SnapshotStatus.CURRENT

    with _LOCK:
        if len(_CACHE) >= MAX_ENTRIES and key not in _CACHE:
            # Evict the oldest entry (dict insertion order in Python 3.7+)
            oldest = next(iter(_CACHE))
            del _CACHE[oldest]
        _CACHE[key] = intelligence


def lookup(owner: str, repo: str, branch: str, commit: Optional[str]) -> Optional[RepositoryIntelligence]:
    """
    Return a cached RepositoryIntelligence if the exact commit matches.
    Returns None if no matching snapshot exists.
    Does NOT return a snapshot for a different commit — use is_stale() for that.
    """
    if not commit:
        return None
    key = _exact_key(owner, repo, branch, commit)
    with _LOCK:
        return _CACHE.get(key)


def is_stale(owner: str, repo: str, branch: str, current_commit: Optional[str]) -> bool:
    """
    Returns True when a cached snapshot exists for this branch but the commit
    has changed — meaning the repository has been updated since the last analysis.
    Returns False if no snapshot exists (not stale, just absent).
    """
    if not current_commit:
        return False
    prefix = _branch_prefix(owner, repo, branch)
    with _LOCK:
        for k, v in _CACHE.items():
            if k.startswith(prefix):
                stored_commit = v.commit
                return bool(stored_commit and stored_commit != current_commit)
    return False


def get_stale_snapshot(owner: str, repo: str, branch: str) -> Optional[RepositoryIntelligence]:
    """
    Return the most recently stored snapshot for a branch regardless of
    commit match. Used to expose staleness information to callers.
    """
    prefix = _branch_prefix(owner, repo, branch)
    with _LOCK:
        for k, v in _CACHE.items():
            if k.startswith(prefix):
                snapshot = v
                snapshot.snapshot_status = SnapshotStatus.STALE
                return snapshot
    return None


def invalidate(owner: str, repo: str, branch: Optional[str] = None) -> None:
    """Remove all cached snapshots for a repo (or specific branch)."""
    prefix = (
        _branch_prefix(owner, repo, branch)
        if branch
        else f"{owner.lower()}/{repo.lower()}@"
    )
    with _LOCK:
        keys = [k for k in _CACHE if k.startswith(prefix)]
        for k in keys:
            del _CACHE[k]


def clear_all() -> None:
    """Clear the entire cache. Used in tests."""
    with _LOCK:
        _CACHE.clear()


def snapshot_info() -> list[dict]:
    """Return metadata about all cached snapshots (no tokens, no secrets)."""
    with _LOCK:
        return [
            {
                "key": k,
                "owner": v.owner,
                "repo": v.repo,
                "branch": v.branch,
                "commit": v.commit,
                "status": v.snapshot_status,
                "generated": v.generated,
            }
            for k, v in _CACHE.items()
        ]


def cache_size() -> int:
    with _LOCK:
        return len(_CACHE)
