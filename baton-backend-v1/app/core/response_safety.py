"""Last boundary: configured secrets cannot leave any JSON API response."""
import json
from app.core.secrets import secret_values
from app.generators.context_builder import scrub


class SafeJSONResponses:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        start, chunks, size = None, [], 0
        headers = dict(scope.get('headers', []))
        secrets = secret_values(*(headers.get(name, b'').decode('utf-8', 'ignore')
                                  for name in (b'x-github-token', b'x-baton-key')))

        async def safe_send(message):
            nonlocal start, size
            if message['type'] == 'http.response.start':
                start = message
            elif message['type'] == 'http.response.body':
                size += len(message.get('body', b''))
                if size <= 32_000_000:
                    chunks.append(message.get('body', b''))
                if message.get('more_body', False):
                    return
                body = b''.join(chunks)
                content_type = dict(start['headers']).get(b'content-type', b'')
                if size > 32_000_000:
                    start['status'] = 413
                    body = b'{"detail":"Response exceeds the configured safety limit."}'
                elif b'application/json' in content_type:
                    try:
                        body = json.dumps(scrub(json.loads(body), secrets), ensure_ascii=False,
                                          separators=(',', ':')).encode()
                    except (ValueError, UnicodeError):
                        start['status'] = 502
                        body = b'{"detail":"Invalid backend response."}'
                start['headers'] = [(k, v) for k, v in start['headers'] if k != b'content-length']
                start['headers'].append((b'content-length', str(len(body)).encode()))
                await send(start)
                await send({'type': 'http.response.body', 'body': body})
            else:
                await send(message)

        await self.app(scope, receive, safe_send)
