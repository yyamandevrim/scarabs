"""Identical offline/public ASGI app. Public compute has bounded inputs and budgets."""
import json
import hashlib
import os
import re
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
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
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
CACHE.mkdir(parents=True,exist_ok=True)
lock=threading.BoundedSemaphore(1)
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
    page=page.replace('data-brand-icon href="data:,"','data-brand-icon href="'+escape(identity['logo'],quote=True)+'"')
    page=page.replace('data-brand-logo', 'data-brand-logo src="'+escape(identity['logo'],quote=True)+'"')
    for field,key in [('name','name'),('team','team')]:
        page=page.replace('<span data-brand-'+field+'></span>', '<span data-brand-'+field+'>'+escape(identity[key])+'</span>')
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
    acquire()
    try:
        results=[run_analysis(c) for c in request.candidates]
        ranking=sorted(range(len(results)),key=lambda i:(results[i]['metrics']['canopy_smoke']['priority_visible_ha'],results[i]['metrics']['canopy_smoke']['visible_forest_ha']),reverse=True)
        return dict(results=results,ranking=ranking,ranking_basis='Visible priority forest first, then total visible forest (smoke-target simulation).')
    finally:lock.release()
