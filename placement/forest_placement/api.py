"""Local-only FastAPI app. No network access is used at runtime."""
import threading
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .engine import ROOT, PREP, CACHE, analyze, metadata
from .models import Candidate,PRESETS

app=FastAPI(title='Orman Gözlem · Yerleşim Simülasyonu')
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
PREP.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
app.mount('/maps',StaticFiles(directory=PREP),name='maps')
app.mount('/results',StaticFiles(directory=CACHE),name='results')
lock=threading.Lock()

@app.middleware('http')
async def local_policy(request,call_next):
    response=await call_next(request)
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'"
    response.headers['X-Content-Type-Options']='nosniff'
    return response

@app.get('/')
def index():return FileResponse(ROOT/'static/index.html')

@app.get('/api/config')
def config():
    try:
        return dict(ready=True,presets=[p.model_dump() for p in PRESETS],data=metadata())
    except FileNotFoundError as e:return dict(ready=False,error=str(e),presets=[p.model_dump() for p in PRESETS])

@app.post('/api/analyze')
def analysis(candidate:Candidate):
    try:
        with lock:return analyze(candidate)
    except FileNotFoundError as e:raise HTTPException(503,str(e))
    except ValueError as e:raise HTTPException(422,str(e))

class Comparison(BaseModel):
    candidates:list[Candidate]=Field(min_length=2,max_length=6)

@app.post('/api/compare')
def compare(request:Comparison):
    results=[analysis(c) for c in request.candidates]
    ranking=sorted(range(len(results)),key=lambda i:(results[i]['metrics']['canopy_smoke']['priority_visible_ha'],results[i]['metrics']['canopy_smoke']['visible_forest_ha']),reverse=True)
    return dict(results=results,ranking=ranking,ranking_basis='Önce görünür öncelikli orman; eşitlikte görünür toplam orman (duman hedefi, simülasyon).')
