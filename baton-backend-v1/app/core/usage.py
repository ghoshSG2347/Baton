"""Request-local numeric accounting. No prompts, identities, credentials or global store."""
from contextvars import ContextVar
from dataclasses import dataclass, field
import json
import time


@dataclass
class RequestUsage:
    github_requests: int = 0
    github_downloads: int = 0
    cache_hits: int = 0
    snapshot_hits: int = 0
    ai_requests: int = 0
    input_tokens: int | None = 0
    output_tokens: int | None = 0
    total_tokens: int | None = 0
    thinking_tokens: int | None = 0
    provider_latency_ms: int = 0
    quota: dict = field(default_factory=dict)


CURRENT_USAGE: ContextVar[RequestUsage | None] = ContextVar('baton_request_usage', default=None)


def increment(name):
    usage = CURRENT_USAGE.get()
    if usage is not None:
        setattr(usage, name, getattr(usage, name) + 1)


def observe_quota(metadata):
    usage = CURRENT_USAGE.get()
    if usage is not None:
        usage.quota = {key: value for key, value in metadata.get('rate_limit', {}).items()
                       if key in ('limit', 'remaining', 'used', 'reset_at') and type(value) is int and 0 <= value <= 2**53 - 1}


def start_provider():
    usage = CURRENT_USAGE.get()
    if usage is not None:
        usage.ai_requests += 1
        # Only actual provider-reported counts may replace UNKNOWN.
        usage.input_tokens = usage.output_tokens = usage.total_tokens = usage.thinking_tokens = None


def finish_provider(started, metadata=None):
    usage = CURRENT_USAGE.get()
    if usage is None:
        return
    usage.provider_latency_ms += round((time.monotonic() - started) * 1000)
    metadata = metadata if isinstance(metadata, dict) else {}
    for target, source in [('input_tokens', 'promptTokenCount'), ('output_tokens', 'candidatesTokenCount'),
                           ('total_tokens', 'totalTokenCount'), ('thinking_tokens', 'thoughtsTokenCount')]:
        value = metadata.get(source)
        setattr(usage, target, value if type(value) is int and 0 <= value <= 2**53 - 1 else None)


class UsageResponses:
    """Return measurements on the same response; no extra polling or usage endpoint."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not scope.get('path', '').startswith('/api/v1/'):
            return await self.app(scope, receive, send)
        usage = RequestUsage()
        handle = CURRENT_USAGE.set(usage)
        started = time.monotonic()

        async def measured_send(message):
            if message['type'] == 'http.response.start':
                values = {**vars(usage), 'latency_ms': round((time.monotonic() - started) * 1000)}
                message = {**message, 'headers': [*message['headers'],
                            (b'x-baton-usage', json.dumps(values, separators=(',', ':')).encode('ascii'))]}
            await send(message)
        try:
            await self.app(scope, receive, measured_send)
        finally:
            CURRENT_USAGE.reset(handle)
