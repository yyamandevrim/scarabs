#!/usr/bin/env python3
"""Run generated python/main.py with real footage/inference and explicit simulated MCU.

Run with the station Python environment on macOS, or inside App Lab's arm64 image.
Only loopback HTTP is used; this script never contacts a board.
"""
import argparse
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


def verify(app, media, data, python, port):
    secret = secrets.token_urlsafe(32)
    env = {**os.environ, "ACORN_PANEL_SECRET": secret, "PYTHONUNBUFFERED": "1"}
    command = [python, str(app / "python/main.py"), "--recorded", str(media), "--data-dir", str(data),
               "--host", "127.0.0.1", "--port", str(port)]
    url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryFile(mode="w+") as log:
        proc = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
        jar = http.cookiejar.CookieJar()
        client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        result = None

        def request(path, body=None):
            payload = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(url + path, data=payload,
                                         headers={"Content-Type": "application/json"} if payload else {})
            with client.open(req, timeout=5) as response:
                return response.read()

        try:
            deadline = time.monotonic() + 60
            while True:
                if proc.poll() is not None:
                    raise RuntimeError(f"Station exited {proc.returncode}")
                try:
                    request("/api/auth/login", {"secret": secret})
                    break
                except (urllib.error.URLError, ConnectionError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Panel did not become ready")
                    time.sleep(.2)
            try:
                urllib.request.urlopen(url + "/api/status", timeout=5)
                raise AssertionError("Unauthenticated status was exposed")
            except urllib.error.HTTPError as exc:
                assert exc.code == 401
            assert b"ACORN" in request("/")
            while True:
                status = json.loads(request("/api/status"))
                active = [c for c in status["cameras"] if c["active"]]
                events = json.loads(request("/api/events"))
                if len(active) == 2 and all(c["connected"] and c["analyses"] >= 6 and not c["pipeline_error"] for c in active) and events:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"Recorded station did not produce healthy real inference/events: {status}")
                time.sleep(.25)
            assert status["runtime"]["state"] == "running" and not status["runtime"]["error"]
            assert status["mcu"]["simulated"] and status["mcu"]["flame_sensor"]["connected"]
            assert not status["mcu"]["flame_sensor"]["triggered"]
            assert json.loads(request("/api/events?kind=flame_sensor")) == []
            for camera in active:
                assert request(f'/api/cameras/{camera["name"]}/frame.jpg').startswith(b"\xff\xd8")
            # Wait for real pre/post evidence encoding, not just the database event.
            while not any(e["snapshot"] and e["clip"] for e in events):
                if time.monotonic() >= deadline:
                    raise RuntimeError("No encoded evidence from real inference")
                time.sleep(.25)
                events = json.loads(request("/api/events"))
            evidence = next(e for e in events if e["snapshot"] and e["clip"])
            assert request("/events/" + evidence["snapshot"]).startswith(b"\xff\xd8")
            assert len(request("/events/" + evidence["clip"])) > 100
            result = {"python": sys.version.split()[0], "profile": status["analysis_profile"],
                    "runtime": status["runtime"], "cameras": [{k: c[k] for k in
                        ("name", "kind", "capture_width", "capture_height", "analyses", "analysis_ms", "pipeline_error")} for c in active],
                    "mcu": "explicitly simulated, no flame trigger injected", "smoke_events": len(events),
                    "event_ids": [e["id"] for e in events],
                    "evidence": "JPEG and encoded clip served with authentication", "unauthenticated_status": 401,
                    "note": "Local machine/container verification; not a UNO Q performance measurement"}
            return result
        except BaseException:
            log.seek(0)
            print(log.read()[-12000:], file=sys.stderr)
            raise
        finally:
            stopping = time.monotonic()
            proc.terminate()
            try:
                # Match the researched App CLI Compose stop timeout.
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise RuntimeError("Station did not stop cleanly")
            if proc.returncode not in (0, -15):
                raise RuntimeError(f"Station shutdown exit code {proc.returncode}")
            if result is not None:
                result["shutdown_seconds"] = round(time.monotonic() - stopping, 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--media", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="acorn-applab-verify-") as directory:
        result = verify(args.app.resolve(), args.media.resolve(), Path(directory), args.python, port)
        restarted = verify(args.app.resolve(), args.media.resolve(), Path(directory), args.python, port)
        assert set(result.pop("event_ids")) <= set(restarted["event_ids"])
        result["restart"] = "Clean restart with the same data directory retained prior smoke events"
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
