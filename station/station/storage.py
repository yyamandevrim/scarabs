"""SQLite event journal and event-only media with retention."""
import json
from pathlib import Path
import sqlite3
from threading import RLock
import uuid

KINDS = ("smoke", "flame_sensor")
TITLES = {"smoke": "Duman şüphesi", "flame_sensor": "Alev sensörü tetiklendi"}
# Columns added after the first release. Existing databases gain them on open;
# old rows keep NULL where the value was never recorded (it is not invented).
MIGRATIONS = (
    ("kind", "TEXT NOT NULL DEFAULT 'smoke'"),
    ("details", "TEXT"),
    ("alarm_confidence", "REAL"),
    ("peak_confidence", "REAL"),
)

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
        self._migrate()
        self.db.commit()

    def _migrate(self):
        with self.lock, self.db:
            existing = {row["name"] for row in self.db.execute("PRAGMA table_info(events)")}
            for name, ddl in MIGRATIONS:
                if name not in existing:
                    self.db.execute(f"ALTER TABLE events ADD COLUMN {name} {ddl}")

    def create(self, camera, detection, now):
        event_id = uuid.uuid4().hex
        with self.lock, self.db:
            self.db.execute("INSERT INTO events(id,camera,opened_at,last_seen,box,confidence,alarm_confidence,peak_confidence) VALUES(?,?,?,?,?,?,?,?)", (event_id,camera,now,now,json.dumps(detection.box),detection.confidence,detection.confidence,detection.confidence))
        return event_id

    def create_flame(self, now, details):
        # Local flame-sensor trigger: no camera, box or model confidence.
        event_id = uuid.uuid4().hex
        with self.lock, self.db:
            self.db.execute("INSERT INTO events(id,kind,camera,opened_at,last_seen,box,confidence,details) VALUES(?,'flame_sensor','',?,?,'null',0,?)", (event_id,now,now,json.dumps(details)))
        return event_id

    def update_flame(self, event_id, now, details):
        with self.lock, self.db:
            self.db.execute("UPDATE events SET last_seen=?,details=? WHERE id=? AND kind='flame_sensor'", (now,json.dumps(details),event_id))

    def pending_count(self, kind="smoke"):
        with self.lock:
            return self.db.execute("SELECT COUNT(*) FROM events WHERE kind=? AND decision='pending'", (kind,)).fetchone()[0]

    def extend(self, event_id, detection, now):
        with self.lock, self.db:
            self.db.execute("UPDATE events SET last_seen=?,box=?,confidence=?,peak_confidence=MAX(COALESCE(peak_confidence,?),?) WHERE id=?", (now,json.dumps(detection.box),detection.confidence,detection.confidence,detection.confidence,event_id))

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

    def events(self, limit=200, kind="smoke"):
        """Newest events of one kind ("smoke", "flame_sensor") or "all"."""
        if kind != "all" and kind not in KINDS:
            raise ValueError(f"kind must be one of {', '.join(KINDS)} or all")
        with self.lock:
            if kind == "all":
                rows = self.db.execute("SELECT * FROM events ORDER BY opened_at DESC LIMIT ?", (limit,)).fetchall()
            else:
                rows = self.db.execute("SELECT * FROM events WHERE kind=? ORDER BY opened_at DESC LIMIT ?", (kind,limit)).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["box"] = json.loads(item["box"])
            item["details"] = json.loads(item["details"]) if item["details"] else None
            item["title"] = TITLES[item["kind"]]
            if item["kind"] == "smoke":
                # confidence is kept for compatibility and equals latest_confidence.
                item["latest_confidence"] = item["confidence"]
            else:
                item.update(camera=None, confidence=None, alarm_confidence=None, peak_confidence=None, latest_confidence=None)
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
