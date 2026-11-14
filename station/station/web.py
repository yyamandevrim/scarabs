"""Entirely local panel and JSON API; no cloud services or frontend dependencies."""
from contextlib import asynccontextmanager
from html import escape
from pathlib import Path
import time
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import identity
from .mcu_bridge import register_routes as register_mcu_routes

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

    app = FastAPI(title=identity.NAME, lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    static = Path(__file__).parent/"static"

    from .auth import install_auth
    install_auth(app, station, static)

    @app.middleware("http")
    async def local_only_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; media-src 'self'; object-src 'none'; frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Language"] = "en"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/")
    def panel():
        markup = (static/"index.html").read_text(encoding="utf-8")
        return HTMLResponse(markup.replace("{{station_title}}", escape(identity.NAME))
                            .replace("{{station_wordmark}}", escape(identity.NAME.partition(" — ")[0])))

    @app.get("/api/status")
    def status():
        # LoRa link state rides along without touching the runtime status builder.
        return {**station.status(), "lora": station.lora.radio_status()}

    @app.get("/api/events")
    def events(kind: Literal["smoke", "flame_sensor", "all"] = "smoke"):
        # Default stays camera "suspected smoke" only; flame-sensor triggers are a separate kind.
        return station.store.events(kind=kind)

    @app.get("/api/events/pending")
    def pending_events(limit: int = Query(200, ge=1, le=200),
                       order: Literal["newest", "oldest"] = "newest",
                       cursor: str | None = Query(None, max_length=256)):
        try:
            return station.store.pending_page(limit=limit, order=order, cursor=cursor)
        except ValueError as exc:
            raise HTTPException(422, "Invalid pending cursor") from exc

    @app.post("/api/events/{event_id}/decision")
    def decide(event_id: str, body: Decision):
        if not station.store.decide(event_id,body.decision):
            raise HTTPException(404, "Event not found")
        return {"ok":True, "decision":body.decision}

    @app.get("/api/cameras/{name}/frame.jpg")
    def frame(name: str):
        if name not in station.workers:
            raise HTTPException(404,"Camera inactive")
        data = station.jpeg(name)
        if not data:
            raise HTTPException(503,"Connection lost")
        return Response(data,media_type="image/jpeg")

    @app.get("/events/{filename}")
    def media(filename: str):
        # Event-generated filenames only; do not expose arbitrary data files.
        import re
        if not re.fullmatch(r"[0-9a-f]{32}\.(jpg|webm|avi)", filename):
            raise HTTPException(404)
        path = station.store.media/filename
        if not path.is_file():
            raise HTTPException(404)
        # WebM plays inline (FileResponse answers Range requests); legacy AVI downloads.
        media_type = {".jpg":"image/jpeg", ".webm":"video/webm", ".avi":"video/x-msvideo"}[path.suffix]
        return FileResponse(path, media_type=media_type, filename=filename if path.suffix == ".avi" else None)

    @app.get("/api/communication")
    def communication():
        link = station.lora
        sender = link.sender
        return {"station_id": station.config.lora.station_id, "role": "Ranger Wi-Fi full-detail panel",
                "radio": link.radio_status(),
                "link": {"enabled": link.link is not None, "transport": link.link.label if link.link is not None else "disabled",
                         "sent": sender.sent if sender else 0, "duty_refusals": sender.refused if sender else 0,
                         "queued": len(sender.queue) if sender else 0, "queue_drops": sender.dropped if sender else 0,
                         "error": link.error,
                         "calculated_next_tx_at": sender.next_tx_at(time.time()) if sender else None,
                         "calculated_min_spacing_seconds": sender.slot_seconds if sender else None,
                         "requested_heartbeat_seconds": station.config.lora.heartbeat_seconds}}

    @app.get("/api/events/{event_id}")
    def event(event_id: str):
        item = station.store.event(event_id)
        if item is None:
            raise HTTPException(404, "Event not found")
        return item

    register_mcu_routes(app, station)
    app.mount("/static", StaticFiles(directory=static), name="static")
    return app
