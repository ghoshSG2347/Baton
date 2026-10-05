/** Recognizable credentials and in-memory access tokens are never saved as user content. */
export function redactUserText(value: string, known: string[] = []): string {
  let safe = value;
  known.filter(Boolean).forEach((secret) => { safe = safe.split(secret).join('[REDACTED]'); });
  return safe.replace(/\b(?:AIza[A-Za-z0-9_-]{35}|gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{10,})\b/g, '[REDACTED]')
    .replace(/((?:api[_-]?key|password|secret|token)\s*[:=]\s*)\S+/gi, '$1[REDACTED]');
}

export function redactUserData(value: unknown, known: string[]): unknown {
  if (typeof value === 'string') return redactUserText(value, known);
  if (Array.isArray(value)) return value.map((item) => redactUserData(item, known));
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, redactUserData(item, known)]));
  return value;
}
