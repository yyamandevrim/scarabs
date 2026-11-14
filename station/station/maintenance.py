"""Offline maintenance commands: clean the event list before a demo, and a
hardware-free camera dropout for recorded file sources."""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sqlite3
from . import datalock

EVENT_FILES = ("events.sqlite3", "events.sqlite3-wal", "events.sqlite3-shm")
UNPLUGGED_SUFFIX = ".unplugged"


def event_summary(data_dir):
    data_dir = Path(data_dir)
    db = data_dir / "events.sqlite3"
    rows = 0
    if db.exists():
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            rows = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        except sqlite3.Error:
            rows = None
        finally:
            con.close()
    media = data_dir / "events"
    files = sum(1 for p in media.iterdir() if p.is_file()) if media.is_dir() else 0
    return {"events": rows, "media_files": files}


def archive_events(data_dir, delete=False, now=None):
    """Move (or, with delete=True, remove) the event database and evidence.

    Refuses while a station server holds the data directory. The archive is a
    self-contained copy: data/archive/<UTC time>/events.sqlite3 plus events/.
    """
    data_dir = Path(data_dir)
    handle = datalock.acquire(data_dir)
    try:
        items = [data_dir / name for name in EVENT_FILES] + [data_dir / "events"]
        present = [p for p in items if p.exists()]
        summary = event_summary(data_dir)
        if not present:
            return {**summary, "action": "nothing", "archive": None}
        if delete:
            for path in present:
                shutil.rmtree(path) if path.is_dir() else path.unlink()
            return {**summary, "action": "deleted", "archive": None}
        stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
        target = data_dir / "archive" / stamp
        suffix = 1
        while target.exists():
            target = data_dir / "archive" / f"{stamp}-{suffix}"
            suffix += 1
        target.mkdir(parents=True)
        for path in present:
            shutil.move(str(path), str(target / path.name))
        return {**summary, "action": "archived", "archive": str(target)}
    finally:
        datalock.release(handle)


def _file_slot(config, name):
    camera = next((c for c in config.cameras if c.name == name), None)
    if camera is None:
        raise ValueError(f"Unknown camera slot {name!r}; use left, centre or right")
    if camera.kind != "file":
        raise ValueError(f"{name} is a USB camera: unplug its cable instead")
    if not camera.active:
        raise ValueError(f"{name} is not active; only an active slot can drop out")
    return Path(camera.source)


def unplug(config, name):
    source = _file_slot(config, name)
    parked = source.with_name(source.name + UNPLUGGED_SUFFIX)
    if parked.exists() and not source.exists():
        return f"{name} is already unplugged"
    if not source.exists():
        raise ValueError(f"{name}: source file is missing")
    source.rename(parked)
    return f"{name} unplugged: its recorded source is hidden; the running panel shows “bağlantı koptu” within about a second"


def replug(config, name):
    source = _file_slot(config, name)
    parked = source.with_name(source.name + UNPLUGGED_SUFFIX)
    if source.exists():
        return f"{name} is already connected"
    if not parked.exists():
        raise ValueError(f"{name}: nothing to restore ({parked.name} not found)")
    parked.rename(source)
    return f"{name} replugged: the station retries and recovers within retry_seconds"
