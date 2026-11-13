"""Fail-closed shared-secret sessions for the ranger Wi-Fi panel and all data APIs."""
from collections import OrderedDict
import hmac
import os
import secrets
from threading import RLock
import time
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

class PanelAuth:
    def __init__(self, configured=None, clock=time.time):
        self.secret = os.environ.get('ACORN_PANEL_SECRET') or configured
        self.clock = clock
        self.sessions = OrderedDict()
        self.failures = OrderedDict()
        self.lock = RLock()
        self.ttl = 8*3600

    def limited(self, key):
        now = self.clock()
        attempts = [t for t in self.failures.get(key, []) if t > now-300]
        self.failures[key] = attempts
        self.failures.move_to_end(key)
        while len(self.failures) > 1024:
            self.failures.popitem(last=False)
        return len(attempts) >= 5

    def login(self, candidate, key):
        with self.lock:
            if not self.secret:
                return 503, None
            # Global limit also bounds attacks from changing client addresses.
            if self.limited(key) or self.limited('*'):
                return 429, None
            if not isinstance(candidate, str) or len(candidate) > 1024 or not hmac.compare_digest(candidate.encode(), self.secret.encode()):
                self.failures.setdefault(key, []).append(self.clock())
                self.failures.setdefault('*', []).append(self.clock())
                return 401, None
            token = secrets.token_urlsafe(32)
            self.sessions[token] = self.clock()+self.ttl
            while len(self.sessions) > 256:
                self.sessions.popitem(last=False)
            self.failures.pop(key, None)
            return 200, token

    def valid(self, token):
        with self.lock:
            expiry = self.sessions.get(token, 0)
            if expiry <= self.clock():
                self.sessions.pop(token, None)
                return False
            return True


def same_origin(request):
    origin = request.headers.get('origin')
    if request.headers.get('sec-fetch-site') == 'cross-site':
        return False
    return not origin or origin == f'{request.url.scheme}://{request.headers.get("host", "")}'


def install_auth(app, station, static):
    auth = PanelAuth(getattr(station.config, 'panel_secret', None))
    app.state.panel_auth = auth

    @app.middleware('http')
    async def protect(request, call_next):
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and not same_origin(request):
            return JSONResponse({'detail': 'Same-origin requests required'}, status_code=403)
        public = request.url.path in ('/login', '/api/auth/login') or request.url.path.startswith('/static/')
        if not public:
            if not auth.secret:
                return JSONResponse({'detail': 'Ranger access disabled: set ACORN_PANEL_SECRET locally'}, status_code=503)
            if not auth.valid(request.cookies.get('acorn_session')):
                if request.url.path == '/':
                    return RedirectResponse('/login', status_code=303)
                return JSONResponse({'detail': 'Login required'}, status_code=401)
        return await call_next(request)

    @app.get('/login')
    def login_page():
        from fastapi.responses import FileResponse
        return FileResponse(static/'login.html', media_type='text/html')

    @app.post('/api/auth/login')
    async def login(request: Request):
        if len(request.headers.get('content-length', '')) > 10 or (request.headers.get('content-length', '0').isdigit() and int(request.headers.get('content-length', '0')) > 2048):
            return JSONResponse({'detail': 'Request too large'}, status_code=413)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 2048:
                return JSONResponse({'detail': 'Request too large'}, status_code=413)
        import json
        try:
            candidate = json.loads(body).get('secret')
        except (ValueError, AttributeError):
            candidate = None
        code, token = auth.login(candidate, request.client.host if request.client else 'unknown')
        response = JSONResponse({'ok': code == 200, 'detail': {200: 'Signed in', 401: 'Incorrect secret', 429: 'Too many attempts; wait five minutes', 503: 'Set ACORN_PANEL_SECRET on the station'}[code]}, status_code=code)
        if token:
            response.set_cookie('acorn_session', token, max_age=auth.ttl, httponly=True, samesite='strict', secure=request.url.scheme == 'https')
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.post('/api/auth/logout')
    def logout(request: Request):
        with auth.lock:
            auth.sessions.pop(request.cookies.get('acorn_session'), None)
        response = JSONResponse({'ok': True})
        response.delete_cookie('acorn_session')
        return response
