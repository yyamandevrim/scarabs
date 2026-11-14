"""Identical offline/public ASGI app. Public compute has bounded inputs and budgets."""
import json
import math
import hashlib
import os
import re
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from html import escape
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from .engine import ROOT, PREP, CACHE, analyze, metadata
from .models import Candidate, PRESETS
from .security import PublicLimits

@asynccontextmanager
async def lifespan(app):
    if os.environ.get('PLACEMENT_PRODUCTION')=='1':
        from .warmup import warmup
        warmup(load_data=True)
    yield

app=FastAPI(title='Forest observation placement simulation',docs_url=None,redoc_url=None,lifespan=lifespan)

@app.exception_handler(RequestValidationError)
async def validation_error(request,exc):
    # The JSON decoder accepts NaN/Infinity, but validation errors must still be
    # serializable as strict JSON after the finite-input model rejects them.
    detail=jsonable_encoder(exc.errors(),custom_encoder={float:lambda value:value if math.isfinite(value) else str(value)})
    return JSONResponse(status_code=422,content={'detail':detail})

app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
CACHE.mkdir(parents=True,exist_ok=True)
lock=threading.BoundedSemaphore(1)
def rate_limits_enabled(env=os.environ):
    """Public deployment only: the laptop/offline demo is never throttled.

    PLACEMENT_RATE_LIMIT=1/0 overrides; otherwise PLACEMENT_PRODUCTION=1 (Modal) enables it."""
    flag=env.get('PLACEMENT_RATE_LIMIT')
    if flag is not None:return flag.strip().lower() in ('1','true','yes','on')
    return env.get('PLACEMENT_PRODUCTION')=='1'

if rate_limits_enabled():
    app.add_middleware(PublicLimits,proxy_hops=int(os.environ.get('PLACEMENT_PROXY_HOPS','0')))

@app.middleware('http')
async def policy(request,call_next):
    response=await call_next(request)
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'"
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    if request.url.path in ('/','/map','/api/brand') or request.url.path.startswith('/static/'):
        response.headers['Cache-Control']='no-cache'
    return response

def branded_page(filename):
    # Render identity before JavaScript starts; brand.json remains the only source.
    identity=json.loads((ROOT/'brand.json').read_text())
    page=(ROOT/'static'/filename).read_text()
    assets=sorted(p for p in (ROOT/'static').iterdir() if p.suffix in ('.js','.css','.json','.svg'))
    revision=hashlib.sha256(b''.join(p.read_bytes() for p in assets)).hexdigest()[:12]
    page=page.replace('<body','<body data-asset-version="'+revision+'"',1)
    page=re.sub(r'(/static/[^"?]+\.(?:js|css|png))"',lambda match:match.group(1)+'?v='+revision+'"',page)
    page=page.replace('data-brand-logo', 'data-brand-logo src="'+escape(identity['logo'],quote=True)+'"')
    page=page.replace('data-brand-stacked', 'data-brand-stacked src="'+escape(identity.get('stacked_logo',identity['logo']),quote=True)+'"')
    page=re.sub(r'<title>([^<]*)</title>',lambda match:'<title>'+escape(identity['name'])+' · '+match.group(1)+'</title>',page,count=1)
    for field,key in [('name','name'),('team','team'),('expansion','expansion'),('event','event'),('challenge','challenge')]:
        page=page.replace('<span data-brand-'+field+'></span>', '<span data-brand-'+field+'>'+escape(identity.get(key,''))+'</span>')
    page=page.replace('<span data-brand-tagline></span>','<span data-brand-tagline>'+escape(identity['tagline']['en'])+'</span>')
    return HTMLResponse(page)

@app.get('/')
def index():return branded_page('landing.html')

@app.get('/map')
def map_page():return branded_page('index.html')

@app.get('/api/brand')
def brand():return json.loads((ROOT/'brand.json').read_text())

@app.get('/api/config')
def config():
    try:return dict(ready=True,presets=[p.model_dump() for p in PRESETS],data=metadata())
    except FileNotFoundError:return dict(ready=False,error='Prepared regional data is not installed. See placement/README.md.',presets=[p.model_dump() for p in PRESETS])

@app.get('/maps/{filename}')
def maps(filename:str):
    if filename not in ('background.png','forest.png','water.png','map.json'):raise HTTPException(404)
    path=PREP/filename
    if not path.is_file():raise HTTPException(404)
    return FileResponse(path)

@app.get('/results/{filename}')
def results(filename:str):
    if not re.fullmatch(r'[0-9a-f]{24}_(bare_ground|bare_smoke|canopy_ground|canopy_smoke)\.png',filename):raise HTTPException(404)
    path=CACHE/filename
    if not path.is_file():raise HTTPException(404,'Result expired; run the analysis again.')
    return FileResponse(path)

def run_analysis(candidate):
    try:return analyze(candidate)
    except FileNotFoundError:raise HTTPException(503,'Regional data unavailable; contact the project team.')
    except ValueError as e:raise HTTPException(422,str(e))

def acquire():
    if not lock.acquire(blocking=False):raise HTTPException(503,'An analysis is running. Retry shortly.',headers={'Retry-After':'2'})

@app.post('/api/analyze')
def analysis(candidate:Candidate):
    acquire()
    try:return run_analysis(candidate)
    finally:lock.release()

class Comparison(BaseModel):
    model_config=ConfigDict(extra='forbid')
    candidates:list[Candidate]=Field(min_length=2,max_length=6)

@app.post('/api/compare')
def compare(request:Comparison):
    from shapely.geometry import Polygon
    first=request.candidates[0]
    target=Polygon(first.priority) if first.priority is not None else None
    for candidate in request.candidates[1:]:
        if candidate.reference!=first.reference:
            raise HTTPException(422,'Comparison requires the same camera mode (connected cameras or reference).')
        if ((candidate.priority is None)!=(target is None) or
            (target is not None and not target.equals(Polygon(candidate.priority)))):
            raise HTTPException(422,'Comparison requires the same priority area for every candidate, or none for all.')
    acquire()
    try:
        results=[run_analysis(c) for c in request.candidates]
        ranking=sorted(range(len(results)),key=lambda i:(results[i]['metrics']['canopy_smoke']['priority_visible_ha'],results[i]['metrics']['canopy_smoke']['visible_forest_ha']),reverse=True)
        return dict(results=results,ranking=ranking,ranking_basis='Visible priority forest first, then total visible forest (smoke-target simulation).')
    finally:lock.release()
