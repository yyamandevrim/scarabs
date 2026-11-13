"""SQLite event journal and event-only media with retention."""
import json
from pathlib import Path
import sqlite3
from threading import RLock
import uuid

class EventStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.media = self.root / "events"
        self.media.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()
        self.db = sqlite3.connect(self.root / "events.sqlite3", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY, camera TEXT NOT NULL, opened_at REAL NOT NULL,
            last_seen REAL NOT NULL, closed_at REAL, box TEXT NOT NULL,
            confidence REAL NOT NULL, snapshot TEXT, clip TEXT,
            decision TEXT NOT NULL DEFAULT 'pending' CHECK(decision IN ('pending','confirmed','rejected')),
            decided_at REAL, media_error TEXT)""")
        self.db.commit()

    def create(self, camera, detection, now):
        event_id = uuid.uuid4().hex
        with self.lock, self.db:
            self.db.execute("INSERT INTO events(id,camera,opened_at,last_seen,box,confidence) VALUES(?,?,?,?,?,?)", (event_id,camera,now,now,json.dumps(detection.box),detection.confidence))
        return event_id

    def extend(self, event_id, detection, now):
        with self.lock, self.db:
            self.db.execute("UPDATE events SET last_seen=?,box=?,confidence=? WHERE id=?", (now,json.dumps(detection.box),detection.confidence,event_id))

    def close_event(self, event_id, now):
        with self.lock, self.db:
            self.db.execute("UPDATE events SET closed_at=? WHERE id=?", (now,event_id))

    def close_previous(self, now):
        with self.lock, self.db:
            self.db.execute("UPDATE events SET closed_at=? WHERE closed_at IS NULL", (now,))

    def set_media(self, event_id, *, snapshot=None, clip=None, error=None):
        with self.lock, self.db:
            cursor = self.db.execute("UPDATE events SET snapshot=COALESCE(?,snapshot),clip=COALESCE(?,clip),media_error=? WHERE id=?", (snapshot,clip,error,event_id))
            return cursor.rowcount > 0

    def decide(self, event_id, decision, now):
        if decision not in ("confirmed", "rejected"):
            raise ValueError("Decision must be confirmed or rejected")
        with self.lock, self.db:
            cursor = self.db.execute("UPDATE events SET decision=?,decided_at=? WHERE id=?", (decision,now,event_id))
            return cursor.rowcount > 0

    def events(self, limit=200):
        with self.lock:
            rows = self.db.execute("SELECT * FROM events ORDER BY opened_at DESC LIMIT ?", (limit,)).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["box"] = json.loads(item["box"])
            item["title"] = "Duman şüphesi"
            result.append(item)
        return result

    def prune(self, now, retention_days):
        with self.lock, self.db:
            rows = self.db.execute("SELECT id FROM events WHERE last_seen < ?", (now-retention_days*86400,)).fetchall()
            for row in rows:
                for suffix in (".jpg", ".webm", ".tmp.webm", ".avi", ".tmp.avi"):
                    (self.media / (row["id"]+suffix)).unlink(missing_ok=True)
                self.db.execute("DELETE FROM events WHERE id=?", (row["id"],))
            # Remove orphaned media left by a process crash, after the same retention period.
            cutoff = now-retention_days*86400
            for path in self.media.iterdir():
                if path.is_file() and path.stat().st_mtime < cutoff:
                    exists = self.db.execute("SELECT 1 FROM events WHERE id=?", (path.name.split('.')[0],)).fetchone()
                    if not exists:
                        path.unlink()
            return len(rows)

    def shutdown(self):
        with self.lock:
            self.db.close()
