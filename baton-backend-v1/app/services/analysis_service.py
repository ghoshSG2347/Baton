"""
Updated Analysis Service — snapshot-aware intelligence pipeline.

Changes from v1:
  1. Checks snapshot cache before re-analyzing
  2. Detects stale snapshots (repository changed since last analysis)
  3. Runs the intelligence pipeline instead of the old RepositoryAnalyzer
  4. Returns both the RepositoryIntelligence AND backward-compatible analysis dict
  5. Preserves all existing API response shapes for frontend compatibility

Token security:
  - GitHub tokens are NEVER stored in the snapshot
  - Tokens are used ephemerally for this request only
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import get_settings
from app.services.github_service import GitHubService
from app.utils.file_filters import is_relevant
from app.intelligence import pipeline as intel_pipeline
from app.intelligence import snapshot as snap


class AnalysisService:
    def __init__(self, token: str | None = None):
        self.github = GitHubService(token)
        # Token is NOT stored in any snapshot — only used for this request

    async def analyze(
        self,
        owner: str,
        repo: str,
        branch: str,
        folder: str = "",
    ) -> dict:
        """
        Analyze a repository and return backward-compatible analysis dict.
        Uses snapshot cache when the same commit has already been analyzed.

        Returns the legacy analysis dict format (for backward compat with
        existing API endpoints and tests).
        """
        intelligence = await self.analyze_intelligence(owner, repo, branch, folder)
        return intelligence.to_legacy_analysis()

    async def analyze_intelligence(
        self,
        owner: str,
        repo: str,
        branch: str,
        folder: str = "",
    ) -> "RepositoryIntelligence":  # type: ignore[name-defined]
        """
        Analyze a repository and return the full RepositoryIntelligence model.
        Snapshot-aware: returns cached result if commit matches.
        """
        from app.intelligence.models import RepositoryIntelligence

        settings = get_settings()

        # --- Fetch repository tree to get current commit ---
        tree_snapshot = await self.github.tree_snapshot(owner, repo, branch)
        current_commit = tree_snapshot.get("sha")

        # --- Snapshot lookup ---
        cached = snap.lookup(owner, repo, branch, current_commit)
        if cached is not None:
            return cached

        # --- Stale detection ---
        is_stale = snap.is_stale(owner, repo, branch, current_commit)
        if is_stale:
            stale = snap.get_stale_snapshot(owner, repo, branch)
            # We'll proceed to re-analyze and replace the stale snapshot
            # (stale variable used only for logging/warnings below)

        # --- Collect files ---
        all_items = tree_snapshot.get("tree", [])
        prefix = folder.strip("/")
        items = [
            x for x in all_items
            if (not prefix or x.get("path", "") == prefix
                or x.get("path", "").startswith(prefix + "/"))
            and x.get("type") in {"blob", "tree"}
            and is_relevant(x.get("path", ""))
        ]
        blobs = [
            {"path": x["path"], "type": x["type"], "size": x.get("size")}
            for x in items
        ]

        # --- Load file contents (bounded) ---
        contents: dict[str, str] = {}
        count = 0
        skipped: list[str] = []

        for x in items:
            if x.get("type") != "blob":
                continue
            if count >= settings.max_files_per_analysis:
                skipped.append(x["path"])
                continue
            if x.get("size", 0) > settings.max_file_size_bytes:
                skipped.append(x["path"])
                continue
            try:
                file_data = await self.github.file(owner, repo, branch, x["path"])
                contents[x["path"]] = file_data["content"]
                count += 1
            except Exception:
                skipped.append(x["path"])

        # --- Build metadata ---
        metadata = {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "folder": folder,
            "commit": current_commit,
            "generated": datetime.now(timezone.utc).isoformat(),
            "files_analyzed": count,
            "analysis_warnings": [],
        }

        if is_stale:
            metadata["analysis_warnings"].append(
                "Repository has changed since the previous analysis snapshot."
            )

        # --- Run intelligence pipeline ---
        intelligence = intel_pipeline.run(
            files=blobs,
            contents=contents,
            metadata=metadata,
            skipped_paths=skipped,
        )

        # --- Store in snapshot cache (NO token stored) ---
        snap.store(intelligence)

        return intelligence
