"""
Intent vs Reality reconciliation.

Compares documented requirements against observed implementation.

CRITICAL: The two must NEVER be silently merged.

Categories:
  DOCUMENTED  — what the PRD/README says should exist
  OBSERVED    — what the code actually contains
  RECONCILED  — the comparison result

Possible statuses:
  NOT_STARTED             — documented but no code evidence found
  PARTIALLY_IMPLEMENTED   — some but not all code components detected
  IMPLEMENTED             — code evidence found for all key aspects
  IMPLEMENTED_WITH_DIFFERENCES — code found but differs from documented intent
  NOT_DETECTABLE          — code might exist but Baton cannot determine
  CONFLICTING             — sources contradict each other
  UNKNOWN                 — insufficient information

Example:
  PRD:  "OTP email login"
  Code: Login UI found, but no OTP backend endpoint found
  → PARTIALLY_IMPLEMENTED
  → missing: "OTP backend endpoint"
"""

from __future__ import annotations

import re
from typing import Optional

from app.intelligence.models import (
    ApiEndpoint,
    Confidence,
    DirectoryClassification,
    DirectoryRole,
    ImplementationStatus,
    IntelligenceConflict,
    Requirement,
)


# ---------------------------------------------------------------------------
# Keyword-to-code signal mapping
# ---------------------------------------------------------------------------

# Maps requirement keywords to code search patterns
_FEATURE_SIGNALS: list[tuple[list[str], list[str]]] = [
    # (requirement keywords, code patterns)
    (
        ["authentication", "login", "auth", "sign in", "signin"],
        [r"auth|login|signin|jwt|token|session|password|credential"],
    ),
    (
        ["registration", "register", "signup", "sign up"],
        [r"register|signup|sign.up|create.account|user.creat"],
    ),
    (
        ["otp", "one.time.password", "verification code"],
        [r"otp|one.time|verification.code|totp"],
    ),
    (
        ["search"],
        [r"search|query|filter|find|lookup"],
    ),
    (
        ["upload", "file upload"],
        [r"upload|multipart|FormData|file"],
    ),
    (
        ["payment", "checkout", "billing", "stripe", "subscription"],
        [r"payment|checkout|billing|stripe|invoice|subscription"],
    ),
    (
        ["notification", "email", "smtp"],
        [r"notification|email|smtp|sendmail|mailgun|ses|nodemailer"],
    ),
    (
        ["dashboard", "analytics", "metrics", "report"],
        [r"dashboard|analytics|metric|report|chart|graph"],
    ),
    (
        ["admin", "management"],
        [r"admin|management|superuser|staff"],
    ),
    (
        ["api", "rest api", "endpoint", "http"],
        [r"@app\.|@router\.|router\.|app\.get|app\.post|app\.route"],
    ),
    (
        ["database", "storage", "persist"],
        [r"database|db\.|model\.|schema\.|repository|migration"],
    ),
    (
        ["chat", "message", "messaging"],
        [r"chat|message|websocket|ws\.|socket\.io"],
    ),
    (
        ["deploy", "deployment", "ci/cd", "docker"],
        [r"deploy|docker|kubernetes|ci|cd|github.action|render|vercel"],
    ),
    (
        ["test", "testing"],
        [r"test|pytest|jest|spec|describe\(|assert"],
    ),
    (
        ["machine learning", "ml model", "training", "classification", "prediction"],
        [r"model|train|predict|classify|sklearn|torch|tensorflow"],
    ),
    (
        ["book", "reading", "library"],
        [r"book|read|library|volume|chapter"],
    ),
]


def reconcile(
    requirements: list[Requirement],
    contents: dict[str, str],
    api_endpoints: list[ApiEndpoint],
    api_calls: list[ApiEndpoint],
    directory_classifications: list[DirectoryClassification],
) -> tuple[list[Requirement], list[IntelligenceConflict], list[str], list[str]]:
    """
    Compare documented requirements against observed code.

    Args:
        requirements: extracted requirements (DOCUMENTED status)
        contents:     decoded file contents
        api_endpoints: detected server routes
        api_calls:    detected client API calls
        directory_classifications: classified directories

    Returns:
        (updated_requirements, conflicts, observed_features, missing_work)
    """
    conflicts: list[IntelligenceConflict] = []
    observed_features: list[str] = []
    missing_work: list[str] = []

    all_text = "\n".join(contents.values())
    route_paths = [e.route.lower() for e in api_endpoints]
    call_paths = [c.route.lower() for c in api_calls]

    for req in requirements:
        observed_code: list[str] = []
        missing: list[str] = []
        intent_lower = req.intent.lower()

        # Find matching signal groups for this requirement
        matched_patterns: list[str] = []
        for keywords, code_patterns in _FEATURE_SIGNALS:
            if any(kw in intent_lower for kw in keywords):
                matched_patterns.extend(code_patterns)

        if not matched_patterns:
            # No known signal group — can't determine
            req.status = ImplementationStatus.NOT_DETECTABLE
            req.confidence = Confidence.LOW
            continue

        # Search for code patterns
        code_found: list[str] = []
        for pat in matched_patterns:
            matches = _search_content(all_text, pat)
            if matches:
                code_found.append(pat)

        # Search in route paths
        route_found = any(
            any(kw in rp for kw in _keywords_from_intent(intent_lower))
            for rp in route_paths + call_paths
        )

        if code_found or route_found:
            observed_code = code_found[:5]
            if route_found:
                observed_code.append("Route/endpoint evidence found")
            observed_features.append(req.intent[:100])

            # Check if all expected components are present
            if len(code_found) >= 2 or (code_found and route_found):
                req.status = ImplementationStatus.IMPLEMENTED
                req.confidence = Confidence.MEDIUM
            else:
                req.status = ImplementationStatus.PARTIALLY_IMPLEMENTED
                req.confidence = Confidence.LOW
                missing.append("Not all expected code components detected")
        else:
            req.status = ImplementationStatus.NOT_STARTED
            req.confidence = Confidence.LOW
            missing.append("No code evidence found for this requirement")
            missing_work.append(req.intent[:100])

        req.observed_code = observed_code
        req.missing_pieces = missing
        req.evidence.extend([f"Code search: {'found' if code_found else 'not found'}"])

    return requirements, conflicts, observed_features, missing_work


def detect_doc_vs_code_conflicts(
    doc_sources: list,  # list[DocumentationSource]
    contents: dict[str, str],
    api_endpoints: list[ApiEndpoint],
    directory_classifications: list[DirectoryClassification],
) -> list[IntelligenceConflict]:
    """
    Detect conflicts between documentation claims and observed code.

    Examples:
      README says "PostgreSQL" → code only shows SQLite config
      README says "React frontend" → no React files found
    """
    conflicts: list[IntelligenceConflict] = []
    all_text = "\n".join(contents.values())

    for doc in doc_sources:
        text = contents.get(doc.path, doc.raw_excerpt or "")
        if not text:
            continue

        # Database conflict detection
        db_claims = _extract_db_claims(text)
        for db_name, db_pattern in db_claims.items():
            if not re.search(db_pattern, all_text, re.I):
                conflicts.append(IntelligenceConflict(
                    description=f"Database claim vs. observed configuration",
                    source_a=doc.path,
                    claim_a=f"References {db_name}",
                    source_b="Observed source code / configuration",
                    claim_b=f"No {db_name} configuration or client detected in code",
                    resolution="Verify which database is actually used or planned.",
                ))

        # Framework conflict detection
        fw_claims = _extract_framework_claims(text)
        for fw_name, fw_pattern in fw_claims.items():
            if not re.search(fw_pattern, all_text, re.I):
                # Only report if we have a substantial amount of code to search
                if len(all_text) > 500:
                    conflicts.append(IntelligenceConflict(
                        description=f"Framework claim vs. observed code",
                        source_a=doc.path,
                        claim_a=f"References {fw_name}",
                        source_b="Observed source code",
                        claim_b=f"No {fw_name} imports or usage detected",
                        resolution="Confirm whether this framework is planned or already implemented.",
                    ))

    return conflicts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search_content(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, re.I | re.MULTILINE))


def _keywords_from_intent(intent: str) -> list[str]:
    """Extract meaningful keywords from a requirement intent string."""
    # Remove common words
    stop = {
        "the", "a", "an", "of", "in", "to", "for", "and", "or", "that",
        "with", "as", "by", "is", "are", "be", "can", "will", "should",
        "must", "allow", "user", "users", "system",
    }
    words = re.findall(r"\b[a-z]{3,}\b", intent.lower())
    return [w for w in words if w not in stop][:5]


def _extract_db_claims(text: str) -> dict[str, str]:
    """Extract database mentions from documentation."""
    claims: dict[str, str] = {}
    db_map = {
        "PostgreSQL": r"postgres|psycopg|pg\b",
        "MySQL": r"mysql",
        "MongoDB": r"mongo|pymongo",
        "SQLite": r"sqlite",
        "Redis": r"redis",
        "Supabase": r"supabase",
        "Firebase": r"firebase",
    }
    for db, pattern in db_map.items():
        if re.search(pattern, text, re.I):
            claims[db] = pattern
    return claims


def _extract_framework_claims(text: str) -> dict[str, str]:
    """Extract framework mentions from documentation."""
    claims: dict[str, str] = {}
    fw_map = {
        "React": r"from ['\"]react['\"]|import React",
        "Vue": r"from ['\"]vue['\"]",
        "FastAPI": r"from fastapi import",
        "Django": r"from django\.|import django",
        "Flask": r"from flask import",
    }
    for fw, pattern in fw_map.items():
        if re.search(fw, text, re.I):
            claims[fw] = pattern
    return claims
