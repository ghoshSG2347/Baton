"""
Requirement extraction from documentation.

Extracts documented requirements and features from PRD, README, specification,
and architecture documents.

Each requirement captures:
  - source_document   (which file)
  - source_section    (which heading)
  - intent            (what it says)

These are DOCUMENTED requirements only.
Observed implementation is determined separately in feature_reconciler.py.
The two are NEVER merged until explicitly compared.
"""

from __future__ import annotations

import re
from typing import Optional

from app.intelligence.models import (
    Confidence,
    DocumentationSource,
    ImplementationStatus,
    Requirement,
)


def extract(
    doc_sources: list[DocumentationSource],
    contents: dict[str, str],
) -> list[Requirement]:
    """
    Extract requirements from documentation sources.

    Args:
        doc_sources: detected documentation files with roles and headings
        contents:    decoded file contents

    Returns:
        list of Requirement (DOCUMENTED status, no observed code yet)
    """
    requirements: list[Requirement] = []
    req_id_counter = 0

    priority_roles = {"PRD", "REQUIREMENTS", "SPECIFICATION", "ARCHITECTURE", "DESIGN"}

    for doc in doc_sources:
        if doc.role not in priority_roles and doc.role != "README":
            continue

        text = contents.get(doc.path, doc.raw_excerpt or "")
        if not text:
            continue

        extracted = _extract_from_document(doc.path, doc.role, text)
        for req in extracted:
            req_id_counter += 1
            if not req.id:
                req.id = f"REQ-{req_id_counter:03d}"
            requirements.append(req)

    return requirements


def _extract_from_document(
    path: str,
    role: str,
    text: str,
) -> list[Requirement]:
    """
    Extract requirements from a single document using heading/bullet structure.
    """
    requirements: list[Requirement] = []
    current_section: Optional[str] = None
    current_subsection: Optional[str] = None

    # Feature/requirement sections we care about
    _FEATURE_SECTION_PATTERNS: list[str] = [
        r"feature|requirement|functionality|capability|must|should|will|user.stor",
        r"product.requirement|prd|specification|scope|mvp",
        r"overview|summary|objective|goal|purpose",
        r"tech|stack|architecture|system|component|service|api|endpoint",
    ]

    _SKIP_SECTIONS: frozenset[str] = frozenset({
        "license", "changelog", "contributors", "contributing",
        "installation", "setup", "getting started", "prerequisites",
        "acknowledgements", "credits",
    })

    in_relevant_section = (role in {"PRD", "REQUIREMENTS", "SPECIFICATION"})  # PRDs are fully relevant
    lines = text.splitlines()

    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith(('```', '~~~')):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue

        # Heading detection
        h_match = re.match(r"^(#{1,4})\s+(.+)", stripped)
        if h_match:
            level = len(h_match.group(1))
            heading = h_match.group(2).strip()
            heading_lower = heading.lower()

            if heading_lower in _SKIP_SECTIONS:
                in_relevant_section = False
                i += 1
                continue

            if level <= 2:
                current_section = heading
                current_subsection = None
                in_relevant_section = any(
                    re.search(p, heading_lower) for p in _FEATURE_SECTION_PATTERNS
                )
                if role == "PRD":
                    in_relevant_section = True
            else:
                current_subsection = heading

            i += 1
            continue

        # Skip if not in a relevant section
        if not in_relevant_section:
            i += 1
            continue

        # Bullet list items as requirements
        bullet_match = re.match(r"^[-*+]\s+(.+)", stripped)
        if bullet_match:
            content = bullet_match.group(1).strip()
            # Multi-line bullet continuation
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if not next_line.strip() or re.match(r"^[-*+#]|^\d+[.)]", next_line.strip()):
                    break
                if next_line.startswith(("  ", "\t")):
                    content += " " + next_line.strip()
                else:
                    break
                j += 1

            if len(content) >= 3:  # retain concise explicit requirements
                req = _make_requirement(
                    path=path,
                    section=current_subsection or current_section,
                    intent=content,
                )
                req.source_line = i + 1
                requirements.append(req)
            i = j
            continue

        # Numbered list items
        num_match = re.match(r"^\d+[.)]\s+(.+)", stripped)
        if num_match:
            content = num_match.group(1).strip()
            if len(content) >= 3:
                req = _make_requirement(
                    path=path,
                    section=current_subsection or current_section,
                    intent=content,
                )
                req.source_line = i + 1
                requirements.append(req)
            i += 1
            continue

        if re.search(r'\b(?:must|shall|should|will|users? can)\b', stripped, re.I) and len(stripped) >= 10:
            req = _make_requirement(path, current_subsection or current_section, stripped)
            req.source_line = i + 1
            requirements.append(req)
        i += 1

    return requirements


def _make_requirement(
    path: str,
    section: Optional[str],
    intent: str,
) -> Requirement:
    return Requirement(
        id=(re.search(r'\b(?:REQ|FR|NFR)-[A-Za-z0-9-]+\b', intent).group(0) if re.search(r'\b(?:REQ|FR|NFR)-[A-Za-z0-9-]+\b', intent) else ''),
        priority=(re.search(r'\b(?:P[0-3]|HIGH|MEDIUM|LOW)\b', intent).group(0) if re.search(r'\b(?:P[0-3]|HIGH|MEDIUM|LOW)\b', intent) else None),
        source_document=path,
        source_section=section,
        intent=intent,
        status=ImplementationStatus.UNKNOWN,
        observed_code=[],
        missing_pieces=[],
        conflicts=[],
        evidence=[f"Documented in `{path}`" + (f" §{section}" if section else "")],
        confidence=Confidence.LOW,   # raised by reconciler after code search
    )
