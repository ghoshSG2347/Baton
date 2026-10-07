"""Last boundary: configured secrets cannot leave any JSON API response."""
import json
from app.core.secrets import secret_values
from app.generators.context_builder import scrub
from app.core.security import REQUEST_AI, AICredential


class SafeJSONResponses:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        start, chunks, size = None, [], 0
        completed = False
        headers = dict(scope.get('headers', []))
        secrets = secret_values(*(headers.get(name, b'').decode('utf-8', 'ignore')
                                  for name in (b'x-github-token', b'x-baton-key', b'x-gemini-key')))
        handle = REQUEST_AI.set(AICredential(headers.get(b'x-gemini-key', b'').decode('ascii', 'ignore').strip(),
                                            headers.get(b'x-gemini-model', b'').decode('ascii', 'ignore').strip()))

        async def safe_send(message):
            nonlocal start, size, completed
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
                completed = True
            else:
                await send(message)

        try:
            await self.app(scope, receive, safe_send)
        except Exception as exc:
            # Keep unexpected application failures safe and visible to CORS clients.
            # Never log exception text: it may contain upstream credentials/content.
            import logging
            from app.core.config import get_settings
            logging.getLogger('uvicorn.error').error('Baton application failure type=%s', type(exc).__name__)
            if not completed:
                body = b'{"detail":"Baton encountered a server error. Try again later.","code":"baton_backend_failure"}'
                response_headers = [(b'content-type', b'application/json'), (b'content-length', str(len(body)).encode())]
                origin = headers.get(b'origin', b'').decode('ascii', 'ignore')
                if origin in get_settings().cors_origins:
                    response_headers.extend([(b'access-control-allow-origin', origin.encode()), (b'vary', b'Origin'), (b'access-control-expose-headers', b'X-Baton-Usage')])
                await send({'type': 'http.response.start', 'status': 500, 'headers': response_headers})
                await send({'type': 'http.response.body', 'body': body})
        finally:
            REQUEST_AI.reset(handle)
