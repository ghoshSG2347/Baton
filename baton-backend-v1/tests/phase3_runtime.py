"""Opt-in local integration server: REAL GitHub, MOCKED Gemini transport. No real Gemini key."""
import json
import httpx
from pydantic import SecretStr
from app.core.config import get_settings

settings = get_settings()
settings.gemini_api_key = SecretStr('synthetic-wire-only-provider-key')
settings.gemini_model = 'fixture-model'
settings.baton_access_key = 'synthetic-wire-operator-key'
settings.frontend_origins = 'http://127.0.0.1:5184'
Original = httpx.AsyncClient

class Wire(httpx.AsyncBaseTransport):
    def __init__(self): self.network = httpx.AsyncHTTPTransport()
    async def handle_async_request(self, request):
        if request.url.host != 'generativelanguage.googleapis.com':
            return await self.network.handle_async_request(request)
        payload = json.loads(request.content)
        packet = json.loads(payload['contents'][0]['parts'][0]['text'])
        assert 'UNTRUSTED DATA' in payload['systemInstruction']['parts'][0]['text']
        assert 'synthetic-wire-only-provider-key' not in request.content.decode()
        records = [r for r in packet['records'] if r['source_paths'] and r.get('section_number') not in (16,18,19,20)]
        selection = {'status':'grounded' if records else 'unknown', 'evidence_ids':[records[0]['id']] if records else [], 'actions':[], 'reasoning':[]}
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(selection)}]}}], 'usageMetadata':{'promptTokenCount':101,'candidatesTokenCount':9,'totalTokenCount':115,'thoughtsTokenCount':5}})
    async def aclose(self): await self.network.aclose()

httpx.AsyncClient = lambda **kwargs: Original(transport=Wire(), **kwargs)
from app.main import app
