def estimate_tokens(text: str) -> int: return max(1, len(text)//4) if text else 0
def fit_context(text: str, max_bytes: int) -> str:
    max_bytes = max(0, max_bytes)
    if len(text.encode()) <= max_bytes:
        return text
    marker = "\n...[truncated]"
    if max_bytes < len(marker.encode()):
        return marker.encode()[:max_bytes].decode('utf-8', 'ignore')
    return text.encode()[:max_bytes - len(marker.encode())].decode('utf-8', 'ignore') + marker
