def estimate_tokens(text: str) -> int: return max(1, len(text)//4) if text else 0
def fit_context(text:str, max_bytes:int)->str: return text if len(text.encode())<=max_bytes else text.encode()[:max_bytes].decode("utf-8","ignore")+"\n...[truncated]"
