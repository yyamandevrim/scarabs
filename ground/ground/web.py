from contextlib import asynccontextmanager
from pathlib import Path
from html import escape
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from station.auth import same_origin
import httpx

class DemoMode(BaseModel):
    enabled: bool


def create_app(receiver, wifi, listener=None):
    @asynccontextmanager
    async def lifespan(app):
        if listener:
            listener.start()
        try:
            yield
        finally:
            if listener:
                listener.stop()
            wifi.client.close()
            receiver.close()

    app = FastAPI(title='ACORN — Ground', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    static = Path(__file__).parent/'static'

    @app.middleware('http')
    async def headers(request, call_next):
        if request.method not in ('GET', 'HEAD') and not same_origin(request):
            return Response(status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self'; media-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'"
        return response

    def known(station, event):
        if (station, event) not in receiver.alerts:
            raise HTTPException(404, 'No LoRa alert with this station and event identifier')

    def require_demo():
        if not wifi.enabled:
            raise HTTPException(403, 'Demo mode is off; imagery is unavailable over LoRa')

    def wifi_call(fn):
        try:
            return fn()
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            # URLs and credentials never go to browser errors.
            raise HTTPException(502, 'Wi-Fi unavailable, authentication failed or evidence not ready; check station settings') from exc

    @app.get('/')
    def index():
        return HTMLResponse((static/'index.html').read_text().replace('{{transport_label}}', escape(receiver.transport_label)))

    @app.get('/api/state')
    def state():
        return receiver.snapshot()

    @app.post('/api/alerts/{station}/{event}/ack')
    def acknowledge(station: int, event: str):
        if not receiver.acknowledge(station, event):
            raise HTTPException(404)
        return {'ok': True, 'scope': 'local only; no radio uplink'}

    @app.get('/api/demo')
    def demo():
        return {'enabled': wifi.enabled}

    @app.post('/api/demo')
    def set_demo(body: DemoMode):
        wifi.enabled = body.enabled
        return {'enabled': wifi.enabled}

    @app.get('/api/demo/status')
    def demo_status():
        require_demo()
        return wifi_call(wifi.status)

    @app.get('/api/demo/cameras/{camera}.jpg')
    def camera(camera: str):
        require_demo()
        return Response(wifi_call(lambda: wifi.frame(camera)), media_type='image/jpeg')

    @app.post('/api/evidence/{station}/{event}/collect')
    def collect(station: int, event: str):
        known(station, event)
        return wifi_call(lambda: wifi.collect(station, event))

    @app.get('/api/evidence/{station}/{event}')
    def saved(station: int, event: str):
        known(station, event)
        return wifi.saved(station, event) or {'files': []}

    @app.get('/api/evidence/{station}/{event}/{filename}')
    def evidence(station: int, event: str, filename: str):
        require_demo()
        known(station, event)
        manifest = wifi.saved(station, event)
        if not manifest or filename not in manifest['files']:
            raise HTTPException(404)
        return FileResponse(wifi.root/str(station)/event/filename)

    app.mount('/static', StaticFiles(directory=static), name='static')
    return app
