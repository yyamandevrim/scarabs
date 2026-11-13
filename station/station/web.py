"""Entirely local panel and JSON API; no cloud services or frontend dependencies."""
from contextlib import asynccontextmanager
from pathlib import Path
import time
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

class Decision(BaseModel):
    decision: Literal["confirmed", "rejected"]


def create_app(station, manage_lifecycle=True):
    @asynccontextmanager
    async def lifespan(app):
        if manage_lifecycle:
            station.start()
        try:
            yield
        finally:
            if manage_lifecycle:
                station.stop()
                station.store.shutdown()

    app = FastAPI(title="Orman Gözlem İstasyonu", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    static = Path(__file__).parent/"static"

    @app.middleware("http")
    async def local_only_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; media-src 'self'; object-src 'none'; frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/")
    def panel():
        return FileResponse(static/"index.html")

    @app.get("/api/status")
    def status():
        return station.status()

    @app.get("/api/events")
    def events():
        return station.store.events()

    @app.post("/api/events/{event_id}/decision")
    def decide(event_id: str, body: Decision):
        if not station.store.decide(event_id,body.decision,time.time()):
            raise HTTPException(404, "Olay bulunamadı")
        return {"ok":True, "decision":body.decision}

    @app.get("/api/cameras/{name}/frame.jpg")
    def frame(name: str):
        if name not in station.workers:
            raise HTTPException(404,"Kamera etkin değil")
        data = station.jpeg(name)
        if not data:
            raise HTTPException(503,"Bağlantı koptu")
        return Response(data,media_type="image/jpeg")

    @app.get("/events/{filename}")
    def media(filename: str):
        # Event-generated filenames only; do not expose arbitrary data files.
        import re
        if not re.fullmatch(r"[0-9a-f]{32}\.(jpg|avi)", filename):
            raise HTTPException(404)
        path = station.store.media/filename
        if not path.is_file():
            raise HTTPException(404)
        return FileResponse(path, filename=filename if path.suffix == ".avi" else None)

    app.mount("/static", StaticFiles(directory=static), name="static")
    return app
