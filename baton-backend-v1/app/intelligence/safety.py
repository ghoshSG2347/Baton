"""Sanitize untrusted input before any finding or snapshot is constructed."""
import re
from dataclasses import fields, is_dataclass, replace
from enum import Enum
from pathlib import PurePosixPath


def sanitize_model(value, known_secrets=()):
    """Preserve canonical types while redacting every retained string, including paths."""
    if isinstance(value, Enum):
        return value
    if isinstance(value, str):
        return sanitize(value, known_secrets)
    if is_dataclass(value):
        return replace(value, **{f.name: sanitize_model(getattr(value, f.name), known_secrets) for f in fields(value)})
    if isinstance(value, dict):
        return {sanitize_model(key, known_secrets): sanitize_model(item, known_secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_model(item, known_secrets) for item in value]
    return value


def sensitive_path(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return (name.startswith('.env') and name not in {'.env.example', '.env.sample', '.env.template'}) or name.endswith(('.pem', '.key', '.p12', '.pfx')) or name in {'credentials.json', 'id_rsa', 'id_ed25519'}


def sanitize(text: str, known_secrets=()) -> str:
    for secret in known_secrets:
        if secret:
            text = text.replace(secret, '[REDACTED]')
    text = re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----', '[REDACTED]', text, flags=re.S)
    text = re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{10,}|AKIA[A-Z0-9]{16})\b', '[REDACTED]', text)
    text = re.sub(r'\bAIza[A-Za-z0-9_-]{35}\b', '[REDACTED]', text)
    text = re.sub(r'(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)(https?://)[^\s/@:]+:[^\s/@]+@', r'\1[REDACTED]@', text)
    # Redact secret assignments in source, JSON, YAML, TOML and documentation.
    text = re.sub(r'''(?im)(["']?[\w.-]*(?:secret|token|password|passwd|api[_-]?key|credential)[\w.-]*["']?\s*[:=]\s*)(?:["'][^"'\n]*["']|[^\s,;\n]+)''', r'\1"[REDACTED]"', text)
    # Environment templates retain names, never values (including innocuous ones).
    return text


def sanitize_file(path: str, text: str, known_secrets=()) -> str:
    text = sanitize(text, known_secrets)
    if PurePosixPath(path).name.startswith('.env'):
        text = re.sub(r'(?m)^(\s*(?:export\s+)?[A-Za-z_][\w]*\s*=).*$', r'\1[REDACTED]', text)
    return text
