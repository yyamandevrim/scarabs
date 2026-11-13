"""Bounded in-process budgets. One worker/container is part of the deployment contract."""
from collections import OrderedDict, deque
from ipaddress import ip_address
import json
import time

class PublicLimits:
    def __init__(self, app, per_client=12, global_limit=60, window=60, max_body=32768, proxy_hops=0):
        self.app, self.per_client, self.global_limit = app, per_client, global_limit
        self.window, self.max_body, self.proxy_hops = window, max_body, proxy_hops
        self.clients = OrderedDict()
        self.total = deque()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'] not in ('/api/analyze', '/api/compare'):
            return await self.app(scope, receive, send)
        async def reject(code, message, retry=False):
            headers=[(b'content-type', b'application/json')]
            if retry: headers.append((b'retry-after', str(self.window).encode()))
            await send({'type':'http.response.start','status':code,'headers':headers})
            await send({'type':'http.response.body','body':json.dumps({'detail':message}).encode()})
        now=time.monotonic()
        client=(scope.get('client') or ('unknown',0))[0]
        headers=dict(scope['headers'])
        # Opt-in only behind the documented number of trusted ingress proxies.
        if self.proxy_hops:
            chain=headers.get(b'x-forwarded-for',b'').decode('ascii',errors='ignore').split(',')
            if len(chain) >= self.proxy_hops:
                try: client=str(ip_address(chain[-self.proxy_hops].strip()))
                except ValueError: pass  # Fail closed to the peer's shared budget.
        for q in (self.total,):
            while q and q[0] <= now-self.window: q.popleft()
        for key in list(self.clients):
            if self.clients[key] and self.clients[key][-1] <= now-self.window: del self.clients[key]
        q=self.clients.pop(client,deque())
        while q and q[0] <= now-self.window:q.popleft()
        self.clients[client]=q
        # Never evict active clients: an exhausted tracking table fails closed.
        if len(self.clients)>4096:
            self.clients.pop(client)
            return await reject(429,'Server request budget is busy. Retry in one minute.',True)
        if len(q)>=self.per_client or len(self.total)>=self.global_limit:
            return await reject(429,'Analysis rate limit reached. Retry in one minute.',True)
        q.append(now); self.total.append(now)
        for key in list(self.clients):
            if self.clients[key] and self.clients[key][-1] <= now-self.window: del self.clients[key]
        try: length=int(headers.get(b'content-length',b'0'))
        except ValueError:return await reject(400,'Invalid Content-Length.')
        if length>self.max_body:
            return await reject(413,'Request body exceeds 32 KiB.')
        body=b''
        while True:
            message=await receive()
            if message['type']=='http.disconnect': return
            body+=message.get('body',b'')
            if len(body)>self.max_body:return await reject(413,'Request body exceeds 32 KiB.')
            if not message.get('more_body',False):break
        delivered=False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered=True
                return {'type':'http.request','body':body,'more_body':False}
            return await receive()
        await self.app(scope,replay,send)
